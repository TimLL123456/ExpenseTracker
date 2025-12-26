from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests

class ApiError(RuntimeError):
    pass

def _join(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"

def process_text(*, text: str, base_url: str, timeout_sec: int = 15) -> Dict[str, Any]:
    url = _join(base_url, "/process")
    try:
        r = requests.post(url, json={"text": text}, timeout=timeout_sec)
        if r.status_code != 200:
            raise ApiError(f"{r.status_code} {r.text}")
        return r.json()
    except requests.RequestException as e:
        raise ApiError(str(e)) from e

def get_transactions(
    *,
    base_url: str,
    timeout_sec: int = 15,
    type_: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    url = _join(base_url, "/transactions")
    params: Dict[str, Any] = {}
    if type_:
        params["type"] = type_
    if category:
        params["category"] = category
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    try:
        r = requests.get(url, params=params, timeout=timeout_sec)
        if r.status_code != 200:
            raise ApiError(f"{r.status_code} {r.text}")
        return r.json()
    except requests.RequestException as e:
        raise ApiError(str(e)) from e

def add_asset_transaction(*, entry: Dict[str, Any], base_url: str, timeout_sec: int = 15) -> Dict[str, Any]:
    url = _join(base_url, "/asset_transactions")
    try:
        r = requests.post(url, json=entry, timeout=timeout_sec)
        if r.status_code != 200:
            raise ApiError(f"{r.status_code} {r.text}")
        return r.json()
    except requests.RequestException as e:
        raise ApiError(str(e)) from e

def get_asset_transactions(
    *, base_url: str, timeout_sec: int = 15, asset_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    url = _join(base_url, "/asset_transactions")
    params: Dict[str, Any] = {}
    if asset_type:
        params["asset_type"] = asset_type
    try:
        r = requests.get(url, params=params, timeout=timeout_sec)
        if r.status_code != 200:
            raise ApiError(f"{r.status_code} {r.text}")
        return r.json()
    except requests.RequestException as e:
        raise ApiError(str(e)) from e

def get_asset_holdings(
    *, base_url: str, timeout_sec: int = 15, asset_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    url = _join(base_url, "/asset_holdings")
    params: Dict[str, Any] = {}
    if asset_type:
        params["asset_type"] = asset_type
    try:
        r = requests.get(url, params=params, timeout=timeout_sec)
        if r.status_code != 200:
            raise ApiError(f"{r.status_code} {r.text}")
        return r.json()
    except requests.RequestException as e:
        raise ApiError(str(e)) from e