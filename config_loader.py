import json
from typing import Dict, Any
from validators import ConfigValidator
import logging
import os

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.mcp_config = None

    def load_config(self) -> Dict[str, Any]:
        try:
            # First check if we have an explicit config file
            config_file = os.getenv('CUSTOM_CONFIG', self.config_path)
            
            # If the file exists, load it directly
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            # Otherwise try to get config from MCP configuration
            else:
                config = self._get_config_from_mcp()
                
            if not ConfigValidator(config).validate():
                logger.warning('Configuration validation failed, using default values')
                config = self._get_default_config()

            return config
        except Exception as e:
            logger.error(f'Failed to load configuration: {e}')
            logger.info('Falling back to default configuration')
            return self._get_default_config()
            
    def _get_config_from_mcp(self) -> Dict[str, Any]:
        """Try to extract configuration from MCP environment"""
        # Check if MCP_CONFIG environment variable exists
        mcp_config_env = os.getenv('MCP_CONFIG')
        if mcp_config_env:
            try:
                # Parse the MCP configuration JSON
                mcp_config = json.loads(mcp_config_env)
                
                # Look for practical-graph server config
                if 'mcpServers' in mcp_config and 'practical-graph' in mcp_config['mcpServers']:
                    pg_config = mcp_config['mcpServers']['practical-graph']
                    if 'config' in pg_config:
                        logger.info('Using configuration from MCP environment')
                        return pg_config['config']
            except Exception as e:
                logger.error(f'Failed to parse MCP configuration: {e}')
        
        return self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration values"""
        app_path = os.getenv('APP_PATH', '/path/to/your/app')
        
        return {
            "app_path": app_path,
            "folder_groups": {
                "core": ["navigation", "state", "auth", "database"],
                "features": ["event", "discovery", "profile"],
                "api": ["endpoints"],
                "lib": ["utilities"]
            },
            "docs": {
                "business": "/docs/business-rules.md",
                "architecture": "/docs/architecture.md"
            },
            "watchdog": {
                "debounce_interval": 5,
                "batch_size": 10,
                "min_change_threshold": 3
            },
            "event_types": ["created", "modified", "deleted"],
            "critical_paths": [],
            "max_batch_time": 5
        }
