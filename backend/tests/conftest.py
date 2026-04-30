import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/interviewos",
)
os.environ["DEBUG"] = "False"
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
