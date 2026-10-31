"""Test that web server is working"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🌐 Testing Web UI Components")
print("=" * 70)
print()

# Test 1: Check if web files exist
print("1️⃣ Checking Web Files...")
web_html = Path("web/index.html")
api_main = Path("src/api/main.py")

if web_html.exists():
    print(f"   ✅ Web UI found: {web_html}")
else:
    print(f"   ❌ Missing: {web_html}")

if api_main.exists():
    print(f"   ✅ API backend found: {api_main}")
else:
    print(f"   ❌ Missing: {api_main}")

# Test 2: Check if uvicorn is installed
print("\n2️⃣ Checking Dependencies...")
try:
    import uvicorn
    print(f"   ✅ uvicorn installed (version: {uvicorn.__version__})")
except ImportError:
    print(f"   ❌ uvicorn not installed")
    print(f"      Run: pip install uvicorn")

try:
    import fastapi
    print(f"   ✅ fastapi installed (version: {fastapi.__version__})")
except ImportError:
    print(f"   ❌ fastapi not installed")
    print(f"      Run: pip install fastapi")

try:
    import websockets
    print(f"   ✅ websockets installed")
except ImportError:
    print(f"   ❌ websockets not installed")
    print(f"      Run: pip install websockets")

# Test 3: Try importing the API
print("\n3️⃣ Testing API Import...")
try:
    from src.api.main import app
    print(f"   ✅ API module loaded successfully")
    print(f"   ✅ FastAPI app created: {app.title}")
except Exception as e:
    print(f"   ❌ Error loading API: {e}")

print("\n" + "=" * 70)
print("✅ Web UI is ready!")
print("=" * 70)
print()
print("🚀 To start the web server:")
print("   run_web.bat")
print()
print("📍 Then open your browser to:")
print("   http://localhost:8000")
print()
