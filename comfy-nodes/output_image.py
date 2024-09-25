import folder_paths
from nodes import SaveImage

class ShellAgentSaveImage(SaveImage):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "output_name": ("STRING", {"multiline": False, "default": "output_image"},),
                "filename_prefix": ("STRING", {"default": "ComfyUI", "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
        
    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None, **extra_kwargs):
        results = super().save_images(images, filename_prefix, prompt, extra_pnginfo)
        results["shellagent_kwargs"] = extra_kwargs
        return results
    
    
NODE_CLASS_MAPPINGS = {
    "ShellAgentPluginSaveImage": ShellAgentSaveImage,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ShellAgentPluginSaveImage": "Save Image (ShellAgent Plugin)"
}