import folder_paths
from PIL import Image, ImageOps
import numpy as np
import torch

class ShellAgentPluginInputText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_name": (
                    "STRING",
                    {"multiline": False, "default": "input_text"},
                ),
            },
            "optional": {
                "default_value": (
                    "STRING",
                    {"multiline": True, "default": ""},
                ),
                "description": (
                    "STRING",
                    {"multiline": True, "default": ""},
                ),
                "choices": (
                    "STRING",
                    {"multiline": False, "default": ""},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    FUNCTION = "run"

    CATEGORY = "shellagent"

    def run(self, input_name, default_value=None, display_name=None, description=None, choices=None):
        return [default_value]


NODE_CLASS_MAPPINGS = {"ShellAgentPluginInputText": ShellAgentPluginInputText}
NODE_DISPLAY_NAME_MAPPINGS = {"ShellAgentPluginInputText": "Input Text (ShellAgent Plugin)"}