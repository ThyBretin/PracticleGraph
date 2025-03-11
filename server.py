import fastmcp
import logging
from particule_utils import logger
from addSubParticule import addSubParticule, addAllSubParticule
from createParticule import createParticule
from createCodebaseParticule import createCodebaseParticule
from loadCodebaseGraph import loadCodebaseGraph
from exportCodebaseGraph import exportCodebaseGraph
from loadGraph import loadGraph
from listGraph import listGraph
from updateParticule import updateParticule
from deleteParticule import deleteParticule
from exportGraph import exportGraph
from list_dir import list_dir
from check_root import check_root

logger.setLevel(logging.DEBUG)

def main():
    mcp = fastmcp.FastMCP("particule-graph")
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
    
    # Register new codebase-wide tools
    mcp.tool()(createCodebaseParticule)
    mcp.tool()(loadCodebaseGraph)
    mcp.tool()(exportCodebaseGraph)
    
    logger.info("Server initialized, entering main loop")
    mcp.run()  # Stdin/stdout

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise