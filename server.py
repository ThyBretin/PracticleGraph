from fastmcp import FastMCP
import logging
from particule_utils import app_path
from check_root import check_root
from list_dir import list_dir
from addSubParticule import addSubParticule
from createParticule import createParticule
from updateParticule import updateParticule
from deleteParticule import deleteParticule
from listGraph import listGraph
from loadGraph import loadGraph
from exportGraph import exportGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ParticuleGraph")

def main():
    mcp = FastMCP("particule-graph")
    mcp.tool()(addSubParticule) 
    mcp.tool()(createParticule)
    mcp.tool()(updateParticule)
    mcp.tool()(deleteParticule)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(list_dir)
    mcp.tool()(check_root)
    logger.info("Server initialized, entering main loop")
    mcp.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise