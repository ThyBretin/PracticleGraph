import logging
from createCodebaseParticule import createCodebaseParticule

# Set up basic logging to console
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

result = createCodebaseParticule()
print(result["summary"])