from fastmcp import FastMCP
import logging
from particule_utils import logger
from addSubParticule import addSubParticule, addAllSubParticule
from createParticule import createParticule
from loadGraph import loadGraph
from listGraph import listGraph
from updateParticule import updateParticule
from exportGraph import exportGraph
from deleteParticule import deleteParticule
from list_dir import list_dir
from check_root import check_root

logging.basicConfig(level=logging.DEBUG)

def main():
    mcp = FastMCP("particule-graph")
    mcp.tool()(createParticule)
    mcp.tool()(updateParticule)
    mcp.tool()(deleteParticule)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(addSubParticule)
    mcp.tool()(addAllSubParticule)
    mcp.tool()(list_dir)
    mcp.tool()(check_root)
    logger.info("Server initialized, entering main loop")
    mcp.run()  # Stdin/stdout

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise