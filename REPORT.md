# What drives Delhi's winter smog, and would acting a month earlier help?

*Four CPCB monitors in Delhi (Anand Vihar, Ashok Vihar, Aya Nagar, Bawana), 2018–2025 · NASA FIRMS VIIRS fire detections (8 paddy seasons) · NASA POWER weather. Every number comes from `python run_all.py` and is traceable to a CSV in `reports/tables/`.*

## Headline

1. **Punjab–Haryana crop fires cause about 15% of Delhi's October–November PM2.5** (95% CI 7–22%), about 26 µg/m³ of a 180 µg/m³ season mean, over 8 seasons (2018–2025).
   - Upwind fires raise PM2.5; the same fires downwind do not. The placebo share is −0.2% (CI −2.1 to 1.7%).
   - Shuffling the wind within each week reproduces a share this large in only 2% of 1,000 runs (permutation p = 0.020).
2. **Fire counts fell, the smoke did not.** Satellite detections in October–November fell ~90% from 2021 (96,664) to 2025 (10,033), yet the smoke's share stayed at 14.5% (2018–23) and 15.3% (2024–25).
   - One detection now stands for about 8× more PM2.5: 241 vs 32 µg/m³ per 1,000 weighted detections (difference p = 0.014).
   - Detections also changed character in 2024–25: the night share rose from 0.3–0.9% to ~4%, and median fire radiative power fell from 4.5–5.1 to 3.8 MW. This is consistent with burning moving away from the satellite's early-afternoon pass.
   - A model that assumes one effect for all years would put the 2024–25 share at 2%, a large undercount.
3. **Diwali is a sharp, short spike.** The night (20:00–02:00) runs at 2.3× an ordinary night, and was higher in all 8 years (sign test p = 0.008).
   - Its peak hour reached 7.0× normal (2025).
   - It accounts for about 10% of PM2.5 in the week starting on Diwali, 3.4% of its month, and 0.5–1.7% of the season.
   - **Dussehra** has no measurable effect.
4. **Weather moves PM2.5 by 53 µg/m³ within a single week** (a stagnant day vs a ventilated one), about 30% of the season mean.
5. **Enforcing GRAP from 1 September, a month before crop burning, would lower Sep–Jan PM2.5 by at most 3.4–3.7%**, using Study 1's best case. At Study 1's estimate GRAP has no detectable effect, so the expected gain is ~0.
   - Real October cuts do more:
     - Delhi's own emissions −30% → October PM2.5 −10.8% (7.8–15.0%), an assumption-based bound.
     - October crop fires halved → −6.5% (3.6–9.5%), measured.

## RQ1 — what contributes, and by how much

### Design

- **Fire index.** Each fire detection is weighted by how directly that day's 50 m wind blows from it towards Delhi:
  - FireUp = Σ max(0, cos(wind − bearing)) / 1,000.
  - FireDown, the placebo, is the same with −cos.
- **Regression.** Station-day PM2.5 in October–November 2018–2025 (1,822 station-days, 485 days) is regressed on FireUp and FireDown at lags 0–2, with controls:
  - one fixed effect per calendar week of each year;
  - 8 wind sectors;
  - temperature, humidity, rain and wind speed;
  - weekday, station, and Diwali/Dussehra days.
- **Standard errors.** Driscoll–Kraay, 14-day Bartlett.
- **Per-period effects.** The fire effect is estimated separately for 2018–2023 and 2024–2025, because one detection does not stand for the same amount of burning in both eras (Headline 2).
- **Attribution.** Fire PM2.5 = Σ effect × FireUp. Share = mean fire PM2.5 / mean PM2.5. The CI uses the delta method.

### Effects (`10_primary_effects.csv`, `fig2_effects.png`)

| Period | Upwind, 3-day effect per 1,000 | Downwind (placebo) |
|---|---|---|
| 2018–2023 | **+31.6** [11.4, 51.7], p = 0.002 | −0.9 [−27.3, 25.5], p = 0.95 |
| 2024–2025 | **+241.3** [74.4, 408.2], p = 0.005 | −16.6 [−178.6, 145.5], p = 0.84 |

The smoke arrives on the same day (lag 0: +24.5, p < 0.001 in 2018–23; +178.1, p = 0.017 in 2024–25) and is gone by day 2. A fourth lag adds nothing (2018–23: +9.3, p = 0.17).

### Contribution (`20_fire_contribution.csv`, `21_fire_contribution_by_year.csv`, `fig4_share_by_year.png`)

