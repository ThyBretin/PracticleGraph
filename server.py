import fastmcp
import logging
from src.particle.particle_support import logger
from src.api.add_particle import addParticle
from src.api.create_graph import createGraph
from src.api.load_graph import loadGraph
from src.api.list_graph import listGraph
from src.api.update_graph import updateGraph
from src.api.delete_graph import deleteGraph
from src.api.export_graph import exportGraph

logger.setLevel(logging.DEBUG)

def main():
    mcp = fastmcp.FastMCP("particle-graph")
    mcp.tool()(addParticle)
    mcp.tool()(createGraph)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(updateGraph)
    mcp.tool()(deleteGraph)

    logger.info("Server initialized, entering main loop")
    mcp.run()  # Stdin/stdout

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise