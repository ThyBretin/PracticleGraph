import fastmcp
import logging
from particle_utils import logger
from addSubParticle import addSubParticle, addAllSubParticle
from createParticle import createParticle
from createCodebaseParticle import createCodebaseParticle
from loadCodebaseGraph import loadCodebaseGraph
from exportCodebaseGraph import exportCodebaseGraph
from loadGraph import loadGraph
from listGraph import listGraph
from updateParticle import updateParticle
from deleteParticle import deleteParticle
from exportGraph import exportGraph
from list_dir import list_dir
from check_root import check_root

logger.setLevel(logging.DEBUG)

def main():
    mcp = fastmcp.FastMCP("particle-graph")
    mcp.tool()(createParticle)
    mcp.tool()(updateParticle)
    mcp.tool()(deleteParticle)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(addSubParticle)
    mcp.tool()(addAllSubParticle)
    mcp.tool()(list_dir)
    mcp.tool()(check_root)
    
    # Register new codebase-wide tools
    mcp.tool()(createCodebaseParticle)
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