#!/usr/bin/env python3
"""Print human-readable Scaleway image and server type tables.

Purpose:
- Help choose valid values for Pulumi stack files (image, commercial_type).

Usage:
  export SCW_SECRET_KEY=...
  python list_scaleway_catalog.py
  python list_scaleway_catalog.py --zone fr-par-1
  python list_scaleway_catalog.py --all-images
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, Iterable, List

import requests

API_BASE = "https://api.scaleway.com/instance/v1"


def api_get(path: str, token: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    headers = {"X-Auth-Token": token}
    response = requests.get(f"{API_BASE}{path}", headers=headers, params=params or {}, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_images(zone: str, token: str) -> List[Dict[str, Any]]:
    page = 1
    per_page = 100
    items: List[Dict[str, Any]] = []

    while True:
        payload = api_get(f"/zones/{zone}/images", token, {"page": page, "per_page": per_page})
        page_items = payload.get("images") or []
        items.extend(page_items)

        # Scaleway APIs expose totals in different fields depending on endpoint versions.
        total_count = int(payload.get("total_count") or payload.get("total") or len(items))
        if len(items) >= total_count or not page_items:
            break
        page += 1

    return items


def fetch_server_types(zone: str, token: str) -> List[Dict[str, Any]]:
    payload = api_get(f"/zones/{zone}/products/servers", token)
    servers_obj = payload.get("servers") or {}

    rows: List[Dict[str, Any]] = []
    if isinstance(servers_obj, dict):
        for name, data in servers_obj.items():
            item = dict(data)
            item.setdefault("name", name)
            rows.append(item)
    elif isinstance(servers_obj, list):
        rows = list(servers_obj)

    return rows


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def print_table(title: str, columns: List[str], rows: Iterable[List[str]]) -> None:
    rows_list = [list(r) for r in rows]
    widths = [len(c) for c in columns]
    for row in rows_list:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    print(f"\n{title}")
    print("-" * sum(widths) + "-" * (3 * (len(columns) - 1)))
    print("  ".join(col.ljust(widths[i]) for i, col in enumerate(columns)))
    print("  ".join("-" * widths[i] for i in range(len(columns))))
    for row in rows_list:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(columns))))


def image_rows(images: List[Dict[str, Any]], include_all: bool) -> List[List[str]]:
    rows: List[List[str]] = []
    for img in images:
        status = "deprecated" if img.get("state") == "deprecated" else "active"
        if not include_all and status == "deprecated":
            continue

        rows.append(
            [
                str(img.get("name") or ""),
                str(img.get("id") or ""),
                str(img.get("arch") or ""),
                str(img.get("creation_date") or "")[:10],
                status,
            ]
        )

    rows.sort(key=lambda r: r[0])
    return rows


def server_rows(server_types: List[Dict[str, Any]]) -> List[List[str]]:
    rows: List[List[str]] = []

    for st in server_types:
        hourly_price = st.get("hourly_price") or {}
        monthly_price = st.get("monthly_price") or {}

        rows.append(
            [
                str(st.get("name") or ""),
                str(st.get("ncpus") or ""),
                str(st.get("ram") or ""),
                str(st.get("volumes_constraint") or ""),
                str(hourly_price.get("value") or "n/a"),
                str(monthly_price.get("value") or "n/a"),
                truncate(str(st.get("description") or ""), 42),
            ]
        )

    rows.sort(key=lambda r: r[0])
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Scaleway images and server types for stack files")
    parser.add_argument("--zone", default="fr-par-1", help="Scaleway zone (default: fr-par-1)")
    parser.add_argument("--all-images", action="store_true", help="Include deprecated images")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv("SCW_SECRET_KEY", "").strip()
    if not token:
        print("Error: SCW_SECRET_KEY is not set.", file=sys.stderr)
        return 2

    try:
        images = fetch_images(args.zone, token)
        server_types = fetch_server_types(args.zone, token)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"Scaleway API error: HTTP {status}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to fetch Scaleway catalog: {exc}", file=sys.stderr)
        return 1

    print_table(
        f"Available OS images in zone {args.zone} (use for servers[].image)",
        ["name", "id", "arch", "created", "status"],
        image_rows(images, include_all=args.all_images),
    )

    print_table(
        f"Available server types in zone {args.zone} (use for servers[].commercial_type)",
        ["name", "vCPU", "RAM(bytes)", "volumes", "EUR/h", "EUR/mo", "description"],
        server_rows(server_types),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
