import json
from pathlib import Path
from typing import Dict, Tuple

DEFAULT_SEARCH_QUERY = "tu-busqueda"
DEFAULT_MAX_PAGES = 5
MIN_MAX_PAGES = 1
MAX_MAX_PAGES = 20

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def _load_config_data() -> Dict[str, object]:
    if CONFIG_PATH.exists():
        try:
            raw = CONFIG_PATH.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else {}
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_config_data(data: Dict[str, object]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_search_query(raw_query: str) -> str:
    sanitized = raw_query.strip()
    sanitized = sanitized.replace(' ', '-')
    return sanitized or DEFAULT_SEARCH_QUERY


def _normalize_max_pages(value: object) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_PAGES
    return max(MIN_MAX_PAGES, min(MAX_MAX_PAGES, numeric))


def load_search_query() -> str:
    data = _load_config_data()
    query = data.get("query", DEFAULT_SEARCH_QUERY)
    if isinstance(query, str) and query.strip():
        return format_search_query(query)
    return DEFAULT_SEARCH_QUERY


def load_max_pages() -> int:
    data = _load_config_data()
    value = data.get("max_pages", DEFAULT_MAX_PAGES)
    return _normalize_max_pages(value)


def save_search_query(raw_query: str) -> str:
    query = format_search_query(raw_query)
    data = _load_config_data()
    data["query"] = query
    data["max_pages"] = _normalize_max_pages(data.get("max_pages", DEFAULT_MAX_PAGES))
    _write_config_data(data)
    return query


def save_search_preferences(raw_query: str, max_pages: object) -> Tuple[str, int]:
    query = format_search_query(raw_query)
    pages = _normalize_max_pages(max_pages)
    _write_config_data({"query": query, "max_pages": pages})
    return query, pages