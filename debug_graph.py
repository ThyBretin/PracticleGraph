import logging
from createCodebaseParticle import createCodebaseParticle

# Set up basic logging to console
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

result = createCodebaseParticle()
print(result["summary"])