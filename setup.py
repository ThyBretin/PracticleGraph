#!/usr/bin/env python3
"""
Setup script for Practical Graph MCP Server
This script helps set up the initial configuration for the Practical Graph MCP server.
"""

import os
import json
import shutil
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("setup")

def setup_config(project_path, force=False):
    """Set up the initial configuration for the Practical Graph MCP server"""
    # Determine the project path
    if not project_path:
        project_path = os.getcwd()
    
    project_path = os.path.abspath(project_path)
    logger.info(f"Setting up Practical Graph for project: {project_path}")
    
    # Check if the project path exists
    if not os.path.exists(project_path):
        logger.error(f"Project path does not exist: {project_path}")
        return False
    
    # Check if config already exists
    config_file = os.path.join(project_path, 'practical-graph.config.json')
    if os.path.exists(config_file) and not force:
        logger.warning(f"Configuration file already exists: {config_file}")
        logger.warning("Use --force to overwrite")
        return False
    
    # Load the example config
    example_config_path = os.path.join(os.path.dirname(__file__), 'practical-graph.config.example.json')
    if not os.path.exists(example_config_path):
        logger.error(f"Example configuration file not found: {example_config_path}")
        return False
    
    try:
        with open(example_config_path, 'r') as f:
            config = json.load(f)
        
        # Replace environment variables
        config_str = json.dumps(config)
        config_str = config_str.replace('${PROJECT_PATH}', project_path)
        config = json.loads(config_str)
        
        # Create the config file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration file created: {config_file}")
        
        # Create docs directory if it doesn't exist
        docs_dir = os.path.join(project_path, 'docs')
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            logger.info(f"Created docs directory: {docs_dir}")
            
            # Create sample docs
            with open(os.path.join(docs_dir, 'business-rules.md'), 'w') as f:
                f.write("# Business Rules\n\nThis document contains business rules for the project.\n")
            
            with open(os.path.join(docs_dir, 'architecture.md'), 'w') as f:
                f.write("# Architecture\n\nThis document describes the architecture of the project.\n")
            
            with open(os.path.join(docs_dir, 'api.md'), 'w') as f:
                f.write("# API Documentation\n\nThis document contains API documentation for the project.\n")
            
            logger.info("Created sample documentation files")
        
        # Create database directory
        db_dir = os.path.join(project_path, '.practical-graph')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up configuration: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Setup Practical Graph MCP Server')
    parser.add_argument('--project', '-p', help='Path to the project directory')
    parser.add_argument('--force', '-f', action='store_true', help='Force overwrite of existing configuration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if setup_config(args.project, args.force):
        logger.info("Setup completed successfully")
        logger.info("You can now run the Practical Graph MCP server with: python server.py")
    else:
        logger.error("Setup failed")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
