from __future__ import annotations

from typing import Any, Dict, List
import time

import requests

API_BASE = "https://api.mercadolibre.com/categories"


def fetch_category_attributes(category_id: str, timeout: int = 12) -> List[Dict[str, Any]]:
    """
    Devuelve la lista de atributos de una categoría. Si falla, retorna [].
    """
    if not category_id:
        return []
    url = f"{API_BASE}/{category_id}/attributes"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def fetch_many_categories_attributes(category_ids: List[str], delay_sec: float = 0.25) -> Dict[str, List[Dict[str, Any]]]:
    """
    Llama en serie a /categories/{id}/attributes con un pequeño delay para no abusar.
    Devuelve {category_id: [atributos...]} para los IDs válidos.
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    seen = set()
    for cid in category_ids:
        if not cid or cid in seen:
            continue
        seen.add(cid)
        out[cid] = fetch_category_attributes(cid)
        if delay_sec and delay_sec > 0:
            time.sleep(delay_sec)
    return out