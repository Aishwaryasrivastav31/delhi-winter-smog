"""
data.py - load and verify every input, and build the daily analysis table.

Air quality  CPCB CAAQMS hourly files (data/raw/cpcb_1hr/Raw_Data_<year>_site_<id>_<name>_1Hr.csv) for four Delhi
             stations, plus the 15-minute Anand Vihar export for 2024-25 (aggregated to hours: >=3 of 4 readings).
             Station identity comes from the site id in the file name; the 15-minute file also carries it in its rows.
             Integrity check: any two station series that are identical in >50% of shared hours are flagged and stop
             the run (the CPCB repository was found to serve one station's data under other station names).
Daily value  mean of hourly values when >=18 of 24 hours are valid. Negative values are masked.
Weather      NASA POWER daily point data for central Delhi (MERRA-2): T2M, RH2M, PRECTOTCORR, WS10M, WD10M, WS50M, WD50M.
Fires        NASA FIRMS VIIRS active-fire detections (any .csv or .csv.gz file in data/raw/firms), type 0 (vegetation fire) only,
             inside the Punjab-Haryana box, excluding detections within 40 km of central Delhi (urban heat sources).
"""

from __future__ import annotations

import glob
import itertools
import math
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
EXT = os.path.join(ROOT, "data", "external")
DELHI = (28.61, 77.21)
SITES = {"301": "Anand Vihar", "1420": "Ashok Vihar", "108": "Aya Nagar", "1560": "Bawana"}
COLS = {
    "PM2.5 (µg/m³)": "pm25",
    "PM10 (µg/m³)": "pm10",
    "CO (mg/m³)": "co",
    "NO2 (µg/m³)": "no2",
    "WS (m/s)": "ws",
    "WD (deg)": "wd",
}


class DataError(Exception):
    pass


# --------------------------------------------------------------------------------------------- air quality
def _hourly_from_1hr(path):
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d["Timestamp"], errors="coerce")
    d = d.dropna(subset=["ts"]).drop_duplicates("ts").set_index("ts")
    out = pd.DataFrame(index=d.index)
    for src, dst in COLS.items():
        out[dst] = pd.to_numeric(d[src], errors="coerce") if src in d else np.nan
    return out


def _hourly_from_15min(path):
    d = pd.read_csv(path, dtype=str)
    d["ts"] = pd.to_datetime(
        d["Timestamp"].str.replace(r"(Z|[+-]\d{2}:?\d{2})$", "", regex=True), format="ISO8601", errors="coerce"
    )
    d = d.dropna(subset=["ts"])
    ids = d["Station ID"].dropna().unique()
    if list(ids) != ["site_301"]:
        raise DataError(f"15-minute file station id {list(ids)} is not site_301")
    d = d.drop_duplicates("ts").set_index("ts")
    q = pd.DataFrame(index=d.index)
    for src, dst in COLS.items():
        q[dst] = pd.to_numeric(d[src], errors="coerce") if src in d else np.nan
    g = q.resample("h")
    return g.mean().where(g.count() >= 3)


def load_hourly():
    """Hourly series per station, 2018-2025, with an integrity audit."""
    parts, audit = {}, []
    for f in sorted(glob.glob(os.path.join(RAW, "cpcb_1hr", "Raw_Data_*_1Hr.csv"))):
        m = re.search(r"Raw_Data_(\d{4})_site_(\d+)_", os.path.basename(f))
        yr, site = m.groups()
        if site not in SITES:
            continue
        h = _hourly_from_1hr(f)
        parts.setdefault(SITES[site], []).append(h)
        audit.append(
            {
                "file": os.path.basename(f),
                "station": SITES[site],
                "year": int(yr),
                "hours": len(h),
                "pm25_coverage": round(h["pm25"].notna().mean(), 3),
            }
        )
    for f in glob.glob(os.path.join(RAW, "cpcb_15min", "*.csv")):
        h = _hourly_from_15min(f)
        parts.setdefault("Anand Vihar", []).append(h)
        audit.append(
            {
                "file": os.path.basename(f),
                "station": "Anand Vihar",
                "year": "2024-25 (15-min)",
                "hours": len(h),
                "pm25_coverage": round(h["pm25"].notna().mean(), 3),
            }
        )
    H = {}
    for st, ps in parts.items():
        x = pd.concat(ps).sort_index()
        H[st] = x[~x.index.duplicated(keep="last")]
    # integrity: no two stations may share (near-)identical PM2.5 series
    pairs = []
    for a, b in itertools.combinations(sorted(H), 2):
        j = pd.concat([H[a]["pm25"], H[b]["pm25"]], axis=1, keys=["a", "b"]).dropna()
        ident = float(((j.a - j.b).abs() < 0.5).mean()) if len(j) else np.nan
        pairs.append(
            {
                "station_a": a,
                "station_b": b,
                "shared_hours": len(j),
                "hourly_corr": round(j.a.corr(j.b), 3),
                "identical_share": round(ident, 3),
            }
        )
        if ident > 0.5:
            raise DataError(f"{a} and {b} are identical in {ident:.0%} of hours: a mislabelled file")
    return H, pd.DataFrame(audit), pd.DataFrame(pairs)


