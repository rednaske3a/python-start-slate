
import os
import shutil
import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from datetime import datetime

from src.constants.constants import MODEL_TYPES, FILE_EXTENSIONS
from src.utils.formatting import format_size
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StorageManager:
    """
    Manager for storage-related operations
    """
    def __init__(self, comfy_path: str):
        self.comfy_path = Path(comfy_path) if comfy_path else None
    
    def get_storage_usage(self) -> Tuple[int, int, Dict[str, int]]:
        """
        Get storage usage statistics
        
        Returns:
            Tuple of (total_size, free_size, category_sizes)
        """
        if not self.comfy_path or not self.comfy_path.exists():
            logger.error(f"ComfyUI directory not found: {self.comfy_path}")
            return 0, 0, {}
        
        # Get total disk usage
        try:
            total, used, free = shutil.disk_usage(self.comfy_path)
        except Exception as e:
            logger.error(f"Failed to get disk usage: {str(e)}")
            return 0, 0, {}
        
        # Get size of each model type
        category_sizes = {}
        
        for model_type, folder_path in MODEL_TYPES.items():
            type_path = self.comfy_path / folder_path
            if type_path.exists():
                size = self.get_folder_size(type_path)
                category_sizes[model_type if model_type != "TextualInversion" else "Embeddings"] = size
        
        # Simplify to main categories for display
        simplified = {
            "LoRAs": category_sizes.get("LORA", 0) + category_sizes.get("LoCon", 0),
            "Checkpoints": category_sizes.get("Checkpoint", 0),
            "Embeddings": category_sizes.get("Embeddings", 0),
            "VAEs": category_sizes.get("VAE", 0),
            "ControlNet": category_sizes.get("Controlnet", 0),
            "Upscalers": category_sizes.get("Upscaler", 0),
            "Other": sum(v for k, v in category_sizes.items() 
                        if k not in ["LORA", "LoCon", "Checkpoint", "Embeddings", "VAE", "Controlnet", "Upscaler"])
        }
        
        return total, free, simplified
    
    def get_folder_size(self, folder_path: Path) -> int:
        """
        Calculate the total size of a folder
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Size in bytes
        """
        total_size = 0
        try:
            for path in folder_path.glob("**/*"):
                if path.is_file():
                    total_size += path.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating folder size: {str(e)}")
        
        return total_size
    
    def scan_models(self) -> List[Dict]:
        """
        Scan for model metadata files
        
        Returns:
            List of model data dictionaries
        """
        if not self.comfy_path or not self.comfy_path.exists():
            logger.error(f"ComfyUI directory not found: {self.comfy_path}")
            return []
        
        models = []
        
        # Scan for metadata.json files
        for model_type, folder_path in MODEL_TYPES.items():
            type_dir = self.comfy_path / folder_path
            if not type_dir.exists():
                continue
            
            # Scan recursively for metadata.json files
            for metadata_file in type_dir.glob("**/metadata.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Check if this is a valid model metadata file
                    if "id" in metadata and "name" in metadata:
                        # Add path information
                        metadata["local_path"] = str(metadata_file.parent)
                        models.append(metadata)
                except Exception as e:
                    logger.error(f"Error processing metadata file {metadata_file}: {str(e)}")
        
        return models
    
    def delete_model(self, model_path: Path) -> bool:
        """
        Delete a model folder
        
        Args:
            model_path: Path to model folder
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not model_path.exists():
            logger.error(f"Model path does not exist: {model_path}")
            return False
        
        try:
            if model_path.is_dir():
                shutil.rmtree(model_path)
            else:
                model_path.unlink()
            logger.info(f"Deleted: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting model: {str(e)}")
            return False
    
    def find_model_path(self, model_id: str, model_type: str, 
                       base_model: str, model_name: str) -> Optional[Path]:
        """
        Find the path to a model folder
        
        Args:
            model_id: Model ID
            model_type: Model type
            base_model: Base model
            model_name: Model name
            
        Returns:
            Path to model folder if found, None otherwise
        """
        if not self.comfy_path or not self.comfy_path.exists():
            return None
            
        model_type_folder = MODEL_TYPES.get(model_type, MODEL_TYPES["Other"])
        
        # Sanitize model name for folder name
        import re
        safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', model_name)
        
        # Check if the path exists
        path = self.comfy_path / model_type_folder / base_model / safe_name
        if path.exists():
            return path
        
        # If not found directly, try to search for metadata.json files and check model ID
        for metadata_file in (self.comfy_path / model_type_folder).glob("**/metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                if str(metadata.get("id")) == str(model_id):
                    return metadata_file.parent
            except:
                pass
        
        return None
    
    def get_file_info(self, file_path: Path) -> Dict:
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        stat = file_path.stat()
        
        file_type = self.get_file_type(file_path)
        size = stat.st_size
        size_str = format_size(size)
        last_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        
        return {
            "name": file_path.name,
            "path": str(file_path),
            "type": file_type,
            "size": size,
            "size_str": size_str,
            "last_modified": last_modified
        }
    
    def get_file_type(self, file_path: Path) -> str:
        """
        Get the type of a file based on its extension
        
        Args:
            file_path: Path to file
            
        Returns:
            File type string
        """
        suffix = file_path.suffix.lower()
        
        for type_name, extensions in FILE_EXTENSIONS.items():
            if suffix in extensions:
                return type_name.capitalize()
        
        return suffix[1:].upper() if suffix else "Unknown"
    
    def find_duplicates(self) -> List[Dict]:
        """
        Find duplicate models based on name, type and base model
        
        Returns:
            List of duplicate groups
        """
        models = self.scan_models()
        
        # Group models by name, type and base model
        groups = {}
        for model in models:
            key = f"{model['name']}|{model['type']}|{model['base_model']}"
            if key not in groups:
                groups[key] = []
            groups[key].append(model)
        
        # Filter for groups with more than one model
        duplicates = [group for group in groups.values() if len(group) > 1]
        
        return duplicates
    
    def export_models(self, model_paths: List[Path], export_path: Path) -> Dict:
        """
        Export models to a specified path
        
        Args:
            model_paths: List of model paths to export
            export_path: Path to export to
            
        Returns:
            Dictionary with results
        """
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not export_path.exists():
            export_path.mkdir(parents=True)
        
        for path in model_paths:
            try:
                if path.is_dir():
                    target_path = export_path / path.name
                    shutil.copytree(path, target_path)
                else:
                    shutil.copy2(path, export_path)
                
                results["success"] += 1
                results["details"].append({
                    "path": str(path),
                    "success": True
                })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "path": str(path),
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_model_count_by_type(self) -> Dict[str, int]:
        """
        Get model counts by type
        
        Returns:
            Dictionary mapping types to counts
        """
        models = self.scan_models()
        
        counts = {}
        for model in models:
            model_type = model.get('type', 'Other')
            counts[model_type] = counts.get(model_type, 0) + 1
        
        return counts
    
    def find_orphaned_files(self) -> List[Dict]:
        """
        Find orphaned files (files not associated with any model)
        
        Returns:
            List of orphaned files info
        """
        if not self.comfy_path or not self.comfy_path.exists():
            return []
        
        # Get all model directories
        model_dirs = set()
        for metadata_file in self.comfy_path.glob("**/metadata.json"):
            model_dirs.add(str(metadata_file.parent))
        
        # Find all model files
        orphaned = []
        for model_type, folder_path in MODEL_TYPES.items():
            type_dir = self.comfy_path / folder_path
            if not type_dir.exists():
                continue
                
            for ext in FILE_EXTENSIONS["model"]:
                for file_path in type_dir.glob(f"**/*{ext}"):
                    parent_dir = str(file_path.parent)
                    if parent_dir not in model_dirs:
                        orphaned.append(self.get_file_info(file_path))
        
        return orphaned
