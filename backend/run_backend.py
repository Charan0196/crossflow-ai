import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.main import app
    print("✅ Backend app loaded successfully!")
    
    import uvicorn
    print("🚀 Starting server on http://localhost:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
