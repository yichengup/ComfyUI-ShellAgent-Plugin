import os
import subprocess
import json
import logging
from functools import partial
import re
import glob
from folder_paths import models_dir as MODELS_DIR
from folder_paths import base_path as BASE_PATH

from .utils import compute_sha256, windows_to_linux_path
from .file_upload import collect_local_file, process_local_file_path_async


model_list_json = json.load(open(os.path.join(os.path.dirname(__file__), "model_info.json")))
model_loaders_info = json.load(open(os.path.join(os.path.dirname(__file__), "model_loader_info.json")))
node_deps_info = json.load(open(os.path.join(os.path.dirname(__file__), "node_deps_info.json")))


model_suffix = [".ckpt", ".safetensors", ".bin", ".pth", ".pt", ".onnx"]

def handle_model_info(ckpt_path):
    ckpt_path = windows_to_linux_path(ckpt_path)
    filename = os.path.basename(ckpt_path)
    dirname = os.path.dirname(ckpt_path)
    save_path = os.path.dirname(os.path.relpath(ckpt_path, MODELS_DIR))
    metadata_path = ckpt_path + ".json"
    if os.path.isfile(metadata_path):
        metadata = json.load(open(metadata_path))
        model_id = metadata["id"]
    else:
        logging.info(f"computing sha256 of {ckpt_path}")
        if not os.path.isfile(ckpt_path):
            raise NotImplementedError(f"please install {ckpt_path} first!")
        model_id = compute_sha256(ckpt_path)
        data = {
            "id": model_id,
            "save_path": save_path,
            "filename": filename,
        }
        json.dump(data, open(metadata_path, "w"))
    if model_id in model_list_json:
        urls = [item["url"] for item in model_list_json[model_id]["links"]][:10] # use the top 10
    else:
        urls = []
        
    item = {
        "filename": filename,
        "save_path": windows_to_linux_path(save_path),
        "urls": urls,
    }
    return model_id, item


def inspect_repo_version(module_path):
    # Create and return the JSON result
    result = {
        "name": os.path.basename(module_path),
        "repo": "",
        "commit": ""
    }
    # Get the remote repository URL
    try:
        remote_url = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=module_path
        ).strip().decode()
    except Exception:
        return result

    # Get the latest commit hash
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=module_path
        ).strip().decode()
    except Exception:
        return result

    # Create and return the JSON result
    result = {
        "name": os.path.basename(module_path),
        "repo": remote_url,
        "commit": commit_hash
    }
    return result

def fetch_model_searcher_results(model_ids):
    import requests
    url = "https://shellagent.myshell.ai/models_searcher/search_urls"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "sha256": model_ids
    }

    response = requests.post(url, headers=headers, json=data)
    results = [item[:10] for item in response.json()]
    return results

def resolve_dependencies(prompt, custom_dependencies): # resolve custom nodes and models at the same time
    from nodes import NODE_CLASS_MAPPINGS
    custom_nodes = []
    ckpt_paths = []
    
    file_mapping_dict = {}
    for node_id, node_info in prompt.items():
        node_class_type = node_info.get("class_type")
        if node_class_type is None:
            raise NotImplementedError(f"Missing nodes founded, please first install the missing nodes using ComfyUI Manager")
        node_cls = NODE_CLASS_MAPPINGS[node_class_type]
        if hasattr(node_cls, "RELATIVE_PYTHON_MODULE"):
            custom_nodes.append(node_cls.RELATIVE_PYTHON_MODULE)
        if node_class_type in model_loaders_info:
            for field_name, filename in node_info["inputs"].items():
                for item in model_loaders_info[node_class_type]:
                    pattern = item["field_name"]
                    if re.match(f"^{pattern}$", field_name):
                        ckpt_path = os.path.join(MODELS_DIR, item["save_path"], filename)
                        ckpt_paths.append(ckpt_path)
        else:
            for field_name, filename in node_info["inputs"].items():
                if type(filename) != str:
                    continue
                is_model = False
                for possible_suffix in model_suffix:
                    if filename.endswith(possible_suffix):
                        is_model = True
                if is_model:
                    print(f"find {filename}, is_model=True")
                    # find possible paths
                    matching_files = []
                    # Walk through all subdirectories and files in the directory
                    for possible_filename in glob.glob(os.path.join(MODELS_DIR, "**", "*"), recursive=True):
                        if os.path.isfile(possible_filename) and possible_filename.endswith(filename):
                            matching_files.append(possible_filename)
                    print(f"matched files: {matching_files}")
                    if len(matching_files) == 1:
                        ckpt_paths.append(matching_files[0])
        list(map(partial(collect_local_file, mapping_dict=file_mapping_dict), node_info["inputs"].values()))
            
    ckpt_paths = list(set(ckpt_paths))
    print("ckpt_paths:", ckpt_paths)
    custom_nodes = list(set(custom_nodes))
    # step 0: comfyui version
    comfyui_version = inspect_repo_version(BASE_PATH)
    
    # step 1: custom nodes
    custom_nodes_list = []
    custom_nodes_names = []
    for custom_node in custom_nodes:
        try:
            repo_info = inspect_repo_version(os.path.join(BASE_PATH, custom_node.replace(".", "/")))
            custom_nodes_list.append(repo_info)
            if repo_info["repo"] == "":
                repo_info["require_recheck"] = True
                if repo_info["name"] in custom_dependencies["custom_nodes"]:
                    repo_info["repo"] = custom_dependencies["custom_nodes"][repo_info["name"]].get("repo", "")
                    repo_info["commit"] = custom_dependencies["custom_nodes"][repo_info["name"]].get("commit", "")
            custom_nodes_names.append(repo_info["name"])
        except:
            print(f"failed to resolve repo info of {custom_node}")
    
    for repo_name in custom_nodes_names:
        if repo_name in node_deps_info:
            for deps_node in node_deps_info[repo_name]:
                if deps_node["name"] not in custom_nodes_names:
                    repo_info = inspect_repo_version(os.path.join("custom_nodes", deps_node["name"]))
                    deps_node["commit"] = repo_info["commit"]
                    custom_nodes_list.append(deps_node)
    
    # step 2: models
    models_dict = {}
    missing_model_ids = []
    for ckpt_path in ckpt_paths:
        model_id, item = handle_model_info(ckpt_path)
        models_dict[model_id] = item
        if len(item["urls"]) == 0:
            item["require_recheck"] = True
            if model_id in custom_dependencies["models"]:
                item["urls"] = custom_dependencies["models"][model_id].get("urls", [])
            missing_model_ids.append(model_id)
            
    # try to fetch from myshell model searcher
    missing_model_results_myshell = fetch_model_searcher_results(missing_model_ids)
    for missing_model_id, missing_model_urls in zip(missing_model_ids, missing_model_results_myshell):
        if len(missing_model_urls) > 0:
            models_dict[missing_model_id]["require_recheck"] = False
            models_dict[missing_model_id]["urls"] = missing_model_urls
            print("successfully fetch results from myshell", models_dict[missing_model_id])

    # step 3: handle local files
    process_local_file_path_async(file_mapping_dict, max_workers=20)
    files_dict = {v[0]: {"filename": windows_to_linux_path(os.path.relpath(v[2], BASE_PATH)), "urls": [v[1]]} for v in file_mapping_dict.values()}
    
    results = {
        "comfyui_version": comfyui_version,
        "custom_nodes": custom_nodes_list,
        "models": models_dict,
        "files": files_dict,
    }
    return results