"""Export the running API to static JSON for a serverless demo build.

GitHub Pages serves static files only and cannot run FastAPI. This script
captures the real API responses - including metrics from genuinely trained
models - into a tree of JSON files that the frontend can read directly when it
is built in static demo mode.

It queries the LIVE backend with real role tokens rather than re-deriving
anything from the database, so the exported payloads are exactly what the API
returns. No value here is invented.

Usage:
    python scripts/export_static_demo.py [--base-url URL] [--out DIR]

Requires the backend to be running and seeded.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_BASE = "http://127.0.0.1:8000"
DEFAULT_OUT = Path("frontend/public/demo-api")
PASSWORD = "demo1234"
ACCOUNTS = {
    "data_scientist": "scientist@evsoh.io",
    "technician": "tech@evsoh.io",
    "ev_user": "owner@evsoh.io",
}

written: list[str] = []
failed: list[str] = []


def call(base: str, path: str, token: str | None = None, method: str = "GET",
         payload: dict | None = None) -> tuple[int, object]:
    """Return (status, parsed_json). Never raises on HTTP error status."""
    url = base + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode())
        except Exception:
            return exc.code, None
    except Exception as exc:
        print(f"  ERROR {path}: {type(exc).__name__}: {exc}")
        return 0, None


def write(out: Path, rel: str, body: object) -> None:
    dest = out / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(body, indent=1, ensure_ascii=True), encoding="ascii")
    written.append(rel)


def capture(base: str, out: Path, path: str, rel: str, token: str | None) -> object:
    """GET `path` and persist it at `rel`. Returns the body (None on failure)."""
    status, body = call(base, path, token)
    if status != 200:
        failed.append(f"{path} -> HTTP {status}")
        print(f"  SKIP {path} (HTTP {status})")
        return None
    write(out, rel, body)
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    base = args.base_url.rstrip("/") + "/api"
    out = Path(args.out)

    status, _ = call(base, "/config/thresholds")
    if status != 200:
        print(f"Backend not reachable at {args.base_url} (status {status}).")
        print("Start it first:  cd backend && python -m uvicorn app.main:app --port 8000")
        return 2

    if out.exists():
        for old in sorted(out.rglob("*.json"), reverse=True):
            old.unlink()
    out.mkdir(parents=True, exist_ok=True)

    # --- tokens + users -------------------------------------------------
    tokens: dict[str, str] = {}
    users: dict[str, dict] = {}
    for role, email in ACCOUNTS.items():
        status, body = call(base, "/auth/login", method="POST",
                            payload={"email": email, "password": PASSWORD})
        if status != 200 or not isinstance(body, dict):
            print(f"Login failed for {email} (HTTP {status}). Is the DB seeded?")
            return 2
        tokens[role] = body["token"]
        users[email] = body["user"]
    # Static login is resolved client-side against this map.
    write(out, "auth/users.json", users)
    print(f"  logged in as {len(tokens)} roles")

    ds, tech, usr = tokens["data_scientist"], tokens["technician"], tokens["ev_user"]

    # --- config ---------------------------------------------------------
    capture(base, out, "/config/thresholds", "config/thresholds.json", None)

    # --- datasets (data scientist) --------------------------------------
    datasets = capture(base, out, "/datasets", "datasets.json", ds) or []
    for d in datasets:
        i = d["id"]
        capture(base, out, f"/datasets/{i}", f"datasets/{i}.json", ds)
        capture(base, out, f"/datasets/{i}/preview?limit=20", f"datasets/{i}/preview.json", ds)
        capture(base, out, f"/datasets/{i}/quality", f"datasets/{i}/quality.json", ds)

    # --- training runs + models -----------------------------------------
    runs = capture(base, out, "/training/runs", "training/runs.json", ds) or []
    for r in runs:
        capture(base, out, f"/training/runs/{r['id']}", f"training/runs/{r['id']}.json", ds)
    capture(base, out, "/models", "models.json", ds)
    capture(base, out, "/models/active", "models/active.json", ds)

    # --- vehicles + batteries (technician) ------------------------------
    vehicles = capture(base, out, "/vehicles", "vehicles.json", tech) or []
    for v in vehicles:
        code = v["vehicle_code"]
        serial = v.get("battery_serial")
        detail = capture(base, out, f"/vehicles/{code}", f"vehicles/{code.lower()}.json", tech)
        if detail is not None:
            # lookup is keyed by either code or serial; serve both spellings
            write(out, f"batteries/lookup/{code.lower()}.json", detail)
            if serial:
                write(out, f"batteries/lookup/{serial.lower()}.json", detail)
        if serial:
            capture(base, out, f"/batteries/{serial}/measurements",
                    f"batteries/{serial.lower()}/measurements.json", tech)

    # --- diagnostics -----------------------------------------------------
    capture(base, out, "/diagnostics?limit=200", "diagnostics.json", tech)
    capture(base, out, "/diagnostics/summary", "diagnostics/summary.json", tech)

    # --- EV user ---------------------------------------------------------
    capture(base, out, "/me/battery", "me/battery.json", usr)
    capture(base, out, "/me/battery/history", "me/battery/history.json", usr)
    capture(base, out, "/me/maintenance", "me/maintenance.json", usr)

    # --- notifications, per role ----------------------------------------
    for role, tok in (("data_scientist", ds), ("technician", tech), ("ev_user", usr)):
        capture(base, out, "/notifications", f"notifications/{role}.json", tok)

    manifest = {
        "generated_from": args.base_url,
        "mode": "static-demo",
        "note": ("Captured from the live API. Model metrics come from real "
                 "training runs. Mutating actions are disabled in this build."),
        "files": len(written),
    }
    write(out, "manifest.json", manifest)

    total = sum(f.stat().st_size for f in out.rglob("*.json"))
    print(f"\nWrote {len(written)} JSON files to {out} ({total/1024:.0f} KB)")
    if failed:
        print(f"{len(failed)} endpoint(s) did not return 200:")
        for f in failed:
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
