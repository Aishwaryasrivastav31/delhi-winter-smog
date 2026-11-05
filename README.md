# Delhi Winter Smog: Sources and Earlier Action

A causal statistical study of what drives Delhi's October-November PM2.5, and how much acting about a month earlier would help. It uses eight years of government air-quality data (2018-2025), 858,000 NASA satellite fire detections and daily weather.

Full write-up: [REPORT.md](REPORT.md). Interactive report: `reports/report.html` (open in a browser).

## Key findings

| Question | Answer |
|---|---|
| How much of Delhi's Oct-Nov PM2.5 comes from Punjab-Haryana crop fires? | **14.7%** (95% CI 7.4-22.0%), about 26 of 180 µg/m³. Causal: upwind fires raise PM2.5, the same fires downwind do not (placebo share -0.2%), and shuffling the wind 1,000 times reproduces the result in only 2% of runs (p = 0.020). |
| Did falling satellite fire counts mean less smoke? | No. Oct-Nov detections fell 90% from 2021 to 2025, but the smoke's share stayed at about 15%. One detection now corresponds to about 8x more PM2.5, consistent with burning moved away from the satellite's afternoon pass. |
| Diwali and Dussehra? | Diwali causes a severe but short spike: the night runs at 2.3x an ordinary night in all 8 years (sign test p = 0.008), up to 7x at the peak hour. It accounts for about 10% of the following week, 3.4% of its month and under 2% of the season. Dussehra has no measurable effect. |
| Weather? | Within a single week, a stagnant day has about 53 µg/m³ (30%) more PM2.5 than a ventilated one. |
| Would enforcing GRAP a month before crop burning help? | At most 3.4-3.7% lower Sep-Jan PM2.5 (best case from the GRAP evaluation, Study 1); no detectable effect at its central estimate. |
| What would help more? | Real October cuts: Delhi's own emissions -30% gives about -10.8% October PM2.5; halving October crop fires gives about -6.5%. |

## Method

**Identification.** Each satellite fire detection is weighted by how directly that day's wind blows from it towards Delhi:

```
FireUp_d   = sum over fires of max(0,  cos(wind_d - bearing_fire)) / 1000
FireDown_d = sum over fires of max(0, -cos(wind_d - bearing_fire)) / 1000   (placebo)
```

**Model.** Station-day PM2.5 in October-November 2018-2025 (1,822 station-days, 485 days) is regressed on FireUp and FireDown at lags 0-2, with these controls:

- one fixed effect per calendar week of each year, so every comparison is between days of the same week;
- wind sector;
- temperature, humidity, rain and wind speed;
- weekday, station and festival days.

**Inference.** Standard errors are Driscoll-Kraay (14-day Bartlett), robust to correlation across stations and over time.

**Detection eras.** Satellite detections changed character in 2024 (more night detections, lower fire power), so the effect per detection is estimated separately for 2018-2023 and 2024-2025. Every alternative is reported in `reports/tables/11_specification_ladder.csv`.

**Statistical tests.**

- Wald z-tests on cumulative effects
- downwind placebo
- future-fire placebo
- randomisation (permutation) test with wind shuffled within each week
- event study around fire spikes
- within-year dose-response
- station-by-station estimates
- second satellite (NOAA-20)
- exact binomial sign test for festivals
- delta-method confidence intervals for contributions

**Festivals.** The festival night (20:00-02:00) is compared with the same hours on ordinary days 4-10 days before and after. The study also reports persistence, and the share of the week, month and season.

**Earlier action.**

- **GRAP from 1 September:** the full confidence range from the GRAP evaluation is carried through.
- **October emission cuts:** Delhi's own share is taken from the TERI-ARAI (2018) source apportionment.
- **October fire cuts:** use the measured October fire share.

## Data

