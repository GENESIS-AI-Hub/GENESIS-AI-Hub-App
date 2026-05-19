PORT="${PORT:-8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="${SCRIPT_DIR}" uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips "'*'" --reload