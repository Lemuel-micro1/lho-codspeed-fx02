"""Core routines for AIS-style vessel position logs.

Each log line is: mmsi,timestamp,lat,lon,sog
  mmsi       vessel identifier (9 digits)
  timestamp  seconds since the start of the log
  lat, lon   position in decimal degrees
  sog        speed over ground reported by the vessel, in knots

Production logs hold millions of lines, so parsing and the per-vessel
track computations run once per line or once per pair of fixes.
"""
import json
import math
import random
import urllib.request

EARTH_RADIUS_NM = 3440.065


def version():
    return "0.3.1"


def parse_line(line):
    mmsi, ts, lat, lon, sog = line.split(",")
    return int(mmsi), int(ts), float(lat), float(lon), float(sog)


def parse_log(text):
    return [parse_line(line) for line in text.splitlines()
            if line and not line.startswith("#")]


def load_log(path):
    with open(path, encoding="utf-8") as f:
        return parse_log(f.read())


def fetch_port_list(url):
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.load(resp)


def haversine_nm(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_NM * math.asin(math.sqrt(a))


def group_by_vessel(records):
    tracks = {}
    for rec in records:
        tracks.setdefault(rec[0], []).append(rec)
    for fixes in tracks.values():
        fixes.sort(key=lambda r: r[1])
    return tracks


def track_distance(records):
    totals = {}
    for mmsi, fixes in group_by_vessel(records).items():
        dist = 0.0
        for a, b in zip(fixes, fixes[1:]):
            dist += haversine_nm(a[2], a[3], b[2], b[3])
        totals[mmsi] = dist
    return totals


def speed_alerts(records, max_knots=30.0):
    alerts = []
    for mmsi, fixes in group_by_vessel(records).items():
        for a, b in zip(fixes, fixes[1:]):
            hours = (b[1] - a[1]) / 3600
            if hours > 0 and haversine_nm(a[2], a[3], b[2], b[3]) / hours > max_knots:
                alerts.append((mmsi, b[1]))
    return alerts


def synthetic_log(n_lines, n_vessels=50, seed=7):
    """Deterministic test log: the same arguments always give the same text."""
    rng = random.Random(seed)
    pos = {200000000 + v: (40.0 + rng.random(), 13.0 + rng.random())
           for v in range(n_vessels)}
    lines = []
    for i in range(n_lines):
        mmsi = 200000000 + i % n_vessels
        lat, lon = pos[mmsi]
        step = 0.5 if rng.random() < 0.01 else 0.002
        lat += rng.uniform(-step, step)
        lon += rng.uniform(-step, step)
        pos[mmsi] = (lat, lon)
        lines.append(f"{mmsi},{i * 6},{lat:.5f},{lon:.5f},{rng.uniform(0, 20):.1f}")
    return "\n".join(lines)