"""Run script for FastAPI service"""
import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)

sys.path.insert(0, project_root)
sys.path.insert(0, parent_dir)

# Change to the fastapi_service directory
os.chdir(current_dir)

# Now import and run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


