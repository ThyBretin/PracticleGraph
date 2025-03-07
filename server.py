import os
from fastmcp import FastMCP
import logging
from particule_utils import app_path
from createParticule import createParticule
from loadParticule import loadParticule
from listParticule import listParticule
from updateParticule import updateParticule
from exportParticule import exportParticule
from deleteParticule import deleteParticule
from list_dir import list_dir
from check_root import check_root

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PracticalGraph")

def main():
    mcp = FastMCP("practical-graph")
    mcp.tool()(createParticule)
    mcp.tool()(loadParticule)
    mcp.tool()(listParticule)
    mcp.tool()(updateParticule)
    mcp.tool()(exportParticule)
    mcp.tool()(deleteParticule)
    mcp.tool()(list_dir)
    mcp.tool()(check_root)
    logger.info("Server initialized, entering main loop")
    mcp.run()  # Keeps it alive

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise