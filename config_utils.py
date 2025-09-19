import json
from pathlib import Path

DEFAULT_SEARCH_QUERY = "tu-busqueda"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

def format_search_query(raw_query: str) -> str:
    sanitized = raw_query.strip()
    sanitized = sanitized.replace(' ', '-')
    return sanitized or DEFAULT_SEARCH_QUERY

def load_search_query() -> str:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            query = data.get("query", DEFAULT_SEARCH_QUERY)
            if isinstance(query, str) and query.strip():
                return format_search_query(query)
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_SEARCH_QUERY

def save_search_query(raw_query: str) -> str:
    query = format_search_query(raw_query)
    CONFIG_PATH.write_text(json.dumps({"query": query}, ensure_ascii=False, indent=2), encoding="utf-8")
    return query