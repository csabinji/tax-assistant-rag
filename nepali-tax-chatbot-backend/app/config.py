import os
import logging
from dotenv import load_dotenv

# Set Chroma telemetry env var as early as possible
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)

# OpenRouter config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL_NAME = "mistralai/mistral-7b-instruct:free"

# Knowledge base config
KNOWLEDGE_BASE_DOCUMENTS = [
    {"path": "nepali_tax_guide.pdf", "type": "pdf"},
    {"path": "nepali_tax_guide2.pdf", "type": "pdf"},
]
