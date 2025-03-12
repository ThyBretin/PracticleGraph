import json
import os
import re
import logging
from typing import Dict, Any, Optional
from validators import ConfigValidator

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self):
        self.env_vars = os.environ.copy()
        self.config_cache = None
        self.config_timestamp = 0

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from MCP config file and environment variables
        
        Args:
            force_reload: If True, ignore any cached configuration
            
        Returns:
            Dict containing the configuration
        """
        try:
            # Check if we have a cached config and it's not a forced reload
            if self.config_cache and not force_reload:
                return self.config_cache

            config = None
            
            # Get config path from environment (set by MCP)
            config_path = os.getenv('MCP_CONFIG_PATH')
            if config_path and os.path.exists(config_path):
                logger.info(f"Loading configuration from: {config_path}")
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            if not config or not ConfigValidator(config).validate():
                logger.error('No valid configuration found')
                return None
            
            # Process the configuration
            config = self._process_config(config)
            
            # Update cache
            self.config_cache = config
            self.config_timestamp = os.path.getmtime(config_path) if config_path else 0

            return config
            
        except Exception as e:
            logger.error(f'Failed to load configuration: {e}')
            return None
    
    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize the configuration"""
        # Expand environment variables in string values
        processed = {}
        for key, value in config.items():
            if isinstance(value, str):
                processed[key] = self._expand_env_vars(value)
            elif isinstance(value, dict):
                processed[key] = self._process_config(value)
            elif isinstance(value, list):
                processed[key] = [
                    self._expand_env_vars(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                processed[key] = value
        
        # Ensure required sections exist
        for section in ['watchdog', 'folder_groups', 'docs']:
            if section not in processed:
                processed[section] = {}
        
        return processed
    
    def _expand_env_vars(self, text: str) -> str:
        """Expand environment variables in text (${VAR} or $VAR format)"""
        if not text or not isinstance(text, str):
            return text
            
        # Replace ${VAR} format
        pattern = r'\${([a-zA-Z0-9_]+)}'
        matches = re.findall(pattern, text)
        for var in matches:
            if var in self.env_vars:
                text = text.replace(f"${{{var}}}", self.env_vars[var])
                
        # Replace $VAR format
        pattern = r'\$([a-zA-Z0-9_]+)'
        matches = re.findall(pattern, text)
        for var in matches:
            if var in self.env_vars:
                text = text.replace(f"${var}", self.env_vars[var])
                
        return text
