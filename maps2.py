"""
Vendor Location Visualiser
--------------------------
• Just run `python maps.py` → prompts you to upload Excel file.
• If you cancel, it runs the demo on a sample coordinate.
"""

from __future__ import annotations
import pathlib
import webbrowser
import requests
from tempfile import TemporaryDirectory
from typing import Tuple, Optional
from datetime import datetime

from PIL import Image           # pip install pillow
import pandas as pd             # pip install pandas openpyxl

# GUI file dialog
import tkinter as tk
from tkinter import filedialog

# ── Configuration ────────────────────────────────────────────────
API_KEY = ""

LAT = 16.763853073120117
LNG = 77.14752197265625

STATIC_SIZE    = "640x400"
STATIC_ZOOM    = 17
STREET_SIZE    = "640x400"
STREET_HEADING = 0
STREET_PITCH   = 0

# ── API helpers ──────────────────────────────────────────────────
def _get_json(url: str, params: dict, timeout: int = 10) -> dict:
    r = requests.get(url, params=params, timeout=timeout)
    try:
        return r.json()
    except ValueError as e:
        raise RuntimeError(f"Non-JSON response ({r.status_code})") from e

def reverse_geocode(lat: float, lng: float) -> Tuple[str, str]:
    data = _get_json(
        "https://maps.googleapis.com/maps/api/geocode/json",
        {"latlng": f"{lat},{lng}", "key": API_KEY},
    )
    if data.get("status") != "OK" or not data.get("results"):
        raise RuntimeError(f"Reverse geocode failed: {data.get('status')}")
    top = data["results"][0]
    return top["formatted_address"], top["place_id"]

def place_details(place_id: str) -> dict:
    data = _get_json(
        "https://maps.googleapis.com/maps/api/place/details/json",
        {"place_id": place_id,
         "fields": "name,types,business_status,formatted_address",
         "key": API_KEY},
    )
    if data.get("status") != "OK":
        raise RuntimeError(f"Place details failed: {data.get('status')}")
    return data["result"]

# ── Download and generate files ─────────────────────────────────
def download_static_map(lat: float, lng: float, out: pathlib.Path) -> None:
    r = requests.get(
        "https://maps.googleapis.com/maps/api/staticmap",
        params={
            "center": f"{lat},{lng}",
            "zoom": STATIC_ZOOM,
            "size": STATIC_SIZE,
            "maptype": "roadmap",
            "markers": f"color:red|{lat},{lng}",
            "key": API_KEY,
        },
        timeout=10,
    )
    r.raise_for_status()
    out.write_bytes(r.content)

def download_street_view(lat: float, lng: float, out: pathlib.Path) -> bool:
    r = requests.get(
        "https://maps.googleapis.com/maps/api/streetview",
        params={
            "size": STREET_SIZE,
            "location": f"{lat},{lng}",
            "heading": STREET_HEADING,
            "pitch": STREET_PITCH,
            "key": API_KEY,
        },
        timeout=10,
    )
    if r.status_code in (200, 302) and r.content:
        out.write_bytes(r.content)
        return True
    return False

def create_360_html(lat: float, lng: float, out: pathlib.Path) -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<title>Street View 360</title>
<style>html,body,#pano{{height:100%;margin:0}}</style>
<script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}"></script>
<script>
function init(){{
  const pos={{lat:{lat},lng:{lng}}};
  new google.maps.StreetViewPanorama(
    document.getElementById('pano'),
    {{position:pos,pov:{{heading:0,pitch:0}},zoom:1}});
}}
window.onload=init;
</script></head><body><div id="pano"></div></body></html>
"""
    out.write_text(html, encoding="utf8")

# ── Excel batch runner ──────────────────────────────────────────
def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {c.lower(): c for c in df.columns}
    for want, options in {"lat": ["lat", "latitude"],
                          "lng": ["lng", "long", "longitude"]}.items():
        for opt in options:
            if opt in col_map:
                df = df.rename(columns={col_map[opt]: want})
                break
        else:
            raise ValueError(f"Missing column: {want}")
    return df[["lat", "lng"]]

def run_excel_batch(xl_path: str) -> None:
    df = _normalize_cols(pd.read_excel(xl_path))
    out_root = pathlib.Path(xl_path).with_suffix("").name + "_outputs"
    out_root = pathlib.Path(out_root).resolve()
    out_root.mkdir(exist_ok=True)

    rows = []
    for idx, (lat, lng) in df.iterrows():
        print(f"\n▶ {idx+1}/{len(df)} — {lat}, {lng}")
        try:
            address, place_id = reverse_geocode(lat, lng)
            details = place_details(place_id)
        except Exception as err:
            print("  ✖ lookup failed:", err)
            rows.append({"lat": lat, "lng": lng, "status": "error", "note": str(err)})
            continue

        stem = f"{idx+1:03d}_{lat}_{lng}"
        map_f   = out_root / f"{stem}_map.png"
        street_f = out_root / f"{stem}_street.jpg"
        html_f  = out_root / f"{stem}_street360.html"

        download_static_map(lat, lng, map_f)
        has_street = download_street_view(lat, lng, street_f)
        create_360_html(lat, lng, html_f)

        rows.append({
            "lat": lat, "lng": lng,
            "address": details.get("formatted_address", address),
            "place_name": details.get("name"),
            "business_status": details.get("business_status"),
            "types": "|".join(details.get("types", [])),
            "static_map": map_f.name,
            "street_img": street_f.name if has_street else "",
            "street360": html_f.name,
            "status": "ok"
        })

    pd.DataFrame(rows).to_csv(out_root / "summary.csv", index=False)
    print(f"\n✔ Done – outputs in {out_root}")

# ── Demo runner ────────────────────────────────────────────────
def run_demo(lat: float, lng: float) -> None:
    print(f"\n📍 Running single-point demo: {lat}, {lng}")
    address, place_id = reverse_geocode(lat, lng)
    details = place_details(place_id)

    with TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        m = tmpdir / "map.png"
        s = tmpdir / "street.jpg"
        h = tmpdir / "360.html"

        download_static_map(lat, lng, m)
        has_sv = download_street_view(lat, lng, s)
        create_360_html(lat, lng, h)

        Image.open(m).show("Static Map")
        if has_sv:
            Image.open(s).show("Street View")
        webbrowser.open_new_tab(h.as_uri())

        print("\n──────── Report ────────")
        print("Address         :", details.get("formatted_address", address))
        print("Place name      :", details.get("name"))
        print("Business status :", details.get("business_status"))
        print("Types           :", ", ".join(details.get("types", [])))
        input("\nPress Enter to close…")

# ── Entry point with file dialog ───────────────────────────────
if __name__ == "__main__":
    # Show file-open dialog immediately
    root = tk.Tk()
    root.withdraw()  # hide main window
    file_path = filedialog.askopenfilename(
        title="Select Excel file with coordinates",
        filetypes=[("Excel files", "*.xlsx *.xls")],
    )

    if file_path:
        run_excel_batch(file_path)
    else:
        print("No file selected. Running demo point instead.")
        run_demo(LAT, LNG)