| Period | Mean PM2.5 | From crop fires | Share [95% CI] |
|---|---|---|---|
| **Oct–Nov 2018–2025** | 179.7 | 26.4 | **14.7%** [7.4, 22.0] |
| 2018–2023 | 174.7 | 25.3 | 14.5% [5.2, 23.8] |
| 2024–2025 | 194.6 | 29.7 | 15.3% [4.7, 25.8] |
| October | 123.0 | 16.1 | 13.1% [7.1, 19.0] |
| November | 237.6 | 37.0 | 15.6% [7.5, 23.7] |

- **By year:**

  | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|
  | 12.3% | 11.2% | 20.4% | 23.8% | 11.7% | 7.5% | 18.2% | 12.0% |

- **Typical day:** smoke is 8.5% of PM2.5 on the median day and 34% or more on the worst tenth of days. It was above 25% on 86 of 485 days.

### Checks (`11_specification_ladder.csv`, `12_checks.csv`, `fig3_checks.png`)

| Check | Fire share [95% CI] | Placebo share |
|---|---|---|
| Pre-specified: full year, one effect | 10.1% [7.5, 12.8] (2024–25 only 1.8%) | 1.0% |
| Oct–Nov, week FE, one effect | 11.6% [4.3, 18.8] (2024–25 only 2.1%) | 0.4% |
| **Primary: per-period effect** | **14.7% [7.4, 22.0]** | **−0.2%** |
| Three detection periods | 14.9% [7.9, 22.0] | 0.1% |
| A separate effect for every year | 16.1% [11.9, 20.3] | −1.7% |
| Four lags | 17.5% [8.0, 26.9] | 0.0% |
| Future fires added | 14.8% [7.9, 21.6] | 0.0% |
| Total fires held fixed (only wind alignment varies) | 14.6% [1.7, 27.4] | — |
| 10 m wind | 14.9% | −0.1% |
| Narrow wind cone (cos⁴) | 12.3% | −0.6% |
| High/nominal-confidence fires | 14.7% | −0.2% |
| Wider window, 15 Sep–15 Dec | 14.7% | −0.2% |
| NOAA-20 satellite (2024–25) | 13.1% [7.7, 18.5] vs S-NPP 17.8% | −4.4% |
| Delhi monitors' wind sensors* | 1.0% | 6.9% |

*The monitors' wind sensors differ from NASA wind by a median 95°, with only 20% of days within 45°, so they cannot locate upwind fires.

**Other tests:**

- **Permutation test** (`19_permutation_null.csv`, `fig7_permutation.png`): the wind is shuffled within each week 1,000 times and the alignment-only model is refitted each time. The shuffled shares average 4.1%, and only 2% of runs reach the real 14.6% (p = 0.020).
- **Event study** (`18_fire_spike_event_study.csv`, `fig5_event_study.png`): the top 10% of upwind-fire days in each year (56 days) are compared with the top 10% of downwind-fire days.
  - Around heavy upwind days, PM2.5 is +44 µg/m³ above its 21-day mean on the day (CI 21–68) and +42 on the next day.
  - Around heavy downwind days, it is −13 and −28.
- **Dose–response** (`17_dose_response.csv`, `fig6_dose.png`), within-year fifths of upwind exposure: the heaviest fifth adds +37.9 µg/m³ (CI 4.0–71.7, p = 0.028). The lower fifths are 1–10 µg/m³ and not significant, so the effect is concentrated on the heaviest smoke days.
- **By station:**

  | Anand Vihar | Ashok Vihar | Aya Nagar | Bawana |
  |---|---|---|---|
  | 14.0% | 10.4% | 20.9% | 13.4% |

  The share is positive and significant at every monitor.
- **Wheat season** (April–May): 4.6% [1.8, 7.3].

**What did not go cleanly:**

- **Future fires, 2024–25.** Fires 1–2 days ahead predict today's PM2.5 in 2024–25 (+105.7, p < 0.001) but not in 2018–23 (+10.7, p = 0.22). This fits the same timing shift: burning missed by today's pass is detected tomorrow. Adding future fires leaves the share at 14.8%.
- **Carbon monoxide** does not rise with upwind fires (2018–23: +0.06 mg/m³, p = 0.11). Delhi's CO is dominated by traffic.
- **Permutation null.** The permutation null is centred at 4%, not 0. Part of the shuffled index still tracks the weekly fire total, which is why the alignment-only share is the test statistic.

### Festivals (`src/diwali.py`; `41_`, `42_`, `43_festival_*.csv`; `fig8_festivals.png`)

