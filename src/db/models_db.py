
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.models.model_info import ModelInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ModelsDatabase:
    """
    Database for managing model information with both JSON and SQLite backends
    """
    def __init__(self):
        """Initialize database"""
        # Set up database directory
        self.db_dir = Path.home() / ".civitai_manager" / "db"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON file path (legacy)
        self.json_path = Path.home() / ".civitai_models_db.json"
        
        # SQLite database path
        self.sqlite_path = self.db_dir / "models.db"
        
        # Initialize models dictionary (cached from database)
        self.models = {}
        
        # Initialize SQLite database
        self._init_sqlite()
        
        # Load models from database
        self.load()
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Create models table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                base_model TEXT NOT NULL,
                nsfw INTEGER NOT NULL DEFAULT 0,
                favorite INTEGER NOT NULL DEFAULT 0,
                download_date TEXT,
                last_updated TEXT,
                size INTEGER NOT NULL DEFAULT 0
            )
            ''')
            
            # Create indices for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON models(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON models(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_base_model ON models(base_model)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorite ON models(favorite)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
    
    def load(self) -> Dict[str, Dict[str, Any]]:
        """Load models from database"""
        models = {}
        
        # Try loading from SQLite first
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, data FROM models')
            rows = cursor.fetchall()
            
            for row in rows:
                model_id = row['id']
                model_data = json.loads(row['data'])
                models[model_id] = model_data
                
            conn.close()
            
            if rows:
                logger.info(f"Loaded {len(models)} models from SQLite database")
                self.models = models
                return models
                
        except Exception as e:
            logger.error(f"Error loading from SQLite database: {e}")
        
        # If SQLite failed or had no data, try loading from JSON
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                
                logger.info(f"Loaded {len(models)} models from JSON database")
                
                # Migrate JSON data to SQLite
                self._migrate_json_to_sqlite(models)
                
            except Exception as e:
                logger.error(f"Error loading JSON database: {e}")
        
        self.models = models
        return models
    
    def _migrate_json_to_sqlite(self, json_models):
        """Migrate data from JSON to SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            for model_id, model_data in json_models.items():
                self.add_model_to_sqlite(cursor, ModelInfo.from_dict(model_data))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Migrated {len(json_models)} models from JSON to SQLite")
            
        except Exception as e:
            logger.error(f"Error migrating to SQLite: {e}")
    
    def add_model_to_sqlite(self, cursor, model_info: ModelInfo):
        """Add a model to SQLite database"""
        model_id = str(model_info.id)
        model_data = json.dumps(model_info.to_dict())
        
        cursor.execute('''
        INSERT OR REPLACE INTO models 
        (id, data, name, type, base_model, nsfw, favorite, download_date, last_updated, size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_id, 
            model_data, 
            model_info.name,
            model_info.type, 
            model_info.base_model,
            1 if model_info.nsfw else 0,
            1 if model_info.favorite else 0,
            model_info.download_date,
            model_info.last_updated,
            model_info.size
        ))
    
    def save(self) -> bool:
        """Save models to database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Begin transaction for better performance
            cursor.execute('BEGIN TRANSACTION')
            
            # Clear existing data
            cursor.execute('DELETE FROM models')
            
            # Add all models
            for model_id, model_data in self.models.items():
                model_info = ModelInfo.from_dict(model_data)
                self.add_model_to_sqlite(cursor, model_info)
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            logger.info("Models database saved successfully to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to SQLite database: {e}")
            return False
    
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get a model by ID"""
        return self.models.get(model_id, {})
    
    def add_model(self, model_info: ModelInfo) -> None:
        """Add or update a model in the database"""
        model_id = str(model_info.id)
        self.models[model_id] = model_info.to_dict()
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            self.add_model_to_sqlite(cursor, model_info)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding model to SQLite: {e}")
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the database"""
        if model_id in self.models:
            del self.models[model_id]
            
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM models WHERE id = ?', (model_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error removing model from SQLite: {e}")
            
            return True
        return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Get all models as a list"""
        return list(self.models.values())
    
    def update_model_field(self, model_id: str, field: str, value: Any) -> bool:
        """Update a specific field in a model"""
        if model_id in self.models:
            self.models[model_id][field] = value
            
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                
                # For certain important fields, update the indexed column too
                if field in ["name", "type", "base_model", "nsfw", "favorite", "download_date", "last_updated", "size"]:
                    if field == "nsfw" or field == "favorite":
                        cursor.execute(f'UPDATE models SET {field} = ? WHERE id = ?', 
                                     (1 if value else 0, model_id))
                    else:
                        cursor.execute(f'UPDATE models SET {field} = ? WHERE id = ?', 
                                     (value, model_id))
                
                # Always update the JSON data field
                cursor.execute('UPDATE models SET data = ? WHERE id = ?',
                             (json.dumps(self.models[model_id]), model_id))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error updating model field in SQLite: {e}")
            
            return True
        return False
    
    def clear(self) -> None:
        """Clear all models from the database"""
        self.models = {}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM models')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing SQLite database: {e}")
    
    def search_models(self, query=None, filters=None) -> List[Dict[str, Any]]:
        """
        Search models with filtering and sorting
        
        Args:
            query: Text search query
            filters: Dict of filters (type, base_model, nsfw, favorite)
            
        Returns:
            List of matching models
        """
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            params = []
            conditions = []
            
            # Text search
            if query and query.strip():
                conditions.append("(name LIKE ? OR data LIKE ?)")
                search_term = f"%{query.strip()}%"
                params.extend([search_term, search_term])
            
            # Apply filters
            if filters:
                if 'type' in filters and filters['type']:
                    conditions.append("type = ?")
                    params.append(filters['type'])
                
                if 'base_model' in filters and filters['base_model']:
                    conditions.append("base_model = ?")
                    params.append(filters['base_model'])
                
                if 'nsfw' in filters:
                    conditions.append("nsfw = ?")
                    params.append(1 if filters['nsfw'] else 0)
                
                if 'favorite' in filters:
                    conditions.append("favorite = ?")
                    params.append(1 if filters['favorite'] else 0)
            
            # Build SQL query
            sql = "SELECT data FROM models"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            # Execute query
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert results to model dicts
            results = [json.loads(row['data']) for row in rows]
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching models in SQLite: {e}")
            
            # Fallback to in-memory search
            results = list(self.models.values())
            
            # Apply text search
            if query and query.strip():
                query = query.lower()
                results = [
                    model for model in results 
                    if query in model.get('name', '').lower() or 
                    query in model.get('description', '').lower() or
                    any(query in tag.lower() for tag in model.get('tags', []))
                ]
            
            # Apply filters
            if filters:
                if 'type' in filters and filters['type']:
                    results = [m for m in results if m.get('type') == filters['type']]
                
                if 'base_model' in filters and filters['base_model']:
                    results = [m for m in results if m.get('base_model') == filters['base_model']]
                
                if 'nsfw' in filters:
                    results = [m for m in results if m.get('nsfw') == filters['nsfw']]
                
                if 'favorite' in filters:
                    results = [m for m in results if m.get('favorite') == filters['favorite']]
            
            return results
    
    def get_model_types(self) -> List[str]:
        """Get all unique model types"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT type FROM models ORDER BY type')
            types = [row[0] for row in cursor.fetchall()]
            conn.close()
            return types
        except Exception as e:
            logger.error(f"Error getting model types from SQLite: {e}")
            # Fallback
            return list(set(m.get('type', '') for m in self.models.values() if m.get('type')))
    
    def get_base_models(self) -> List[str]:
        """Get all unique base models"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT base_model FROM models ORDER BY base_model')
            base_models = [row[0] for row in cursor.fetchall()]
            conn.close()
            return base_models
        except Exception as e:
            logger.error(f"Error getting base models from SQLite: {e}")
            # Fallback
            return list(set(m.get('base_model', '') for m in self.models.values() if m.get('base_model')))
