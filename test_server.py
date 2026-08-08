import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from api.server import app

print("✓ FastAPI server imported cleanly!")
print("✓ Endpoints available:", [route.path for route in app.routes])
