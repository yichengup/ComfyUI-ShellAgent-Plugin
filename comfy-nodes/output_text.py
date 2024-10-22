
json_type_mapipng = {
    "text": "string",
    "float": "number",
    "integer": "integer"
}

class ShellAgentOutputText:
    TYPE_STR = "text"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                s.TYPE_STR: ("STRING", {"tooltip": f"The {s.TYPE_STR} to output."}),
                "output_name": ("STRING", {"multiline": False, "default": f"output_{s.TYPE_STR}"},),
            },
        }
        
    RETURN_TYPES = ()
    FUNCTION = "output_var"

    OUTPUT_NODE = True

    CATEGORY = "shellagent"
    DESCRIPTION = "output the text"
    
    @classmethod
    def validate(cls, **kwargs):
        schema = {
            "title": kwargs["output_name"],
            "type": json_type_mapipng[cls.TYPE_STR]
        }
        return schema
    
    def output_var(self, **kwargs):
        results = {"ui": {"output": [kwargs[self.TYPE_STR]]}}
        return results
    
class ShellAgentOutputFloat(ShellAgentOutputText):
    TYPE_STR = "float"
    DESCRIPTION = "output the float"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                s.TYPE_STR: ("STRING", {"tooltip": f"The {s.TYPE_STR} to output."}),
                "output_name": ("STRING", {"multiline": False, "default": f"output_{s.TYPE_STR}"},),
            },
        }
    
    
class ShellAgentOutputInteger(ShellAgentOutputText):
    TYPE_STR = "integer"
    DESCRIPTION = "output the integer"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                s.TYPE_STR: ("STRING", {"tooltip": f"The {s.TYPE_STR} to output."}),
                "output_name": ("STRING", {"multiline": False, "default": f"output_{s.TYPE_STR}"},),
            },
        }
    
    
NODE_CLASS_MAPPINGS = {
    "ShellAgentPluginOutputText": ShellAgentOutputText,
    "ShellAgentPluginOutputFloat": ShellAgentOutputFloat,
    "ShellAgentPluginOutputInteger": ShellAgentOutputInteger
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ShellAgentPluginOutputText": "Output Text (ShellAgent Plugin)",
    "ShellAgentPluginOutputFloat": "Output Float (ShellAgent Plugin)",
    "ShellAgentPluginOutputInteger": "Output Integer (ShellAgent Plugin)",
}