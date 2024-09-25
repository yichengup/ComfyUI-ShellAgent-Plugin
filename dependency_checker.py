import os
import subprocess
import json
import logging
from .utils import compute_sha256, windows_to_linux_path

ComfyUIModelLoaders = {
    'VAELoader': (["vae_name"], "vae"),
    'CheckpointLoader': (["ckpt_name"], "checkpoints"),
    'CheckpointLoaderSimple': (["ckpt_name"], "checkpoints"),
    'DiffusersLoader': (["model_path"], "diffusers"),
    'unCLIPCheckpointLoader': (["ckpt_name"], "checkpoints"),
    'LoraLoader': (["lora_name"], "loras"),
    'LoraLoaderModelOnly': (["lora_name"], "loras"),
    'ControlNetLoader': (["control_net_name"], "controlnet"),
    'DiffControlNetLoader': (["control_net_name"], "controlnet"),
    'UNETLoader': (["unet_name"], "unet"),
    'CLIPLoader': (["clip_name"], "clip"),
    'DualCLIPLoader': (["clip_name1", "clip_name2"], "clip"),
    'CLIPVisionLoader': (["clip_name"], "clip_vision"),
    'StyleModelLoader': (["style_model_name"], "style_models"),
    'GLIGENLoader': (["gligen_name"], "gligen"),
}


ComfyUIFileLoaders = {
    'VAELoader': (["vae_name"], "vae"),
    'CheckpointLoader': (["ckpt_name"], "checkpoints"),
    'CheckpointLoaderSimple': (["ckpt_name"], "checkpoints"),
    'DiffusersLoader': (["model_path"], "diffusers"),
    'unCLIPCheckpointLoader': (["ckpt_name"], "checkpoints"),
    'LoraLoader': (["lora_name"], "loras"),
    'LoraLoaderModelOnly': (["lora_name"], "loras"),
    'ControlNetLoader': (["control_net_name"], "controlnet"),
    'DiffControlNetLoader': (["control_net_name"], "controlnet"),
    'UNETLoader': (["unet_name"], "unet"),
    'CLIPLoader': (["clip_name"], "clip"),
    'DualCLIPLoader': (["clip_name1", "clip_name2"], "clip"),
    'CLIPVisionLoader': (["clip_name"], "clip_vision"),
    'StyleModelLoader': (["style_model_name"], "style_models"),
    'GLIGENLoader': (["gligen_name"], "gligen"),
}


model_list_json = json.load(open(os.path.join(os.path.dirname(__file__), "model_info.json")))
def handle_model_info(ckpt_path):
    ckpt_path = windows_to_linux_path(ckpt_path)
    filename = os.path.basename(ckpt_path)
    dirname = os.path.dirname(ckpt_path)
    save_path = dirname.split('/', 1)[1]
    metadata_path = ckpt_path + ".json"
    if os.path.isfile(metadata_path):
        metadata = json.load(open(metadata_path))
        model_id = metadata["id"]
    else:
        logging.info(f"computing sha256 of {ckpt_path}")
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
        "save_path": save_path,
        "urls": urls,
    }
    return model_id, item


def inspect_repo_version(module_path):
    # Get the remote repository URL
    try:
        remote_url = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=module_path
        ).strip().decode()
    except subprocess.CalledProcessError:
        return {"error": "Failed to get remote repository URL"}

    # Get the latest commit hash
    try:
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=module_path
        ).strip().decode()
    except subprocess.CalledProcessError:
        return {"error": "Failed to get commit hash"}

    # Create and return the JSON result
    result = {
        "repo": remote_url,
        "commit": commit_hash
    }
    return result


def resolve_dependencies(prompt): # resolve custom nodes and models at the same time
    from nodes import NODE_CLASS_MAPPINGS
    custom_nodes = []
    ckpt_paths = []
    for node_id, node_info in prompt.items():
        node_class_type = node_info["class_type"]
        node_cls = NODE_CLASS_MAPPINGS[node_class_type]
        if hasattr(node_cls, "RELATIVE_PYTHON_MODULE"):
            custom_nodes.append(node_cls.RELATIVE_PYTHON_MODULE)
        if node_class_type in ComfyUIModelLoaders:
            input_names, save_path = ComfyUIModelLoaders[node_class_type]
            for input_name in input_names:
                ckpt_path = os.path.join("models", save_path, node_info["inputs"][input_name])
                ckpt_paths.append(ckpt_path)
            
    ckpt_paths = list(set(ckpt_paths))
    custom_nodes = list(set(custom_nodes))
    # step 1: custom nodes
    custom_nodes_list = [inspect_repo_version(custom_node.replace(".", "/")) for custom_node in custom_nodes]
    
    # step 2: models
    models_dict = {}
    for ckpt_path in ckpt_paths:
        model_id, item = handle_model_info(ckpt_path)
        models_dict[model_id] = item

    # step 1: handle the custom nodes version
    import pdb; pdb.set_trace()
    # return ckpt_pat
    # # step 1:
    # for class_type in 