def daily_station(H, min_hours=18):
    rows = []
    for st, h in H.items():
        h = h.copy()
        for c in ("pm25", "pm10", "co", "no2"):
            h.loc[h[c] < 0, c] = np.nan
        g = h.resample("D")
        dm = g[["pm25", "pm10", "co", "no2"]].mean().where(g[["pm25", "pm10", "co", "no2"]].count() >= min_hours)
        r = np.deg2rad(h["wd"])
        s, c = np.sin(r).resample("D").mean(), np.cos(r).resample("D").mean()
        dm["wd_station"] = (np.rad2deg(np.arctan2(s, c)) % 360).where(h["wd"].resample("D").count() >= min_hours)
        dm["ws_station"] = h["ws"].resample("D").mean().where(h["ws"].resample("D").count() >= min_hours)
        dm["station"] = st
        rows.append(dm.rename_axis("date").reset_index())
    d = pd.concat(rows, ignore_index=True)
    return d[(d.date >= "2018-01-01") & (d.date <= "2025-12-31")]


# --------------------------------------------------------------------------------------------- weather
def load_weather():
    parts = []
    for f in sorted(glob.glob(os.path.join(RAW, "weather", "POWER*.csv"))):
        with open(f, encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
        k = next(i for i, l in enumerate(lines) if l.startswith("YEAR,"))
        w = pd.read_csv(f, skiprows=k)
        w["date"] = pd.to_datetime({"year": w.YEAR, "month": w.MO, "day": w.DY})
        parts.append(w.replace(-999, np.nan))
    w = pd.concat(parts).drop_duplicates("date").sort_values("date")
    return w.rename(
        columns={
            "T2M": "t2m",
            "RH2M": "rh",
            "PRECTOTCORR": "rain",
            "WS10M": "ws10",
            "WD10M": "wd10",
            "WS50M": "ws50",
            "WD50M": "wd50",
        }
    )[["date", "t2m", "rh", "rain", "ws10", "wd10", "ws50", "wd50"]]


# --------------------------------------------------------------------------------------------- fires
def bearing_from_delhi(lat, lon):
    """Bearing (degrees clockwise from north) from central Delhi to a point, flat-earth approximation."""
    dy = np.asarray(lat) - DELHI[0]
    dx = (np.asarray(lon) - DELHI[1]) * math.cos(math.radians(DELHI[0]))
    return np.rad2deg(np.arctan2(dx, dy)) % 360, np.hypot(dx, dy) * 111.0


def load_fires():
    """All FIRMS files, de-duplicated; returns detections with satellite, bearing and distance from Delhi."""
    parts = []
    files = sorted(glob.glob(os.path.join(RAW, "firms", "*.csv")) + glob.glob(os.path.join(RAW, "firms", "*.csv.gz")))
    for f in files:
        d = pd.read_csv(f)
        parts.append(d)
    if not parts:
        raise DataError("no FIRMS files in data/raw/firms")
    d = pd.concat(parts, ignore_index=True)
    d = d.drop_duplicates(["latitude", "longitude", "acq_date", "acq_time", "satellite"])
    d = d[(d["type"] == 0) & d.latitude.between(27.6, 32.6) & d.longitude.between(73.8, 77.6)].copy()
    d["bearing"], d["dist_km"] = bearing_from_delhi(d.latitude, d.longitude)
    d = d[d.dist_km > 40].copy()
    d["date"] = pd.to_datetime(d["acq_date"])
    d["sat"] = (
        d["satellite"]
        .astype(str)
        .map({"N": "SNPP", "SNPP": "SNPP", "Suomi NPP": "SNPP", "N20": "NOAA20", "1": "NOAA20", "NOAA-20": "NOAA20"})
        .fillna(d["satellite"].astype(str))
    )
    return d


def fire_index(fires, wind_dir, sat="SNPP", power=1.0, low_conf=True):
    """Daily upwind and downwind fire indices (thousands of detections, weighted by wind alignment).

    wind_dir: Series indexed by date, meteorological direction the wind blows FROM (degrees).
    A fire at bearing b from Delhi is upwind when the wind comes from b: weight max(0, cos(wind - b))**power.
    Downwind weight max(0, -cos(wind - b))**power (fires the wind carries away from Delhi)."""
    f = fires[fires.sat == sat]
    if not low_conf:
        f = f[f.confidence.astype(str).str.lower() != "l"]
    w = wind_dir.reindex(f.date).to_numpy()
    c = np.cos(np.deg2rad(w - f.bearing.to_numpy()))
    up = np.clip(c, 0, None) ** power
    dn = np.clip(-c, 0, None) ** power
    out = pd.DataFrame({"date": f.date.to_numpy(), "up": up, "dn": dn, "n": 1.0})
    g = out.groupby("date").sum() / 1000.0
    return g.rename(columns={"up": "fire_up", "dn": "fire_dn", "n": "fire_all"})


def festivals():
    f = pd.read_csv(os.path.join(EXT, "festivals.csv"), parse_dates=["date"])
    return f
