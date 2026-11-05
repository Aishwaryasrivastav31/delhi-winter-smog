"""
diwali.py - RQ1b: every festival test in one place (Diwali and Dussehra, 2018-2025).

    python src/diwali.py          (run on its own; run_all.py also calls run())

1. Regression: festival day + next day inside the week-fixed-effects model (Oct-Nov 2018-2025), Wald z-test.
2. Hourly event study: network PM2.5 on the festival night vs the median of the same hours on ordinary days
   4-10 days before and after (the baseline). Windows: night 20:00-02:00, peak 22:00-03:00.
3. Sign test: in how many of the 8 years the festival night exceeded its baseline (exact binomial, two-sided).
4. Persistence: excess PM2.5 in 6-hour blocks from 18:00 on the festival day to 18:00 two days later.
5. Shares: the festival's extra PM2.5 (day + next day, vs baseline) as a share of PM2.5 over the two days,
   the week starting on the festival, the calendar month and the Oct-Nov season.
6. Wind: festival wind speed (10 m, festival day + next day); share in calm (< 2.5 m/s) vs windy years, Spearman correlation.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import festivals  # noqa: E402
from models import fit, lincomb  # noqa: E402

BASE_DAYS = list(range(-10, -3)) + list(range(4, 11))
CALM_MS = 2.5  # 10 m wind (m/s) below which the festival nights are called calm (descriptive split)


def binom_two_sided(k, n):
    pk = [math.comb(n, i) / 2**n for i in range(n + 1)]
    obs = pk[k]
    return float(min(1.0, sum(p for p in pk if p <= obs + 1e-12)))


def hourly_profiles(hourly_net):
    """49-hour profile (00:00 festival day to 00:00 two days later) and its baseline for every festival."""
    rows = []
    for _, r in festivals().iterrows():
        t0 = r.date
        win = hourly_net.loc[t0 : t0 + pd.Timedelta(hours=48)]
        base = []
        for k in BASE_DAYS:
            bw = hourly_net.loc[t0 + pd.Timedelta(days=k) : t0 + pd.Timedelta(days=k, hours=48)]
            if len(bw) == 49:
                base.append(bw.to_numpy())
        if len(win) == 49 and base:
            b = np.nanmedian(np.vstack(base), axis=0)
            for h in range(49):
                rows.append(
                    {
                        "festival": r.festival,
                        "year": r.date.year,
                        "date": r.date,
                        "hour": h,
                        "pm25": win.iloc[h],
                        "baseline": b[h],
                    }
                )
    return pd.DataFrame(rows)


def run(panel, hourly_net, net, weather, tab_dir, week="%Y-%W"):
    out = {}
    prof = hourly_profiles(hourly_net)
    prof.drop(columns="date").to_csv(os.path.join(tab_dir, "40_festival_hourly_profiles.csv"), index=False)

    # 1. regression (Oct-Nov, 2018-2025, no fire terms so every year counts)
    pad = panel[panel.date.dt.month.isin((10, 11))]
    b, V, _ = fit(pad, [], time_fe=week)
    mean_on = net[net.index.month.isin((10, 11))].mean()
    reg = []
    for name in ("diwali", "dussehra"):
        r = lincomb(b, V, {f"{name}0": 1.0, f"{name}1": 1.0})
        reg.append(
            {
                "festival": name.capitalize(),
                "two_day_effect": r["estimate"],
                "ci_low": r["ci_low"],
                "ci_high": r["ci_high"],
                "p_value": r["p_value"],
                "share_of_oct_nov": r["estimate"] / (61 * mean_on),
                "share_ci_low": r["ci_low"] / (61 * mean_on),
                "share_ci_high": r["ci_high"] / (61 * mean_on),
            }
        )
    reg = pd.DataFrame(reg)
    reg.to_csv(os.path.join(tab_dir, "41_festival_regression.csv"), index=False)
    out["regression"] = reg

    # 2-6. event study per festival and year
    wd = weather.set_index("date")
    ev = []
    for (fest, yr), g in prof.groupby(["festival", "year"]):
        g = g.set_index("hour")
        day0 = pd.Timestamp(prof[(prof.festival == fest) & (prof.year == yr)].date.iloc[0])
        night = g.loc[20:26]  # 20:00 festival day to 02:00 next day
        peak = g.loc[22:27]  # 22:00 to 03:00
        two = g.loc[0:47]
        excess_two = float((two.pm25 - two.baseline).mean() * 2)  # µg/m³·day over the two calendar days
        wk = net.loc[day0 : day0 + pd.Timedelta(days=6)]
        mon = net.loc[f"{day0.year}-{day0.month:02d}"]
        season = net.loc[f"{day0.year}-10-01" : f"{day0.year}-11-30"]
        near = pd.concat(
            [wd.loc[day0 + pd.Timedelta(days=k)] for k in BASE_DAYS if day0 + pd.Timedelta(days=k) in wd.index], axis=1
        ).T
        blocks = {}
        for s, e, lab in (
            (18, 23, "18-24h"),
            (24, 29, "00-06h"),
            (30, 35, "06-12h"),
            (36, 41, "12-18h"),
            (42, 47, "18-24h next"),
        ):
            blk = g.loc[s:e]
            blocks[f"excess_{lab}"] = float((blk.pm25 - blk.baseline).mean())
        ev.append(
            {
                "festival": fest,
                "year": yr,
                "date": day0.date(),
                "night_pm25": night.pm25.mean(),
                "night_baseline": night.baseline.mean(),
                "night_excess": night.pm25.mean() - night.baseline.mean(),
                "night_ratio": night.pm25.mean() / night.baseline.mean(),
                "night_share": 1 - night.baseline.mean() / night.pm25.mean(),
                "peak_hour_ratio": float((peak.pm25 / peak.baseline).max()),
                "share_two_days": excess_two / float(two.pm25.mean() * 2),
                "share_week": excess_two / wk.sum(),
                "share_month": excess_two / mon.sum(),
                "share_season": excess_two / season.sum(),
                "wind_festival_ms": float(wd.loc[day0 : day0 + pd.Timedelta(days=1), "ws10"].mean()),
                "wind_nearby_ms": float(near.ws10.mean()),
                **blocks,
            }
        )
    ev = pd.DataFrame(ev)
    ev["calm"] = ev.wind_festival_ms < CALM_MS  # absolute wind speed on the festival day and the next day
    ev.to_csv(os.path.join(tab_dir, "42_festival_events.csv"), index=False)
    out["events"] = ev

    summ = []
    for fest, g in ev.groupby("festival"):
        n = len(g)
        k = int((g.night_excess > 0).sum())
        row = {
            "festival": fest,
            "years": n,
            "nights_above_baseline": k,
            "sign_test_p": binom_two_sided(k, n),
            "night_pm25": g.night_pm25.mean(),
            "night_baseline": g.night_baseline.mean(),
            "night_ratio_of_means": g.night_pm25.mean() / g.night_baseline.mean(),
            "night_share_mean": g.night_share.mean(),
            "peak_hour_ratio_max": g.peak_hour_ratio.max(),
            "peak_hour_ratio_max_year": int(g.loc[g.peak_hour_ratio.idxmax(), "year"]),
        }
        for col in ("share_two_days", "share_week", "share_month", "share_season"):
            v = g[col].to_numpy()
            se = v.std(ddof=1) / np.sqrt(n)
            t = 2.365 if n == 8 else 1.96
            row[col] = v.mean()
            row[col + "_ci_low"] = v.mean() - t * se
            row[col + "_ci_high"] = v.mean() + t * se
            row[col + "_years_positive"] = int((v > 0).sum())
        calm, windy = g[g.calm], g[~g.calm]
        row["spearman_wind_vs_month_share"] = float(g.wind_festival_ms.rank().corr(g.share_month.rank()))
        row.update(
            {
                "calm_years": ",".join(map(str, calm.year)),
                "windy_years": ",".join(map(str, windy.year)),
                "share_month_calm": calm.share_month.mean(),
                "share_month_windy": windy.share_month.mean(),
                "share_week_calm": calm.share_week.mean(),
                "share_week_windy": windy.share_week.mean(),
                "share_week_calm_min": calm.share_week.min() if len(calm) else np.nan,
            }
        )
        for c_ in [c for c in g.columns if c.startswith("excess_")]:
            row["mean_" + c_] = g[c_].mean()
        summ.append(row)
    summ = pd.DataFrame(summ)
    summ.to_csv(os.path.join(tab_dir, "43_festival_summary.csv"), index=False)
    out["summary"] = summ
    return out, prof


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import TAB  # noqa: E402
    from data import load_fires, load_hourly, load_weather  # noqa: E402
    from run_all import build_panel  # noqa: E402

    H, _, _ = load_hourly()
    w = load_weather()
    panel, _ = build_panel(H, w, load_fires())
    hourly_net = pd.concat({k: v["pm25"] for k, v in H.items()}, axis=1).mean(axis=1)
    os.makedirs(TAB, exist_ok=True)
    o, _ = run(panel, hourly_net, panel.groupby("date")["pm25"].mean(), w, TAB)
    pd.set_option("display.width", 200)
    print(o["regression"].round(3).to_string(index=False))
    print(o["summary"].T.to_string())
