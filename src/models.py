"""
models.py - the regression engine: design matrix, OLS with Driscoll-Kraay standard errors, lags, linear combinations.

Unit of analysis: station-day. Outcome: daily PM2.5 (µg/m³), so effects add up to contributions.
design() builds: fire terms + wind-sector FE (8 x 45 deg, 50 m wind) + temperature + humidity + log(1+rain)
+ wind speed 10 m and 50 m + time controls + weekday FE + station FE + Diwali/Dussehra (day, next day) + COVID lockdown.
Time controls: with time_fe="%Y-%W" (the primary design) one fixed effect per calendar week of each year; without it,
annual Fourier terms (K=3) + year FE (the pre-specified design, kept in the specification ladder).
GRAP days are NOT controlled for: GRAP is triggered by high PM2.5 and would block part of the fire effect.
Standard errors: Driscoll-Kraay, scores summed per calendar day, Bartlett 14 days.
The fire model itself (per-period effects, attribution, permutation test) is in fire_model.py.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

LAGS = (0, 1, 2)


def p_normal(z):
    """Two-sided p-value of a standard-normal z statistic."""
    return math.erfc(abs(z) / math.sqrt(2))


FOURIER_K = 3
START = pd.Timestamp("2018-01-01")


def ols_dk_cov(X, y, day, L=14):
    if np.linalg.matrix_rank(X) < X.shape[1]:
        raise np.linalg.LinAlgError("rank-deficient design")
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    nd = int(day.max()) + 1
    S0 = np.zeros((nd, X.shape[1]))
    np.add.at(S0, day, X * e[:, None])
    S = S0.T @ S0
    for k in range(1, min(L, nd - 1) + 1):
        G = S0[k:].T @ S0[:-k]
        S += (1 - k / (L + 1)) * (G + G.T)
    bread = np.linalg.inv(X.T @ X)
    return b, bread @ S @ bread, e


def add_lags(panel, cols, lags=LAGS, leads=()):
    """Lags/leads are taken on the calendar (date) axis of the daily fire series, then merged."""
    daily = panel.drop_duplicates("date").set_index("date")[cols].sort_index()
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max(), freq="D"))
    out = {}
    for c in cols:
        for l in lags:
            out[f"{c}_L{l}"] = daily[c].shift(l)
        for l in leads:
            out[f"{c}_F{l}"] = daily[c].shift(-l)
    out = pd.DataFrame(out).rename_axis("date").reset_index()
    return panel.drop(columns=[c for c in out.columns if c in panel and c != "date"]).merge(out, on="date", how="left")


def design(p, fire_terms, outcome="pm25", wind_col="wd50", extra=None, station_interact=None, log=False, time_fe=None):
    x = p.dropna(subset=[outcome] + fire_terms + ["t2m", "rh", "rain", "ws10", "ws50", wind_col]).copy()
    X = pd.DataFrame({"const": 1.0}, index=x.index)
    for c in fire_terms:
        X[c] = x[c]
    if station_interact:
        for st in sorted(x.station.unique()):
            for c in station_interact:
                X[f"{c}:{st}"] = x[c] * (x.station == st)
        X = X.drop(columns=station_interact)
    sec = (x[wind_col] // 45).astype(int) % 8
    for s in range(1, 8):
        X[f"sector_{s}"] = (sec == s).astype(float)
    X["t2m"], X["rh"], X["lrain"], X["ws10"], X["ws50"] = x.t2m, x.rh, np.log1p(x.rain), x.ws10, x.ws50
    if time_fe:  # calendar-period fixed effects (e.g. "%Y-%W" = each week of each year) replace Fourier + year FE
        k = x.date.dt.strftime(time_fe)
        for v in sorted(k.unique())[1:]:
            X[f"t_{v}"] = (k == v).astype(float)
    else:
        doy = x.date.dt.dayofyear.to_numpy(float)
        for k in range(1, FOURIER_K + 1):
            X[f"sin{k}"], X[f"cos{k}"] = np.sin(2 * np.pi * k * doy / 365.25), np.cos(2 * np.pi * k * doy / 365.25)
        for yv in sorted(x.date.dt.year.unique())[1:]:
            X[f"y{yv}"] = (x.date.dt.year == yv).astype(float)
    for k in range(1, 7):
        X[f"wd_{k}"] = (x.date.dt.dayofweek == k).astype(float)
    for st in sorted(x.station.unique())[1:]:
        X[f"st_{st}"] = (x.station == st).astype(float)
    for c in ("diwali0", "diwali1", "dussehra0", "dussehra1", "covid"):
        if c == "covid" and time_fe:  # the lockdown spans whole weeks: absorbed by the week fixed effects
            continue
        if x[c].any():
            X[c] = x[c].astype(float)
    if extra:
        for c in extra:
            X[c] = x[c]
    X = X[[c for c in X.columns if c == "const" or X[c].std() > 0]]
    y = x[outcome].to_numpy(float)
    if log:
        y = np.log1p(y)
    day = (x.date - START).dt.days.to_numpy()
    return X, y, day, x


def fit(p, fire_terms, **kw):
    X, y, day, x = design(p, fire_terms, **kw)
    b, V, _ = ols_dk_cov(X.to_numpy(float), y, day)
    return pd.Series(b, index=X.columns), pd.DataFrame(V, index=X.columns, columns=X.columns), x


def lincomb(b, V, w: dict):
    names = list(w)
    a = np.array([w[n] for n in names])
    est = float(a @ b[names].to_numpy())
    se = float(math.sqrt(max(a @ V.loc[names, names].to_numpy() @ a, 0)))
    return {
        "estimate": est,
        "se": se,
        "ci_low": est - 1.96 * se,
        "ci_high": est + 1.96 * se,
        "p_value": p_normal(est / se) if se > 0 else np.nan,
    }


def cum(b, V, prefix, lags=LAGS):
    return lincomb(b, V, {f"{prefix}_L{l}": 1.0 for l in lags})
