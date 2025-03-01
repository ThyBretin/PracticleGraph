from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import jsonschema
import os
import logging
import re

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "properties": {
        "app_path": {"type": "string"},
        "folder_groups": {
            "type": "object",
            "patternProperties": {
                ".*": {"type": "array", "items": {"type": "string"}}
            }
        },
        "docs": {
            "type": "object",
            "patternProperties": {
                ".*": {"type": "string"}
            }
        },
        "watchdog": {
            "type": "object",
            "properties": {
                "debounce_interval": {"type": "number", "minimum": 0.1},
                "batch_size": {"type": "integer", "minimum": 1},
                "min_change_threshold": {"type": "integer", "minimum": 1}
            }
        },
        "event_types": {
            "type": "array",
            "items": {"type": "string", "enum": ["created", "modified", "deleted", "moved", "any"]}
        },
        "critical_paths": {
            "type": "array",
            "items": {"type": "string"}
        },
        "max_batch_time": {"type": "number", "minimum": 0.5},
        "ignored_extensions": {
            "type": "array",
            "items": {"type": "string"}
        },
        "ignored_paths": {
            "type": "array",
            "items": {"type": "string"}
        },
        "scan_on_startup": {"type": "boolean"},
        "database": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "backup_count": {"type": "integer", "minimum": 0, "maximum": 10}
            }
        }
    },
    "required": ["app_path"]
}

class ConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate the configuration against the schema and additional rules.
        Returns True if the configuration is valid, False otherwise.
        """
        # Reset errors and warnings
        self.errors = []
        self.warnings = []
        
        # First validate against JSON schema
        try:
            jsonschema.validate(instance=self.config, schema=SCHEMA)
        except jsonschema.ValidationError as e:
            self.errors.append(f"Schema validation error: {e.message}")
            logger.error(f"Config schema validation error: {e.message}")
            return False
            
        # Then validate additional rules
        self._validate_app_path()
        self._validate_watchdog()
        self._validate_paths()
        self._validate_environment_vars()
        
        # Log all warnings
        for warning in self.warnings:
            logger.warning(warning)
            
        # If there are any errors, validation fails
        if self.errors:
            for error in self.errors:
                logger.error(error)
            return False
            
        return True

    def _validate_app_path(self) -> None:
        """Validate the app_path setting"""
        if 'app_path' not in self.config:
            self.errors.append("Missing required configuration field: app_path")
            return
            
        app_path = self.config['app_path']
        
        # Skip validation if running in Docker or using placeholder
        if os.getenv('RUNNING_IN_DOCKER') == 'true':
            return
            
        if app_path == '/path/to/your/app' or app_path == '/app':
            self.warnings.append(f"Using default app_path: {app_path}")
            return
            
        # Check if path exists and is readable
        if not os.path.exists(app_path):
            self.errors.append(f"App path does not exist: {app_path}")
        elif not os.path.isdir(app_path):
            self.errors.append(f"App path is not a directory: {app_path}")
        elif not os.access(app_path, os.R_OK):
            self.errors.append(f"App path is not readable: {app_path}")

    def _validate_watchdog(self) -> None:
        """Validate watchdog settings"""
        if 'watchdog' not in self.config:
            self.warnings.append("Missing watchdog configuration, will use defaults")
            return
            
        watchdog = self.config['watchdog']
        
        # Check debounce_interval
        if 'debounce_interval' in watchdog:
            interval = watchdog['debounce_interval']
            if not isinstance(interval, (int, float)):
                self.errors.append(f"debounce_interval must be a number, got {type(interval).__name__}")
            elif not (0.1 <= interval <= 60):
                self.warnings.append(f"debounce_interval of {interval} seconds is outside recommended range (0.1-60)")
                
        # Check batch_size
        if 'batch_size' in watchdog:
            batch_size = watchdog['batch_size']
            if not isinstance(batch_size, int):
                self.errors.append(f"batch_size must be an integer, got {type(batch_size).__name__}")
            elif not (1 <= batch_size <= 1000):
                self.warnings.append(f"batch_size of {batch_size} is outside recommended range (1-1000)")
                
        # Check min_change_threshold
        if 'min_change_threshold' in watchdog:
            threshold = watchdog['min_change_threshold']
            if not isinstance(threshold, int):
                self.errors.append(f"min_change_threshold must be an integer, got {type(threshold).__name__}")
            elif 'batch_size' in watchdog and threshold > watchdog['batch_size']:
                self.errors.append(f"min_change_threshold ({threshold}) must be less than or equal to batch_size ({watchdog['batch_size']})")

    def _validate_paths(self) -> None:
        """Validate paths in the configuration"""
        # Skip validation if running in Docker
        if os.getenv('RUNNING_IN_DOCKER') == 'true':
            return
            
        # Validate docs paths
        if 'docs' in self.config:
            for doc_key, doc_path in self.config['docs'].items():
                # Skip validation if path starts with http or https
                if doc_path.startswith(('http://', 'https://')):
                    continue
                    
                # Skip validation if path is a placeholder
                if doc_path.startswith('/docs/') and not os.path.isabs(doc_path):
                    continue
                    
                # Check if path exists
                if not os.path.exists(doc_path):
                    self.warnings.append(f"Documentation path does not exist: {doc_path}")
                elif not os.access(doc_path, os.R_OK):
                    self.warnings.append(f"Documentation path is not readable: {doc_path}")
                    
        # Validate database path
        if 'database' in self.config and 'path' in self.config['database']:
            db_path = self.config['database']['path']
            
            # Check if parent directory exists and is writable
            parent_dir = os.path.dirname(db_path)
            if parent_dir and not os.path.exists(parent_dir):
                self.warnings.append(f"Database parent directory does not exist: {parent_dir}")
            elif parent_dir and not os.access(parent_dir, os.W_OK):
                self.errors.append(f"Database parent directory is not writable: {parent_dir}")

    def _validate_environment_vars(self) -> None:
        """Check for environment variables in the configuration that might not be set"""
        # Convert config to string to check for environment variables
        config_str = str(self.config)
        
        # Look for ${VAR} pattern
        env_vars = re.findall(r'\${([a-zA-Z0-9_]+)}', config_str)
        env_vars.extend(re.findall(r'\$([a-zA-Z0-9_]+)', config_str))
        
        # Check if environment variables are set
        for var in set(env_vars):
            if not os.getenv(var):
                self.warnings.append(f"Environment variable not set: {var}")
                
    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.errors
        
    def get_warnings(self) -> List[str]:
        """Get list of validation warnings"""
        return self.warnings
