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
from .dependency_checker import resolve_dependencies



@server.PromptServer.instance.routes.post("/shellagent/export") # data same as queue prompt, plus workflow_name
async def shellagent_export(request):
    data = await request.json()
    client_id = data["client_id"]
    prompt = data["prompt"]
    extra_data = data["extra_data"]
    workflow_name = data["workflow_name"]
    workflow_id = str(uuid.uuid4())
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # metadata.json
    metadata = {
        "name": data["workflow_name"],
        "workflow_id": workflow_id,
        "create_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # custom_node.json
    resolve_dependencies(prompt)
    
    workflow = prompt # used during running
    
    # 
    import pdb; pdb.set_trace()