| | Diwali | Dussehra |
|---|---|---|
| Night 20:00–02:00 vs ordinary nights | 500 vs 222 µg/m³ (2.3×) | 140 vs 118 (1.2×) |
| Nights above baseline (sign test) | 8 of 8 (p = 0.008) | 6 of 8 (p = 0.29) |
| Peak hour, 22:00–03:00 | up to 7.0× (2025) | up to 1.8× |
| Share of PM2.5, Diwali + next day | 26% [1, 52] | 1% |
| Share of the week starting on the festival | 10.2% [0.6, 19.9] | 1.2% |
| Share of the month it falls in | 3.4% [0.3, 6.6] | 0.6% |
| Share of the Oct–Nov season | 1.7% (vs ordinary days) / 0.5% (regression, weather-controlled) | ~0% |
| Regression, 2 days (week FE, weather-controlled) | +53.7 µg/m³ [−32.9, 140.3], p = 0.22 | −6.8 [−36.9, 23.4], p = 0.66 |

- **Wind.** In the five years with wind below 2.5 m/s on Diwali (2018–21, 2025), Diwali was 5.7% of its month and 17% of its week (at least 7.9%). In the three windier years (2022–24), it was about 0%. Spearman ρ between wind and month share = −0.74.
- **Persistence.** The excess is +190 µg/m³ from 18:00–24:00, +260 from 00:00–06:00 and +97 from 06:00–12:00, then +26 by the afternoon.

### Weather (`30_`, `31_weather_*.csv`)

Within the same week, the combined weather component (wind sector, speed, humidity, temperature, rain) moves PM2.5 by 53.1 µg/m³ from the 10th to the 90th percentile. That is 29.5% of the October–November mean. No single variable is significant on its own.

### October–November composition (`32_oct_nov_composition.csv`, `fig9_composition.png`)

| Source | Share | Basis |
|---|---|---|
| Crop fires | 14.7% (7.4–22.0) | measured |
| Diwali + Dussehra | 0.4% | measured (regression) |
| Delhi's own emissions | 36% (26–50%) | outside estimate, TERI–ARAI 2018 |
| NCR, regional, secondary aerosol | ~49% | remainder |

## RQ2 — acting about a month earlier (`src/counterfactuals.py`)

| Lever | Effect | Basis |
|---|---|---|
| GRAP Stage III from 1 Sep (75 / 72 days earlier) | best case −3.4% (2024–25), −3.7% (2025–26) of Sep–Jan PM2.5; no detectable effect at Study 1's estimate; worst case +9–10% | Study 1 effect, full CI carried through |
| GRAP Stage III from 1 Oct | best case −2.9% / −3.1% | as above |
| Delhi's own emissions −10 / −20 / −30 / −50% from 1 Oct | October PM2.5 −3.6 / −7.2 / −10.8 / −18.0% (range 26–50% share) | TERI–ARAI share, assumption-based |
| October crop fires −25 / −50 / −100% | October PM2.5 −3.3 / −6.5 / −13.1% (CI for −50%: 3.6–9.5%) | measured October fire share |

Only 10 of 106 severe days (>250 µg/m³) in October–November 2018–2025 came before 1 November. October still averages 1.3–2.5× the 24-hour standard every year.

## Limitations

- **Per-period effects.** The per-period effect was adopted after seeing that one effect for all years fits badly (Headline 2). The specification ladder reports every version.
- **Delhi's own share** comes from TERI–ARAI and is not estimated here.
- **Linearity.** Contributions assume the fire effect is linear within each period. Daily shares on extreme days are extrapolations; period averages are the reliable quantities.
- **Second satellite.** The NOAA-20 check covers 2024–25 only, because its archive file covers only those years.

## Data

| Source | Coverage | Size |
|---|---|---|
| CPCB CAAQMS hourly | 4 stations, 2018–2025, 31 files | 280,512 hourly rows; 10,571 valid station-days (≥18 h) |
| NASA FIRMS VIIRS S-NPP | 2018–2025, Punjab–Haryana box (27.6–32.6°N, 73.8–77.6°E), type 0, >40 km from Delhi | 742,861 detections |
| NASA FIRMS VIIRS NOAA-20 | 2024–2025 | 115,271 detections |
| NASA POWER (MERRA-2) | 2018–2025, central Delhi | 2,922 days |

**Integrity:** an automatic check stops the run if two stations match in more than 50% of hours. The largest match in the final data is 1.4%.
