"""
fire_model.py - RQ1a: the causal contribution of Punjab-Haryana crop fires to Delhi PM2.5.

Primary model (station-day, October-November, 2018-2025):
  PM2.5_sd = sum_k sum_{l=0..2} b_lk FireUp_{d-l} 1[period k] + sum_k sum_l g_lk FireDown_{d-l} 1[period k]
             + wind sector + temperature + humidity + log(1+rain) + wind speed 10/50 m
             + week-of-year x year FE + weekday FE + station FE
FireUp/FireDown: thousands of VIIRS S-NPP detections weighted by how directly the day's wind blows from them
toward Delhi (up) or away from it (down, the placebo). The per-detection effect is allowed to differ by detection
period (config.PERIODS). Standard errors: Driscoll-Kraay, 14-day Bartlett.

Attribution: fire PM2.5 on day d = sum_k sum_l b_lk FireUp_{d-l,k}; share = mean(fire PM2.5) / mean(network PM2.5),
95% CI by the delta method on the full covariance of the b's.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from data import fire_index
from models import LAGS, design, fit, lincomb


def months(p, ms):
    return p[p.date.dt.month.isin(ms)]


def period_of(dates, periods):
    lab = pd.Series(np.nan, index=dates.index, dtype=object)
    for k, yrs in periods.items():
        lab[dates.dt.year.isin(list(yrs))] = k
    return lab


def add_period_terms(p, periods, bases=("fire_up", "fire_dn"), lags=LAGS, leads=()):
    """Interact each fire term with a period indicator. Returns the panel and the term names per base."""
    q = p.copy()
    lab = period_of(q.date, periods)
    names = {b: [] for b in bases}
    cols = {}
    for k in periods:
        m = (lab == k).astype(float)
        for b in bases:
            for l in lags:
                c = f"{b}_L{l}@{k}"
                cols[c] = q[f"{b}_L{l}"] * m
                names[b].append(c)
            for l in leads:
                c = f"{b}_F{l}@{k}"
                cols[c] = q[f"{b}_F{l}"] * m
                names.setdefault(b + "_lead", []).append(c)
    q = pd.concat([q, pd.DataFrame(cols, index=q.index)], axis=1)
    return q, names


def fit_periods(p, periods, bases=("fire_up", "fire_dn"), lags=LAGS, leads=(), **kw):
    q, names = add_period_terms(p, periods, bases, lags, leads)
    terms = [t for b in names for t in names[b]]
    b, V, x = fit(q, terms, **kw)
    return b, V, x, names


def period_effects(b, V, names, periods, lags=LAGS):
    rows = []
    for k in periods:
        for base, lab in (("fire_up", "upwind"), ("fire_dn", "downwind (placebo)")):
            if base not in names:
                continue
            r = lincomb(b, V, {f"{base}_L{l}@{k}": 1.0 for l in lags})
            rows.append({"period": k, "term": lab, **r})
        for l in lags:
            r = lincomb(b, V, {f"fire_up_L{l}@{k}": 1.0})
            rows.append({"period": k, "term": f"upwind lag {l}", **r})
    return pd.DataFrame(rows)


def attribution(b, V, x, net, terms):
    """Daily contribution of the given terms (sum of coef x value) and a function for period averages with CIs."""
    days = x.drop_duplicates("date").set_index("date").sort_index()
    U = days[terms]
    beta = b[terms].to_numpy()
    Vb = V.loc[terms, terms].to_numpy()
    c = pd.DataFrame({"fire_contrib": (U * beta).sum(axis=1), "pm25_network": net.reindex(U.index)}).dropna()
    U = U.loc[c.index]

    def avg(idx):
        g = c.loc[idx]
        a = U.loc[idx].mean().to_numpy()
        se = float(np.sqrt(max(a @ Vb @ a, 0)))
        m, pm = g.fire_contrib.mean(), g.pm25_network.mean()
        sh = g.fire_contrib / g.pm25_network
        return {
            "days": len(g),
            "pm25_mean": pm,
            "fire_contrib": m,
            "ci_low": m - 1.96 * se,
            "ci_high": m + 1.96 * se,
            "share": m / pm,
            "share_ci_low": (m - 1.96 * se) / pm,
            "share_ci_high": (m + 1.96 * se) / pm,
            "median_daily_share": float(sh.median()),
            "p90_daily_share": float(sh.quantile(0.9)),
            "days_share_over_25pct": int((sh > 0.25).sum()),
        }

    return c, avg


def overall_share(b, V, x, net, names):
    c, avg = attribution(b, V, x, net, names["fire_up"])
    res = {"up": avg(c.index)}
    if "fire_dn" in names:
        cd, avgd = attribution(b, V, x, net, names["fire_dn"])
        res["dn"] = avgd(cd.index)
    return res


def contribution_tables(b, V, x, net, names, periods, fires):
    c, avg = attribution(b, V, x, net, names["fire_up"])
    rows = [{"period": "Oct-Nov, 2018-2025", **avg(c.index)}]
    for k, yrs in periods.items():
        rows.append({"period": f"Oct-Nov, {k}", **avg(c.index[c.index.year.isin(list(yrs))])})
    rows.append({"period": "October, 2018-2025", **avg(c.index[c.index.month == 10])})
    rows.append({"period": "November, 2018-2025", **avg(c.index[c.index.month == 11])})
    summary = pd.DataFrame(rows)
    det = fires[(fires.sat == "SNPP") & fires.date.dt.month.isin((10, 11))].groupby(fires.date.dt.year).size()
    yr = []
    for y in sorted(c.index.year.unique()):
        idx = c.index[c.index.year == y]
        yr.append(
            {
                "year": int(y),
                "snpp_detections_oct_nov": int(det.get(y, 0)),
                **avg(idx),
                "october_share": avg(idx[idx.month == 10])["share"],
                "november_share": avg(idx[idx.month == 11])["share"],
            }
        )
    return summary, pd.DataFrame(yr), c, avg


# ------------------------------------------------------------------------------------------- permutation test
def permutation_test(panel, fires, weather, net, periods, n_perm, seed, ms=(10, 11), week="%Y-%W"):
    """Randomisation inference: shuffle the wind direction among days of the same week (same year), rebuild every
    fire's upwind/downwind weight, refit the primary model and recompute the fire share. The share under shuffled
    winds shows what the design would find if wind alignment did not matter."""
    rng = np.random.default_rng(seed)
    wd = weather.set_index("date")["wd50"]
    f = fires[fires.sat == "SNPP"]
    pad = months(panel, ms)
    dates = pd.DatetimeIndex(sorted(pad.date.unique()))
    lagdates = pd.date_range(dates.min() - pd.Timedelta(days=max(LAGS)), dates.max())
    # fixed part of the design (everything except fire terms) from the observed panel
    # statistic: fire share in the alignment-only model (upwind terms + total fire count held fixed). Shuffling the
    # wind leaves the total fire count untouched, so under the null the upwind terms carry no information.
    q, names = add_period_terms(pad, periods, bases=("fire_up", "fire_all"))
    terms = names["fire_up"] + names["fire_all"]
    X, y, _, x = design(q, terms, time_fe=week)
    X = X.copy()
    fire_cols = [c for c in X.columns if c in names["fire_up"]]
    base = X.drop(columns=fire_cols)
    lab = period_of(x.date, periods).to_numpy()
    obs_b = np.linalg.lstsq(X.to_numpy(float), y, rcond=None)[0]
    obs = _share_from_b(pd.Series(obs_b, index=X.columns), x, net, names["fire_up"])

    # per-fire data for the permutation dates
    need = pd.DatetimeIndex(sorted({d - pd.Timedelta(days=l) for d in dates for l in LAGS}))
    ff = f[f.date.isin(need)]
    fday = (ff.date - lagdates[0]).dt.days.to_numpy()
    fbear = np.deg2rad(ff.bearing.to_numpy())
    wk = pd.Series(lagdates.strftime(week), index=lagdates)
    groups = [np.flatnonzero(wk.to_numpy() == g) for g in wk.unique()]
    w0 = wd.reindex(lagdates).to_numpy()
    xi = (x.date - lagdates[0]).dt.days.to_numpy()
    null = []
    for _ in range(n_perm):
        w = w0.copy()
        for g in groups:
            w[g] = w0[rng.permutation(g)]
        cang = np.cos(np.deg2rad(w)[fday] - fbear)
        up = np.bincount(fday, np.clip(cang, 0, None), len(lagdates)) / 1000
        cols = {}
        for k in periods:
            m = (lab == k).astype(float)
            for l in LAGS:
                cols[f"fire_up_L{l}@{k}"] = up[xi - l] * m
        Xp = pd.concat([base, pd.DataFrame(cols, index=base.index)], axis=1)
        bp = np.linalg.lstsq(Xp.to_numpy(float), y, rcond=None)[0]
        xp = x[["date"]].copy()
        for c_, v in cols.items():
            xp[c_] = v
        null.append(_share_from_b(pd.Series(bp, index=Xp.columns), xp, net, names["fire_up"]))
    null = np.array(null)
    p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (len(null) + 1)
    return obs, null, p


def _share_from_b(b, x, net, terms):
    days = x.drop_duplicates("date").set_index("date")
    contrib = (days[terms] * b[terms].to_numpy()).sum(axis=1)
    pm = net.reindex(contrib.index)
    return float(contrib.mean() / pm.mean())


# ------------------------------------------------------------------------------------------- event study
def fire_spike_event_study(panel, net, ms=(10, 11), top=0.9, window=5, n_boot=2000, seed=1):
    """PM2.5 around the heaviest upwind-fire days (top 10% within each year) and, as a placebo, around the heaviest
    downwind-fire days. Outcome: network PM2.5 minus its centred 21-day mean (removes the seasonal build-up)."""
    rng = np.random.default_rng(seed)
    days = panel.drop_duplicates("date").set_index("date").sort_index()
    pm = net.reindex(pd.date_range(net.index.min(), net.index.max()))
    dev = pm - pm.rolling(21, center=True, min_periods=15).mean()
    rows = []
    for kind, col in (("upwind spike", "fire_up"), ("downwind spike (placebo)", "fire_dn")):
        d = days[days.index.month.isin(ms) & days[col].notna()]
        ev = []
        for _, g in d.groupby(d.index.year):
            thr = g[col].quantile(top)
            ev += list(g.index[g[col] >= thr]) if thr > 0 else []
        mat = np.array([[dev.get(e + pd.Timedelta(days=o), np.nan) for o in range(-window, window + 1)] for e in ev])
        for j, o in enumerate(range(-window, window + 1)):
            v = mat[:, j][~np.isnan(mat[:, j])]
            bs = [rng.choice(v, len(v)).mean() for _ in range(n_boot)] if len(v) else [np.nan]
            rows.append(
                {
                    "event": kind,
                    "offset": o,
                    "events": len(v),
                    "pm25_vs_21day_mean": v.mean() if len(v) else np.nan,
                    "ci_low": np.percentile(bs, 2.5),
                    "ci_high": np.percentile(bs, 97.5),
                }
            )
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------- dose-response
def dose_response(pad, periods, week="%Y-%W"):
    """Flexible dose-response: same-day upwind index in within-year quintiles (positive days), against days with no
    upwind fire; lags 1-2 and downwind terms kept period-specific. Within-year bins make doses comparable across
    detection periods."""
    q = pad.copy()
    d = q.drop_duplicates("date").set_index("date")["fire_up_L0"]
    binmap = pd.Series(0, index=d.index)
    for _, g in d.groupby(d.index.year):
        pos = g[g > 0]
        if len(pos) >= 10:
            binmap.loc[pos.index] = pd.qcut(pos.rank(method="first"), 5, labels=False).astype(int) + 1
    q["dose_bin"] = q.date.map(binmap)
    labs = [f"Q{i}" for i in range(1, 6)]
    for i, l in enumerate(labs, 1):
        q[l] = (q.dose_bin == i).astype(float)
    q2, names = add_period_terms(q, periods, lags=(1, 2))
    q2, n0 = add_period_terms(q2, periods, bases=("fire_dn",), lags=(0,))
    terms = names["fire_up"] + names["fire_dn"] + n0["fire_dn"] + labs
    b, V, x = fit(q2, terms, time_fe=week)
    out = []
    for l in labs:
        r = lincomb(b, V, {l: 1.0})
        out.append({"bin": l, "days": int(x[x[l] == 1].date.nunique()), **r})
    return pd.DataFrame(out)


def detection_character(fires, ms=(10, 11)):
    f = fires[(fires.sat == "SNPP") & fires.date.dt.month.isin(ms)]
    g = f.groupby(f.date.dt.year)
    return (
        pd.DataFrame(
            {
                "detections": g.size(),
                "night_share": g.daynight.apply(lambda s: (s == "N").mean()),
                "median_frp_mw": g.frp.median(),
                "low_confidence_share": g.confidence.apply(lambda s: (s.astype(str) == "l").mean()),
            }
        )
        .rename_axis("year")
        .reset_index()
    )


def index_for_variant(fires, weather, sat="SNPP", wind="wd50", power=1.0, low_conf=True, station_wind=None):
    wdir = station_wind if station_wind is not None else weather.set_index("date")[wind]
    return fire_index(fires, wdir.dropna(), sat=sat, power=power, low_conf=low_conf)
