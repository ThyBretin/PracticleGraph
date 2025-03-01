from typing import Dict, Any
from pathlib import Path
import jsonschema
import os
import logging

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
                "debounce_interval": {"type": "number", "minimum": 1},
                "batch_size": {"type": "integer", "minimum": 1},
                "min_change_threshold": {"type": "integer", "minimum": 1}
            },
            "required": ["debounce_interval", "batch_size", "min_change_threshold"]
        },
        "event_types": {
            "type": "array",
            "items": {"type": "string"}
        },
        "critical_paths": {
            "type": "array",
            "items": {"type": "string"}
        },
        "max_batch_time": {"type": "number", "minimum": 1}
    },
    "required": ["app_path", "folder_groups", "docs", "watchdog"]
}

class ConfigValidator:
    REQUIRED_FIELDS = ['app_path', 'folder_groups', 'docs', 'watchdog']
    WATCHDOG_FIELDS = ['debounce_interval', 'batch_size', 'min_change_threshold']

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def validate(self) -> bool:
        try:
            jsonschema.validate(instance=self.config, schema=SCHEMA)
            return self._validate_config()
        except (jsonschema.ValidationError, FileNotFoundError) as e:
            logger.error(f"Config validation error: {str(e)}")
            return False

    def _validate_config(self) -> bool:
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.config:
                logger.error(f'Missing required configuration field: {field}')
                return False

        # Validate watchdog settings
        if not self._validate_watchdog(self.config['watchdog']):
            return False

        # Validate paths - but only if not running in Docker
        if not os.getenv('RUNNING_IN_DOCKER') and not self._validate_paths(self.config):
            return False

        return True

    def _validate_watchdog(self, watchdog_config: Dict[str, Any]) -> bool:
        for field in self.WATCHDOG_FIELDS:
            if field not in watchdog_config:
                logger.error(f'Missing watchdog configuration field: {field}')
                return False

        if not (1 <= watchdog_config['debounce_interval'] <= 60):
            logger.error('debounce_interval must be between 1 and 60 seconds')
            return False

        if not (1 <= watchdog_config['batch_size'] <= 100):
            logger.error('batch_size must be between 1 and 100')
            return False

        if not (1 <= watchdog_config['min_change_threshold'] <= watchdog_config['batch_size']):
            logger.error('min_change_threshold must be between 1 and batch_size')
            return False

        return True

    def _validate_paths(self, config: Dict[str, Any]) -> bool:
        # Don't validate paths if app_path isn't set yet
        if config['app_path'] == '/path/to/your/app':
            logger.warning('Using default app_path, skipping path validation')
            return True
            
        if not os.path.exists(config['app_path']):
            logger.error(f'App path does not exist: {config["app_path"]}')
            return False

        if not os.access(config['app_path'], os.R_OK):
            logger.error(f'App path is not readable: {config["app_path"]}')
            return False

        return True
