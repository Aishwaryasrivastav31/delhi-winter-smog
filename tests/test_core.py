"""Unit tests for the parts the conclusions rest on: fire geometry, upwind/downwind weights, lags, linear combinations."""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from data import DELHI, bearing_from_delhi, fire_index  # noqa: E402
from models import add_lags, lincomb  # noqa: E402


def test_bearing_cardinal_points():
    b, d = bearing_from_delhi(
        [DELHI[0] + 1, DELHI[0], DELHI[0] - 1, DELHI[0]], [DELHI[1], DELHI[1] + 1, DELHI[1], DELHI[1] - 1]
    )
    assert np.allclose(b, [0, 90, 180, 270], atol=1e-6)
    assert abs(d[0] - 111) < 1 and abs(d[1] - 111 * np.cos(np.radians(DELHI[0]))) < 1


def _fires(bearing_points):
    lat = [DELHI[0] + 2 * np.cos(np.radians(t)) for t in bearing_points]
    lon = [DELHI[1] + 2 * np.sin(np.radians(t)) / np.cos(np.radians(DELHI[0])) for t in bearing_points]
    f = pd.DataFrame(
        {"latitude": lat, "longitude": lon, "date": pd.Timestamp("2024-11-01"), "sat": "SNPP", "confidence": "n"}
    )
    f["bearing"], f["dist_km"] = bearing_from_delhi(f.latitude, f.longitude)
    return f


def test_northwest_fire_is_upwind_on_a_northwest_wind():
    f = _fires([315])
    wind = pd.Series([315.0], index=[pd.Timestamp("2024-11-01")])  # wind blowing FROM the north-west
    g = fire_index(f, wind)
    assert np.isclose(g.fire_up.iloc[0], 0.001) and np.isclose(g.fire_dn.iloc[0], 0.0)


def test_same_fire_is_downwind_on_a_southeast_wind():
    f = _fires([315])
    wind = pd.Series([135.0], index=[pd.Timestamp("2024-11-01")])
    g = fire_index(f, wind)
    assert np.isclose(g.fire_up.iloc[0], 0.0) and np.isclose(g.fire_dn.iloc[0], 0.001)


def test_crosswind_fire_counts_for_neither_and_cone_narrows():
    f = _fires([315, 0])  # one exactly upwind, one 45 deg off
    wind = pd.Series([315.0], index=[pd.Timestamp("2024-11-01")])
    g1 = fire_index(f, wind, power=1.0)
    g4 = fire_index(f, wind, power=4.0)
    assert np.isclose(g1.fire_up.iloc[0] * 1000, 1 + np.cos(np.radians(45)))
    assert np.isclose(g4.fire_up.iloc[0] * 1000, 1 + np.cos(np.radians(45)) ** 4)
    f90 = _fires([45])
    assert np.isclose(fire_index(f90, wind).fire_up.iloc[0], 0.0, atol=1e-12)


def test_lags_follow_the_calendar_not_row_order():
    d = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-11-03", "2024-11-01", "2024-11-02"] * 2),
            "station": ["A"] * 3 + ["B"] * 3,
            "x": [3.0, 1.0, 2.0] * 2,
        }
    )
    out = add_lags(d, ["x"], lags=(0, 1), leads=(1,)).sort_values(["station", "date"])
    a = out[out.station == "A"]
    assert a.x_L1.tolist()[1:] == [1.0, 2.0] and np.isnan(a.x_L1.iloc[0])
    assert a.x_F1.tolist()[:2] == [2.0, 3.0]


def test_lincomb_matches_hand_calculation():
    b = pd.Series([2.0, 3.0], index=["a", "c"])
    V = pd.DataFrame([[1.0, 0.5], [0.5, 4.0]], index=["a", "c"], columns=["a", "c"])
    r = lincomb(b, V, {"a": 1.0, "c": 1.0})
    assert r["estimate"] == 5.0 and np.isclose(r["se"], np.sqrt(1 + 4 + 2 * 0.5))


def test_period_terms_split_the_effect_by_year():
    import fire_model as fm

    d = pd.DataFrame({"date": pd.to_datetime(["2020-10-01", "2025-10-01"]), "fire_up_L0": [2.0, 3.0]})
    q, _ = fm.add_period_terms(
        d, {"early": range(2018, 2024), "late": range(2024, 2026)}, bases=("fire_up",), lags=(0,)
    )
    assert q["fire_up_L0@early"].tolist() == [2.0, 0.0] and q["fire_up_L0@late"].tolist() == [0.0, 3.0]


def test_binomial_sign_test():
    import diwali

    assert abs(diwali.binom_two_sided(8, 8) - 2 / 256) < 1e-12
    assert diwali.binom_two_sided(4, 8) == 1.0


def test_grap_counterfactual_best_case_is_9_4_percent_of_window():
    import counterfactuals as cf

    idx = pd.date_range("2024-09-01", "2025-01-31")
    net = pd.Series(100.0, index=idx)
    pol = pd.DataFrame({"policy": ["GRAP Stage III"], "year": [2024], "date": [pd.Timestamp("2024-11-15")]})
    g = cf.grap_earlier(net, pol, {"best": 0.906})
    r = g.iloc[0]
    assert abs(r.best_ug_per_day - (100 - (0.906 * 101 - 1))) < 1e-9
