import json
import os
import re
import logging
from typing import Dict, Any, Optional
from validators import ConfigValidator
from pathlib import Path
import glob

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.mcp_config = None
        self.env_vars = self._load_env_vars()
        self.config_cache = None
        self.config_timestamp = 0

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from various sources with priority order.
        
        Args:
            force_reload: If True, ignore any cached configuration
            
        Returns:
            Dict containing the configuration
        """
        # Check if we have a cached config and it's not a forced reload
        if self.config_cache and not force_reload:
            # Check if config file has been modified
            if self.config_path and os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
                if mtime <= self.config_timestamp:
                    return self.config_cache
            
            # Check if project config has been modified
            project_config_path = self._get_project_config_path()
            if project_config_path and os.path.exists(project_config_path):
                mtime = os.path.getmtime(project_config_path)
                if mtime <= self.config_timestamp:
                    return self.config_cache
        
        try:
            # Check sources in priority order
            config = None
            config_source = None
            
            # 1. Check for explicit config file from environment variable
            explicit_config = os.getenv('CUSTOM_CONFIG')
            if explicit_config:
                explicit_config = self._expand_env_vars(explicit_config)
                if os.path.exists(explicit_config):
                    logger.info(f"Loading configuration from CUSTOM_CONFIG: {explicit_config}")
                    with open(explicit_config, 'r') as f:
                        config = json.load(f)
                    config_source = explicit_config
            
            # 2. Check for project-level config from MCP configuration
            if not config:
                project_config, project_path = self._get_project_config()
                if project_config:
                    config = project_config
                    config_source = project_path
            
            # 3. Check for default config file
            if not config and self.config_path and os.path.exists(self.config_path):
                logger.info(f"Loading configuration from default path: {self.config_path}")
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                config_source = self.config_path
            
            # 4. Fall back to MCP embedded config
            if not config:
                mcp_config, mcp_source = self._get_config_from_mcp()
                if mcp_config:
                    config = mcp_config
                    config_source = mcp_source
                
            # Validate and use default if invalid
            if not config or not ConfigValidator(config).validate():
                logger.warning('Configuration validation failed, using default values')
                config = self._get_default_config()
                config_source = "default"
            
            # Process the configuration
            config = self._process_config(config)
            
            # Update cache
            self.config_cache = config
            if config_source and os.path.exists(config_source):
                self.config_timestamp = os.path.getmtime(config_source)
            else:
                self.config_timestamp = 0

            logger.info(f"Configuration loaded from {config_source}")
            return config
        except Exception as e:
            logger.error(f'Failed to load configuration: {e}')
            logger.info('Falling back to default configuration')
            default_config = self._get_default_config()
            return self._process_config(default_config)
    
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
        
        # Set app_path to current directory if not specified or not valid
        if 'app_path' not in processed or not processed['app_path'] or not os.path.exists(processed['app_path']):
            # Try to use PROJECT_PATH environment variable
            project_path = self.env_vars.get('PROJECT_PATH')
            if project_path and os.path.exists(project_path):
                processed['app_path'] = project_path
            else:
                # Fall back to current directory
                processed['app_path'] = os.getcwd()
        
        # Ensure app_path is absolute
        if not os.path.isabs(processed['app_path']):
            processed['app_path'] = os.path.abspath(processed['app_path'])
        
        return processed
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from .env file if it exists"""
        env_vars = {}
        
        # First load system environment variables
        for key, value in os.environ.items():
            env_vars[key] = value
            
        # Then try to load from .env file in current directory
        env_file = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_file):
            logger.info(f"Loading environment variables from {env_file}")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip().strip('"\'')
                        except ValueError:
                            logger.warning(f"Invalid line in .env file: {line}")
        
        # Check for Docker environment
        if os.getenv('RUNNING_IN_DOCKER') == 'true':
            env_vars['RUNNING_IN_DOCKER'] = 'true'
                        
        return env_vars
    
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
    
    def _get_project_config_path(self) -> Optional[str]:
        """Get the path to the project configuration file"""
        # Check if we have a PROJECT_PATH environment variable
        project_path = self.env_vars.get('PROJECT_PATH', os.getcwd())
        
        # Look for practical-graph.config.json in the project directory
        config_patterns = [
            os.path.join(project_path, 'practical-graph.config.json'),
            os.path.join(project_path, '.practical-graph.json'),
            os.path.join(project_path, 'config', 'practical-graph.json')
        ]
        
        for pattern in config_patterns:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
                
        return None
    
    def _get_project_config(self) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Try to load project-specific configuration"""
        config_file = self._get_project_config_path()
        
        if config_file and os.path.exists(config_file):
            logger.info(f"Loading project configuration from {config_file}")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Set app_path to project path if not specified
                if 'app_path' not in config:
                    project_path = os.path.dirname(config_file)
                    config['app_path'] = project_path
                    
                return config, config_file
            except Exception as e:
                logger.error(f"Failed to load project configuration: {e}")
                
        return None, None
            
    def _get_config_from_mcp(self) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
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
                    
                    # Check if config is a string (path to config file)
                    if 'config' in pg_config and isinstance(pg_config['config'], str):
                        config_path = self._expand_env_vars(pg_config['config'])
                        if os.path.exists(config_path):
                            logger.info(f"Loading configuration from MCP config path: {config_path}")
                            with open(config_path, 'r') as f:
                                return json.load(f), config_path
                    
                    # Check if config is an object
                    elif 'config' in pg_config and isinstance(pg_config['config'], dict):
                        logger.info('Using configuration from MCP environment')
                        return pg_config['config'], "MCP_CONFIG"
            except Exception as e:
                logger.error(f'Failed to parse MCP configuration: {e}')
        
        return None, None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration values"""
        app_path = self.env_vars.get('APP_PATH', os.getcwd())
        
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
            "max_batch_time": 5,
            "ignored_extensions": [".pyc", ".pyo", ".pyd", ".git", ".swp", ".tmp", "~"]
        }
    
    def save_config(self, config: Dict[str, Any], path: str = None) -> bool:
        """Save configuration to a file"""
        try:
            # If no path is specified, use the project config path
            if not path:
                path = self._get_project_config_path()
                if not path:
                    # Create a new config file in the project directory
                    project_path = self.env_vars.get('PROJECT_PATH', os.getcwd())
                    path = os.path.join(project_path, 'practical-graph.config.json')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Write config to file
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Configuration saved to {path}")
            
            # Update cache
            self.config_cache = config
            self.config_timestamp = os.path.getmtime(path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
