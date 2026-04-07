import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import uvicorn
from app.config import API_HOST, API_PORT

if __name__ == "__main__":
    uvicorn.run("app.api.server:app", host=API_HOST, port=API_PORT, reload=True)
