from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Any

import requests


def discover_instances(registry_url: str, service_name: str) -> list[dict[str, Any]]:
    resp = requests.get(f"{registry_url}/discover/{service_name}", timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Discovery failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    return data.get("instances", [])


def pick_random(instances: list[dict[str, Any]]) -> dict[str, Any]:
    if not instances:
        raise RuntimeError("No instances returned from registry")
    return random.choice(instances)


def main() -> int:
    parser = argparse.ArgumentParser(description="Discovery client that calls a random service instance.")
    parser.add_argument("service_name", help="Service to discover (e.g. user-service)")
    parser.add_argument("--registry", default="http://localhost:5001", help="Registry base URL")
    parser.add_argument("--path", default="/hello", help="Path to call on the service instance")
    parser.add_argument("--calls", type=int, default=10, help="Number of calls to make")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between calls")
    args = parser.parse_args()

    print(f"🔎 Discovering instances for {args.service_name} via {args.registry}")
    instances = discover_instances(args.registry, args.service_name)
    print(f"✓ Found {len(instances)} instance(s)")
    for inst in instances:
        print(f"  - {inst.get('address')}")

    print("\n🎯 Calling random instances:")
    for i in range(1, args.calls + 1):
        instances = discover_instances(args.registry, args.service_name)
        chosen = pick_random(instances)
        base = chosen["address"].rstrip("/")
        url = f"{base}{args.path}"

        try:
            r = requests.get(url, timeout=5)
            payload = r.json() if "application/json" in r.headers.get("content-type", "") else {"body": r.text}
            instance_id = payload.get("instance_id", "unknown")
            print(f"{i:02d}. {url} -> {r.status_code} (instance_id={instance_id})")
        except Exception as e:
            print(f"{i:02d}. {url} -> ERROR: {e}")

        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    sys.exit(main())