| Source | Coverage | Size |
|---|---|---|
| CPCB CAAQMS, hourly | Anand Vihar, Ashok Vihar, Aya Nagar, Bawana; 2018-2025 | 280,512 hourly rows, 31 files |
| CPCB / DPCC, 15-minute | Anand Vihar, 2024-2025 | 70,177 rows |
| NASA FIRMS VIIRS S-NPP | Punjab-Haryana box (27.6-32.6N, 73.8-77.6E), 2018-2025 | 742,861 vegetation-fire detections |
| NASA FIRMS VIIRS NOAA-20 | Same box, 2024-2025 | 115,271 detections |
| NASA POWER (MERRA-2) | Central Delhi, daily, 2018-2025 | 2,922 days |
| External | Festival dates, GRAP dates, TERI-ARAI share | `data/external/` |

**Data quality.** The CPCB repository was found to serve one station's readings under other station names. An integrity check now stops the run if any two stations are identical in more than 50% of shared hours; the largest match in the final data is 1.4%. A day is used only when at least 18 of its 24 hours are valid.

**Format.** FIRMS archives are stored as `.csv.gz` to keep the repository small. The loader reads them directly.

## Repository structure

```
run_all.py                 runs the whole analysis in order
src/
  config.py                paths, detection periods, GRAP range, permutation settings
  data.py                  loading, integrity check, fire index
  models.py                design matrix, OLS with Driscoll-Kraay standard errors, lags, linear combinations
  fire_model.py            per-period fire effects, attribution, permutation test, event study, dose-response
  diwali.py                all festival tests (can be run on its own)
  counterfactuals.py       GRAP earlier, October emission cuts, fire cuts, severe days before policy
  figures.py               the eleven figures
  report_html.py           builds reports/report.html
  report_charts.js, report_style.css   assets for the HTML report
tests/
  test_core.py             fire geometry, lags, periods, linear combinations, sign test, GRAP counterfactual
data/
  raw/cpcb_1hr/            CPCB hourly files (station = site id in the file name)
  raw/cpcb_15min/          Anand Vihar 15-minute file
  raw/firms/               NASA FIRMS VIIRS archives (.csv.gz)
  raw/weather/             NASA POWER daily files
  external/                festival dates, GRAP dates, source-share assumption
reports/
  tables/                  every number in the report, as CSV
  figures/                 fig1-fig11
  results.json, timeline.json
  report.html              interactive report
REPORT.md                  full write-up
```

## How to run

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
python run_all.py            # all tables, figures and results.json (about 40 seconds; --quick uses 100 permutations)
python src/diwali.py         # festival tests only
python src/report_html.py    # rebuild reports/report.html
python -m pytest             # 9 unit tests
```

## Limitations

- **Per-period fire effects** were adopted after a single-effect model was seen to undercount 2024-2025. All versions are reported.
- **Delhi's own emission share** is taken from TERI-ARAI (2018) and is not estimated here. The local-cut figures are scenarios under that share.
- **The NOAA-20 check covers 2024-2025 only.**
- **Linearity.** Contributions assume a linear effect within each detection period. Period averages are more reliable than shares on single extreme days.

## Related work

This is the second study in a series. The first, an episode-based evaluation of GRAP Stage III/IV in Delhi (2024-2025), found no statistically significant PM2.5 reduction (+11.7%, 95% CI -9.4% to +25.5%). Its confidence range is used here for the GRAP counterfactual.

## Data sources

- Central Pollution Control Board, CAAQMS Data Repository: https://airquality.cpcb.gov.in/ccr/
- NASA FIRMS, VIIRS 375 m active fire archive: https://firms.modaps.eosdis.nasa.gov/
- NASA POWER daily point data: https://power.larc.nasa.gov/
- TERI-ARAI (2018), Source Apportionment of PM2.5 and PM10 of Delhi NCR
- Manchanda et al., Chemical speciation and source apportionment of ambient PM2.5 in New Delhi before, during, and after the Diwali fireworks: https://arxiv.org/abs/2011.14402

## Author

Aishwarya Srivastava
