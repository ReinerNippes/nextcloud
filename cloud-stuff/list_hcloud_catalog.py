#!/usr/bin/env python3
"""Print human-readable Hetzner Cloud image and server type tables.

Purpose:
- Help choose valid values for Pulumi stack files (image, server_type).

Usage:
  export HCLOUD_TOKEN=...
  python list_hcloud_catalog.py
  python list_hcloud_catalog.py --all-images
  python list_hcloud_catalog.py --location fsn1
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, Iterable, List

import requests

API_BASE = "https://api.hetzner.cloud/v1"


def fetch_all(endpoint: str, token: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    query = dict(params or {})
    query.setdefault("per_page", 50)
    query.setdefault("page", 1)

    items: List[Dict[str, Any]] = []
    while True:
        response = requests.get(f"{API_BASE}/{endpoint}", headers=headers, params=query, timeout=30)
        response.raise_for_status()
        payload = response.json()
        key = endpoint
        if key not in payload:
            raise RuntimeError(f"Unexpected API response key for endpoint {endpoint}")

        items.extend(payload[key])

        pagination = payload.get("meta", {}).get("pagination", {})
        current_page = int(pagination.get("page", query["page"]))
        last_page = int(pagination.get("last_page", current_page))
        if current_page >= last_page:
            break
        query["page"] = current_page + 1

    return items


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
        status = "deprecated" if img.get("deprecated") else "active"
        if not include_all and status == "deprecated":
            continue

        os_name = img.get("os_flavor") or img.get("type") or "unknown"
        description = img.get("description") or ""
        rows.append(
            [
                str(img.get("name") or ""),
                str(img.get("id") or ""),
                str(os_name),
                str(img.get("architecture") or ""),
                status,
                truncate(description.replace("\n", " "), 52),
            ]
        )

    rows.sort(key=lambda r: r[0])
    return rows


def server_type_rows(server_types: List[Dict[str, Any]], location: str | None) -> List[List[str]]:
    rows: List[List[str]] = []
    for st in server_types:
        prices = st.get("prices") or []
        price_text = "n/a"

        if location:
            loc_price = next((p for p in prices if p.get("location") == location), None)
            if loc_price:
                gross = (loc_price.get("price_hourly") or {}).get("gross")
                if gross is not None:
                    price_text = f"{gross} EUR/h"
        else:
            values: List[float] = []
            for p in prices:
                gross = (p.get("price_hourly") or {}).get("gross")
                if gross is None:
                    continue
                try:
                    values.append(float(gross))
                except (TypeError, ValueError):
                    continue
            if values:
                price_text = f"{min(values):.6f} EUR/h"

        rows.append(
            [
                str(st.get("name") or ""),
                str(st.get("architecture") or ""),
                str(st.get("cores") or ""),
                str(st.get("memory") or ""),
                str(st.get("disk") or ""),
                price_text,
            ]
        )

    rows.sort(key=lambda r: r[0])
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Hetzner images and server types for stack files")
    parser.add_argument(
        "--all-images",
        action="store_true",
        help="Include deprecated images in the output",
    )
    parser.add_argument(
        "--location",
        default=None,
        help="Location code for server type pricing (e.g. fsn1, nbg1, hel1)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv("HCLOUD_TOKEN", "").strip()
    if not token:
        print("Error: HCLOUD_TOKEN is not set.", file=sys.stderr)
        return 2

    try:
        images = fetch_all("images", token)
        server_types = fetch_all("server_types", token)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"Hetzner API error: HTTP {status}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to fetch Hetzner catalog: {exc}", file=sys.stderr)
        return 1

    img_rows = image_rows(images, include_all=args.all_images)
    st_rows = server_type_rows(server_types, location=args.location)

    print_table(
        "Available OS images (use for servers[].image)",
        ["name", "id", "os", "arch", "status", "description"],
        img_rows,
    )

    pricing_note = f" at location {args.location}" if args.location else " (cheapest hourly price)"
    print_table(
        f"Available server types (use for servers[].server_type){pricing_note}",
        ["name", "arch", "vCPU", "RAM(GB)", "Disk(GB)", "price"],
        st_rows,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
