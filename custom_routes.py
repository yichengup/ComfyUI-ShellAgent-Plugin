from io import BytesIO
from pprint import pprint
from aiohttp import web
import os
import requests
import folder_paths
import json
import server
from PIL import Image
import time
import execution
import random
import traceback
import uuid
import asyncio
import logging
from urllib.parse import quote
import threading
import hashlib
import aiohttp
from aiohttp import ClientSession, web
import aiofiles
from typing import Dict, List, Union, Any, Optional
from PIL import Image
import copy
import struct
from aiohttp import web, ClientSession, ClientError, ClientTimeout, ClientResponseError
import atexit
from datetime import datetime
import nodes
import traceback

from .dependency_checker import resolve_dependencies


WORKFLOW_ROOT = "shellagent/comfy_workflow"

CustomNodeTypeMap = {
    "ShellAgentPluginInputText": "text",
    "ShellAgentPluginInputInteger": "integer",
    "ShellAgentPluginInputFloat": "number",
    "ShellAgentPluginInputImage": "image",
    "ShellAgentPluginInputVideo": "video",
    "ShellAgentPluginSaveImage": "image",
    "ShellAgentPluginSaveVideoVHS": "video",
}


def schema_validator(prompt):
    from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    input_names = []
    output_names = []
    schemas = {
        "inputs": {},
        "outputs": {}
    }
    for node_id, node_info in prompt.items():
        node_class_type = node_info["class_type"]
        node_cls = NODE_CLASS_MAPPINGS[node_class_type]
        if hasattr(node_cls, "RELATIVE_PYTHON_MODULE") and node_cls.RELATIVE_PYTHON_MODULE == "custom_nodes.ComfyUI-ShellAgent-Plugin":
            schema = {}
            if "input_name" in node_info["inputs"]:
                mode = "inputs"
                input_name = node_info["inputs"]["input_name"]
                if input_name not in input_names:
                    input_names.append(input_name)
                else:
                    raise ValueError(f"Duplicated input_name found in node {NODE_DISPLAY_NAME_MAPPINGS[node_class_type]} with ID={node_id}")
                # handle the schema at the same time
                schema["name"] = input_name
                
            elif "output_name" in node_info["inputs"]:
                mode = "outputs"
                output_name = node_info["inputs"]["output_name"]
                if output_name not in output_names:
                    output_names.append(output_name)
                else:
                    raise ValueError(f"Duplicated output_name found in node {NODE_DISPLAY_NAME_MAPPINGS[node_class_type]} with ID={node_id}")
                schema["name"] = output_name
            else:
                # neither input nor output
                continue
            if hasattr(node_cls, "validate"):
                schema = node_cls.validate(**node_info["inputs"])
            else:
                raise NotImplementedError("the validate is not implemented")
            schemas[mode][node_id] = schema
    return schemas
            
                
@server.PromptServer.instance.routes.get("/shellagent/list_workflow") # data same as queue prompt, plus workflow_name
async def shellagent_list_workflow(request):
    workflow_ids = os.listdir(WORKFLOW_ROOT)
    # append the metadata
    data = []
    for workflow_id in workflow_ids:

        metadata_file = os.path.join(WORKFLOW_ROOT, workflow_id, "metadata.json")
        metadata = json.load(open(metadata_file))
        item = {
            "id": workflow_id,
            "metadata": metadata
        }
        data.append(item)
    return web.json_response(data, status=400)
    
@server.PromptServer.instance.routes.post("/shellagent/get_file") # data same as queue prompt, plus workflow_name
async def shellagent_get_file(request):
    data = await request.json()
    assert data["filename"] in [
        "workflow_api.json",
        "dependencies.json",
        "metadata.json",
        "extra_data.json",
        "schemas.json",
    ]
    
    data = json.load(open(os.path.join(WORKFLOW_ROOT, data["workflow_id"], data["filename"])))
    return web.json_response(data, status=400)
    
@server.PromptServer.instance.routes.post("/shellagent/export") # data same as queue prompt, plus workflow_name
async def shellagent_export(request):
    data = await request.json()
    prompt = data["prompt"]
    # extra_data = data["extra_data"]
    workflow_id = str(uuid.uuid4())
    
    # metadata.json
    # metadata = {
    #     "name": data["workflow_name"],
    #     "workflow_id": workflow_id,
    #     "create_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # }
    
    return_dict = {}
    status = 200
    try:
        schemas = schema_validator(prompt)
        # custom_node.json
        dependency_results = resolve_dependencies(prompt)
        # save_root = os.path.join(WORKFLOW_ROOT, workflow_id)
        # os.makedirs(save_root, exist_ok=True)
        
        # fname_mapping = {
        #     "workflow_api.json": prompt,
        #     "dependencies.json": dependency_results,
        #     # "metadata.json": metadata,
        #     # "extra_data.json": extra_data,
        #     "schemas.json": schemas,
        # }
        
        # for fname, dict_to_save in fname_mapping.items():
        #     with open(os.path.join(save_root, fname), "w") as f:
        #         json.dump(dict_to_save, f, indent=2)
        
        return_dict = {
            "success": True,
            "dependencies": dependency_results,
            "schemas": schemas
        }
    except Exception as e:
        status = 400
        return_dict = {
            "success": False,
            "message": str(traceback.print_exc())
        }
    return web.json_response(return_dict, status=status)