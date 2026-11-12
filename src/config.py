"""config.py - paths, periods and fixed parameters used across the analysis."""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "reports")
TAB = os.path.join(OUT, "tables")
FIG = os.path.join(OUT, "figures")
EXT = os.path.join(ROOT, "data", "external")

PADDY = (10, 11)  # RQ1 season: paddy-residue burning, October-November
WEEK = "%Y-%W"  # primary time control: one fixed effect per calendar week of each year

# Detection periods. Satellite fire counts fell ~90% between 2021 and 2025 while Delhi PM2.5 did not, and in
# 2024-25 the detections changed character (night share ~0.5% -> ~4%, median FRP 4.8 -> 3.8 MW), consistent with
# burning shifted away from the 13:30 overpass. One detection therefore does not stand for the same amount of
# burning in both eras, so the fire effect per detection is estimated separately for each period.
PERIODS = {"2018-2023": range(2018, 2024), "2024-2025": range(2024, 2026)}
PERIODS_3 = {"2018-2021": range(2018, 2022), "2022-2023": range(2022, 2024), "2024-2025": range(2024, 2026)}

GRAP_STUDY1 = {
    "best": 0.906,
    "point": 1.117,
    "worst": 1.255,
}  # Study 1 effect on the 1+PM2.5 scale: lower CI, point, upper CI
N_PERM = 1000
SEED = 20261105
