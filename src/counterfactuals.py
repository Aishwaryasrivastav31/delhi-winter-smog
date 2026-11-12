"""
counterfactuals.py - RQ2: what acting about a month earlier could buy.

1. GRAP Stage III enforced from 1 September (a month before crop burning begins) or 1 October, instead of its actual
   first day. Study 1's effect is carried through with its full uncertainty: best case (lower 95% bound, -9.4%),
   point estimate (+11.7%) and worst case (upper bound, +25.5%), all on the 1+PM2.5 scale.
2. Delhi's own emissions cut from 1 October, using the TERI-ARAI winter share (26%, 36%, 50%): an assumption-based bound.
3. Fewer October crop fires: the measured October fire share, scaled linearly.
4. Descriptive: severe days (>250 µg/m³) before 1 November and before the first Stage III day.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd


def grap_earlier(net, pol, study1):
    rows = []
    for _, r in pol[pol.policy.str.startswith("GRAP")].iterrows():
        y = r.date.year
        season = net.loc[f"{y}-09-01" : f"{y + 1}-01-31"]
        for start in (pd.Timestamp(f"{y}-09-01"), pd.Timestamp(f"{y}-10-01")):
            w = net.loc[start : r.date - pd.Timedelta(days=1)]
            row = {
                "season": f"{y}-{str(y + 1)[2:]}",
                "actual_stage_III": r.date.date(),
                "earlier_start": start.date(),
                "days_earlier": int((r.date - start).days),
                "window_mean_pm25": w.mean(),
            }
            for lab, ratio in study1.items():
                avoided = w - (ratio * (1 + w) - 1)  # positive = cleaner air
                row[f"{lab}_ug_per_day"] = avoided.mean()
                row[f"{lab}_pct_of_window"] = avoided.mean() / w.mean()
                row[f"{lab}_pct_of_sep_jan"] = avoided.sum() / season.sum()
            rows.append(row)
    return pd.DataFrame(rows)


def local_cut_curve(net, share):
    rows = []
    for y in range(2018, 2026):
        oct_ = net.loc[f"{y}-10-01" : f"{y}-10-31"]
        season = net.loc[f"{y}-10-01" : f"{y + 1}-01-31"]
        if oct_.count() < 20:
            continue
        for red in np.round(np.arange(0, 0.51, 0.05), 2):
            for lab, sh in (("low", share.low), ("central", share.central), ("high", share.high)):
                rows.append(
                    {
                        "year": y,
                        "emission_cut": red,
                        "delhi_share": lab,
                        "ug_reduction_october": red * sh * oct_.mean(),
                        "pct_reduction_october": red * sh,
                        "pct_of_oct_jan": red * sh * oct_.sum() / season.sum(),
                    }
                )
    return pd.DataFrame(rows)


def fire_cut(october_row):
    return pd.DataFrame(
        [
            {
                "fire_cut": k,
                "pct_lower_october": k * october_row["share"],
                "ci_low": k * october_row["share_ci_low"],
                "ci_high": k * october_row["share_ci_high"],
                "ug_lower_october": k * october_row["fire_contrib"],
            }
            for k in (0.25, 0.5, 0.75, 1.0)
        ]
    )


def severe_before(net, pol):
    rows = []
    for y in range(2018, 2026):
        on = net.loc[f"{y}-10-01" : f"{y}-11-30"]
        sev = on[on > 250]
        g3 = pol[(pol.policy.str.startswith("GRAP")) & (pol.year == y)]
        rows.append(
            {
                "year": y,
                "severe_days_oct_nov": len(sev),
                "severe_before_1_nov": int((sev.index < f"{y}-11-01").sum()),
                "severe_before_first_stage_III": int((sev.index < g3.date.iloc[0]).sum()) if len(g3) else np.nan,
                "mean_pm25_october": net.loc[f"{y}-10-01" : f"{y}-10-31"].mean(),
                "mean_pm25_november": net.loc[f"{y}-11-01" : f"{y}-11-30"].mean(),
            }
        )
    return pd.DataFrame(rows)


def run(net, pol, share, october_row, study1, tab_dir):
    g = grap_earlier(net, pol, study1)
    g.to_csv(os.path.join(tab_dir, "50_grap_earlier.csv"), index=False)
    c = local_cut_curve(net, share)
    c.to_csv(os.path.join(tab_dir, "51_october_local_cut_curve.csv"), index=False)
    f = fire_cut(october_row)
    f.to_csv(os.path.join(tab_dir, "52_october_fire_cut.csv"), index=False)
    s = severe_before(net, pol)
    s.to_csv(os.path.join(tab_dir, "53_severe_days_before_policy.csv"), index=False)
    return {"grap": g, "curve": c, "fire_cut": f, "before": s}
