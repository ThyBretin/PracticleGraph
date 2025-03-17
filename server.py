import fastmcp
import logging
from src.particle.particle_support import logger
from src.api.add_particle import addParticle
from src.api.create_graph import createGraph
from src.api.list_graph import listGraph
from src.api.export_graph import exportGraph
from src.api.particle_this import particleThis
logger.setLevel(logging.DEBUG)

def main():
    mcp = fastmcp.FastMCP("particle-graph")
    mcp.tool()(addParticle)
    mcp.tool()(createGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(listGraph)
    mcp.tool()(particleThis)
 

    logger.info("Server initialized, entering main loop")
    mcp.run()  # Stdin/stdout

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise