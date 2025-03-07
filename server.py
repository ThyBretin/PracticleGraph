import os
from fastmcp import FastMCP
import logging
from practicle_utils import app_path
from createPracticle import createPracticle
from showPracticle import showPracticle
from listPracticle import listPracticle
from updatePracticle import updatePracticle
from exportPracticle import exportPracticle
from deletePracticle import deletePracticle
from list_dir import list_dir
from check_root import check_root

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PracticalGraph")

def main():
    mcp = FastMCP("practical-graph")
    mcp.tool()(createPracticle)
    mcp.tool()(showPracticle)
    mcp.tool()(listPracticle)
    mcp.tool()(updatePracticle)
    mcp.tool()(exportPracticle)
    mcp.tool()(deletePracticle)
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