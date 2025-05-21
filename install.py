
#!/usr/bin/env python3
"""
ComfyUI Model Manager - Installation script
"""
import os
import sys
import shutil
from pathlib import Path

def install_comfyui_mm():
    """Install ComfyUI Model Manager"""
    print("Installing ComfyUI Model Manager...")
    
    # Get the current directory (where install.py is located)
    current_dir = Path(__file__).parent.absolute()
    
    # Get the ComfyUI directory
    comfyui_dir = None
    while comfyui_dir is None:
        comfyui_path = input("Enter the path to your ComfyUI installation: ").strip()
        if not comfyui_path:
            print("Path cannot be empty.")
            continue
        
        # Convert to Path and expand user directory if needed
        path = Path(comfyui_path).expanduser()
        
        # Check if the directory exists
        if not path.exists():
            print(f"Directory '{path}' does not exist.")
            continue
        
        # Check if it looks like a ComfyUI installation
        if not (path / "main.py").exists() or not (path / "web").exists():
            print(f"Directory '{path}' doesn't appear to be a ComfyUI installation.")
            response = input("Install anyway? (y/n): ").strip().lower()
            if response != 'y':
                continue
        
        comfyui_dir = path
    
    # Create the custom_nodes directory if it doesn't exist
    custom_nodes_dir = comfyui_dir / "custom_nodes"
    custom_nodes_dir.mkdir(exist_ok=True)
    
    # Create the ComfyUI-MM directory in custom_nodes
    target_dir = custom_nodes_dir / "ComfyUI-MM"
    if target_dir.exists():
        print(f"Directory '{target_dir}' already exists.")
        response = input("Overwrite existing installation? (y/n): ").strip().lower()
        if response != 'y':
            print("Installation cancelled.")
            return
        
        # Remove existing directory
        shutil.rmtree(target_dir)
    
    # Copy the source files to the target directory
    source_dir = current_dir / "ComfyUI-MM"
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' not found.")
        return
    
    # Create target directory
    target_dir.mkdir(exist_ok=True)
    
    # Copy files
    for file in source_dir.glob("*.py"):
        shutil.copy2(file, target_dir)
    
    print("Creating configuration...")
    
    # Create config directory and configuration file
    config_dir = Path.home() / ".comfyui_mm"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.json"
    if not config_file.exists():
        import json
        config = {
            "comfy_path": str(comfyui_dir),
            "theme": "dark",
            "top_image_count": 9,
            "max_concurrent_downloads": 3,
            "download_threads": 3,
            "download_model": True,
            "download_images": True,
            "download_nsfw": False,
            "create_html": True,
            "auto_open_html": False
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    print(f"\nComfyUI Model Manager installed successfully to {target_dir}")
    print(f"Configuration saved to {config_file}")
    print("\nTo use ComfyUI Model Manager:")
    print("1. Run the app with: python custom_nodes/ComfyUI-MM/main.py")
    print("2. Add models from Civitai in the Download tab")
    print("3. Downloaded models will be placed in appropriate folders in ComfyUI")
    print("\nEnjoy!\n")

if __name__ == "__main__":
    install_comfyui_mm()
