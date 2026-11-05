"""report_html.py - build the animated HTML report from the result tables.

python src/report_html.py          (after run_all.py)  ->  reports/report.html
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "reports", "tables")
HERE = os.path.dirname(os.path.abspath(__file__))


def r(x, k=1):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), k)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def tab(n):
    return pd.read_csv(os.path.join(T, n))


def load():
    R = json.loads(read_text(os.path.join(ROOT, "reports", "results.json")))
    D = {"tl": json.loads(read_text(os.path.join(ROOT, "reports", "timeline.json")))}
    daily = pd.read_csv(os.path.join(T, "22_fire_contribution_daily.csv"), parse_dates=[0], index_col=0)
    D["contrib"] = {
        str(y): [
            [d.strftime("%d %b"), r(row.pm25_network, 0), r(max(row.fire_contrib, 0), 0)] for d, row in g.iterrows()
        ]
        for y, g in daily.groupby(daily.index.year)
    }
    eff = tab("10_primary_effects.csv")
    D["eff"] = []
    for k in [p for p in eff.period.unique() if "minus" not in p]:
        u = eff[(eff.period == k) & (eff.term == "upwind")].iloc[0]
        d = eff[(eff.period == k) & (eff.term == "downwind (placebo)")].iloc[0]
        D["eff"].append(
            [k, r(u.estimate, 0), r(u.ci_low, 0), r(u.ci_high, 0), r(d.estimate, 0), r(d.ci_low, 0), r(d.ci_high, 0)]
        )
    lad, ck = tab("11_specification_ladder.csv"), tab("12_checks.csv")
    short = {
        "1. Pre-specified: full year, seasonal curve + year FE, one effect for all years": "1 · Full year, one effect (pre-specified)",
        "2. Oct-Nov, seasonal curve + year FE, one effect": "2 · Oct–Nov, seasonal curve, one effect",
        "3. Oct-Nov, week FE, one effect": "3 · Oct–Nov, week effects, one effect",
        "4. PRIMARY: Oct-Nov, week FE, effect per detection period": "4 · Week effects, effect per period (primary)",
        "Total fire count held fixed (only wind alignment varies)": "Total fires held fixed, only wind varies",
        "Delhi monitors' own wind sensors instead of NASA wind*": "Delhi monitors' wind sensors *",
        "Three detection periods (2018-21, 2022-23, 2024-25)": "Three detection periods",
        "Narrow wind cone (cos^4 weighting)": "Narrow wind cone (cos⁴)",
    }
    pct = lambda v: r(v * 100, 1) if pd.notna(v) else None  # noqa: E731
    D["forest"] = [
        [
            short.get(x.analysis, x.analysis),
            pct(x.fire_share),
            pct(x.fire_ci_low),
            pct(x.fire_ci_high),
            pct(x.placebo_share),
            pct(x.placebo_ci_low),
            pct(x.placebo_ci_high),
            "ladder",
        ]
        for x in lad.itertuples()
    ]
    D["forest"] += [
        [
            short.get(x.analysis, x.analysis),
            pct(x.fire_share),
            pct(x.fire_ci_low),
            pct(x.fire_ci_high),
            pct(x.placebo_share),
            pct(x.placebo_ci_low),
            pct(x.placebo_ci_high),
            "check",
        ]
        for x in ck.itertuples()
        if not x.analysis.startswith("PRIMARY")
    ]
    by = tab("21_fire_contribution_by_year.csv")
    D["byyear"] = [
        [
            int(x.year),
            int(x.snpp_detections_oct_nov),
            r(x.share * 100, 1),
            r(x.share_ci_low * 100, 1),
            r(x.share_ci_high * 100, 1),
        ]
        for x in by.itertuples()
    ]
    es = tab("18_fire_spike_event_study.csv")
    D["es"] = {
        k: [
            [int(x.offset), r(x.pm25_vs_21day_mean, 1), r(x.ci_low, 1), r(x.ci_high, 1)]
            for x in es[es.event.str.startswith(n)].itertuples()
        ]
        for k, n in (("up", "upwind"), ("dn", "downwind"))
    }
    dose = tab("17_dose_response.csv")
    D["dose"] = [
        [lab, r(x.estimate, 0), r(x.ci_low, 0), r(x.ci_high, 0), int(x.days)]
        for lab, x in zip(["lightest 20%", "2nd", "3rd", "4th", "heaviest 20%"], dose.itertuples(), strict=False)
    ]
    pr = tab("40_festival_hourly_profiles.csv")
    D["prof"] = {
        f: {
            "h": sorted(g.hour.unique().tolist()),
            "pm": [r(v, 0) for v in g.groupby("hour").pm25.mean()],
            "base": [r(v, 0) for v in g.groupby("hour").baseline.mean()],
            "years": {str(y): [r(v, 0) for v in gy.sort_values("hour").pm25] for y, gy in g.groupby("year")},
        }
        for f, g in pr.groupby("festival")
    }
    ev = tab("42_festival_events.csv")
    D["night"] = {
        f: [[int(x.year), r(x.night_excess, 0), r(x.night_ratio, 2)] for x in g.itertuples()]
        for f, g in ev.groupby("festival")
    }
    comp = tab("32_oct_nov_composition.csv")
    D["comp"] = [[x.component, r(x.share, 3), r(x.low, 3), r(x.high, 3), x.basis] for x in comp.itertuples()]
    g = tab("50_grap_earlier.csv")
    g = g[g.earlier_start.astype(str).str.endswith("09-01")]
    D["grap"] = [[x.season, r(x.best_pct_of_sep_jan * 100, 1)] for x in g.itertuples()]
    cv = (
        tab("51_october_local_cut_curve.csv")
        .groupby(["emission_cut", "delhi_share"])[["pct_reduction_october", "ug_reduction_october", "pct_of_oct_jan"]]
        .mean()
        .reset_index()
    )
    D["curve"] = {
        s: [
            [
                r(x.emission_cut * 100, 0),
                r(x.pct_reduction_october * 100, 2),
                r(x.ug_reduction_october, 1),
                r(x.pct_of_oct_jan * 100, 2),
            ]
            for x in gg.itertuples()
        ]
        for s, gg in cv.groupby("delhi_share")
    }
    fc = tab("52_october_fire_cut.csv")
    D["firecut"] = [
        [r(x.fire_cut * 100, 0), r(x.pct_lower_october * 100, 1), r(x.ci_low * 100, 1), r(x.ci_high * 100, 1)]
        for x in fc.itertuples()
    ]
    bf = tab("53_severe_days_before_policy.csv")
    D["before"] = [
        [
            int(x.year),
            r(x.mean_pm25_october, 0),
            r(x.mean_pm25_november, 0),
            int(x.severe_before_1_nov),
            int(x.severe_days_oct_nov),
        ]
        for x in bf.itertuples()
    ]
    return R, D


def build(standalone=False):
    R, D = load()
    css = read_text(os.path.join(HERE, "report_style.css"))
    js = read_text(os.path.join(HERE, "report_charts.js"))
    ct = tab("20_fire_contribution.csv").set_index("period")
    allp, a, b_ = ct.loc["Oct-Nov, 2018-2025"], ct.loc["Oct-Nov, 2018-2023"], ct.loc["Oct-Nov, 2024-2025"]
    eff = tab("10_primary_effects.csv")
    up = {k: eff[(eff.period == k) & (eff.term == "upwind")].iloc[0] for k in ("2018-2023", "2024-2025")}
    dn = {k: eff[(eff.period == k) & (eff.term == "downwind (placebo)")].iloc[0] for k in ("2018-2023", "2024-2025")}
    diff = eff[eff.term == "upwind, difference"].iloc[0]
    prim, perm, W = R["primary"], R["permutation"], R["weather"]
    det = tab("03_detection_character_oct_nov.csv").set_index("year")
    fs = tab("43_festival_summary.csv").set_index("festival")
    di, du = fs.loc["Diwali"], fs.loc["Dussehra"]
    reg = tab("41_festival_regression.csv").set_index("festival")
    lead = R["leads"]
    swd = R["station_wind_disagreement"]
    co = tab("14_co_tracer.csv")
    co_a = co[(co.period == "2018-2023") & (co.term == "upwind")].iloc[0]
    wheat = R["wheat"]
    g = tab("50_grap_earlier.csv")
    gs = g[g.earlier_start.astype(str).str.endswith("09-01")]
    bf = tab("53_severe_days_before_policy.csv")
    lad = tab("11_specification_ladder.csv")
    oct_ratio = bf.mean_pm25_october / 60
    fc50 = tab("52_october_fire_cut.csv").set_index("fire_cut").loc[0.5]
    p = lambda v, k=0: f"{v * 100:.{k}f}%"  # noqa: E731
    years = R["fire_years"]
    nsd = sum(R["station_days_pm25"].values())
    drop = 1 - det.loc[2025, "detections"] / det.loc[2021, "detections"]
    ratio = up["2024-2025"].estimate / up["2018-2023"].estimate
    year_buttons = "".join(
        f'<button type="button" data-y="{y}" aria-pressed="{str(i == 0).lower()}">{y}</button>'
        for i, y in enumerate(years[::-1])
    )

    body = f"""
<div id="progress" aria-hidden="true"></div>
<header class="hero">
  <canvas id="haze" aria-hidden="true"></canvas>
  <div class="wrap">
    <div>
      <p class="eyebrow">Research report · Delhi air, study 2</p>
      <h1>What drives Delhi's <em>winter smog</em>, and would acting a month earlier help?</h1>
      <p class="sub">A causal estimate of crop-fire smoke from wind direction over eight burning seasons, the real size of Diwali and Dussehra, and what an earlier start could realistically buy.</p>
      <dl class="meta">
        <dt>Author</dt><dd>Aishwarya Srivastava</dd>
        <dt>Outcome</dt><dd>Daily PM2.5 (µg/m³), 4 CPCB stations</dd>
        <dt>Fires</dt><dd>NASA FIRMS VIIRS, Punjab–Haryana</dd>
        <dt>Period</dt><dd>2018–2025 (8 paddy seasons)</dd>
      </dl>
    </div>
    <div class="headline grow" id="hero-fig">
      <span class="eyebrow">Crop-fire share of Oct–Nov PM2.5</span>
      <span class="big">{p(allp.share)}</span>
      <svg id="heroci" viewBox="0 0 380 70" role="img" aria-label="95 percent confidence interval {p(allp.share_ci_low)} to {p(allp.share_ci_high)}"></svg>
      <span class="verdict">Causal: upwind fires count, downwind fires do not</span>
      <span class="cap">95% CI {p(allp.share_ci_low)}–{p(allp.share_ci_high)} · ≈{allp.fire_contrib:.0f} of {allp.pm25_mean:.0f} µg/m³ · 2018–23: {p(a.share)}, 2024–25: {p(b_.share)} · permutation p = {perm["p_value"]:.2f}</span>
    </div>
  </div>
</header>

<div class="wrap layout">
  <nav class="toc" aria-label="Contents">
    <span class="eyebrow">Contents</span>
    <ol>
      <li><a href="#abstract">Abstract</a></li>
      <li><a href="#s1">1 · Questions</a></li>
      <li><a href="#s2">2 · Data</a></li>
      <li><a href="#s3">3 · Design</a></li>
      <li><a href="#s4">4 · Crop fires</a></li>
      <li><a href="#s5">5 · Fewer detections, same smoke</a></li>
      <li><a href="#s6">6 · Checks</a></li>
      <li><a href="#s7">7 · Festivals</a></li>
      <li><a href="#s8">8 · Weather and the whole season</a></li>
      <li><a href="#s9">9 · A month earlier?</a></li>
      <li><a href="#s10">10 · Conclusion</a></li>
    </ol>
  </nav>

  <article>
    <section id="abstract">
      <h2>Abstract</h2>
      <div class="prose reveal">
        <p>Every October and November, Delhi's air turns from bad to dangerous, and three suspects are named every year: crop-residue fires in Punjab and Haryana, festival fireworks and the weather. This study measures each over eight burning seasons (2018–2025), then asks whether acting about a month earlier would help.</p>
        <p>Fire smoke is identified from a natural experiment: on any day, the wind decides whether the same fires blow towards Delhi or away from it. Comparing days within the same week, <b>crop fires cause {p(allp.share, 1)} of Delhi's October–November PM2.5</b> (95% CI {p(allp.share_ci_low, 1)}–{p(allp.share_ci_high, 1)}), while the same fires downwind explain nothing ({p(prim["placebo_share"], 1)}). Shuffling the wind 1,000 times reproduces a share this large only {perm["p_value"] * 100:.0f}% of the time.</p>
        <p>Satellite fire detections fell {drop * 100:.0f}% between 2021 and 2025, yet the smoke's share did not: one detection now stands for about {ratio:.0f}× more PM2.5, consistent with burning moved away from the satellite's afternoon pass. Diwali night runs at {di.night_ratio_of_means:.1f}× an ordinary night in all 8 years, but adds about {p(di.share_week)} to its week and {p(di.share_month, 1)} to its month. Dussehra is not visible.</p>
        <p>Enforcing GRAP from 1 September would lower season PM2.5 by <b>at most {p(gs.best_pct_of_sep_jan.min(), 1)}–{p(gs.best_pct_of_sep_jan.max(), 1)}</b>, and by nothing at Study 1's estimate. Real October cuts do more: a 30% cut in Delhi's own emissions lowers October PM2.5 by about 11%, and halving October fires by about {p(fc50.pct_lower_october, 1)}.</p>
      </div>
      <div class="numbers reveal">
        <div><b data-count="{R["hourly_rows"]}">{R["hourly_rows"]:,}</b><span>hourly air-quality records, 4 stations</span></div>
        <div><b data-count="{R["snpp_detections"]}">{R["snpp_detections"]:,}</b><span>S-NPP fire detections, 2018–2025</span></div>
        <div><b data-count="{int(allp.days)}">{int(allp.days)}</b><span>Oct–Nov days in the fire design</span></div>
        <div><b data-count="1000">1,000</b><span>wind permutations</span></div>
      </div>
    </section>

    <section id="s1">
      <h2><span class="n">01</span>Questions</h2>
      <div class="cards reveal">
        <div class="card"><span class="badge no">RQ1</span><h3>What contributes to Delhi's PM2.5, and by how much?</h3><p class="muted">Punjab–Haryana crop fires (causal), Diwali and Dussehra, and the weather. Delhi's own share is taken from source apportionment, not estimated.</p></div>
        <div class="card"><span class="badge yes">RQ2</span><h3>If action started about a month earlier, how much lower would PM2.5 be?</h3><p class="muted">GRAP from 1 September (Study 1's full range), October cuts in Delhi's own emissions, and fewer October crop fires.</p></div>
      </div>
      <div class="figure reveal" id="tl-fig">
        <h3>The season, day by day</h3>
        <div class="toggle" role="group" aria-label="Year">{year_buttons}</div>
        <svg id="tl" viewBox="0 0 900 270" role="img" aria-label="Daily Delhi PM2.5 and the upwind fire index, mid-September to mid-December"></svg>
        <p class="cap">Line: 4-station mean PM2.5. Bars: upwind fire index, scaled within each year. Dashed: festivals. Solid: first GRAP Stage III day. Hover for values.</p>
      </div>
    </section>

    <section id="s2">
      <h2><span class="n">02</span>Data</h2>
      <div class="prose reveal">
        <ul>
          <li><b>Air quality</b>: CPCB CAAQMS hourly data, 2018–2025, Anand Vihar, Ashok Vihar, Aya Nagar and Bawana ({R["hourly_rows"]:,} hourly rows; {nsd:,} valid station-days, at least 18 of 24 hours).</li>
          <li><b>Fires</b>: NASA FIRMS VIIRS active fires, vegetation fires only, Punjab–Haryana, more than 40 km from Delhi: {R["snpp_detections"]:,} S-NPP detections (2018–2025) and {R["noaa20_detections"]:,} NOAA-20 detections (2024–2025, a check).</li>
          <li><b>Weather</b>: NASA POWER (MERRA-2) daily temperature, humidity, rain, and wind speed and direction at 10 m and 50 m.</li>
        </ul>
      </div>
      <div class="fix reveal"><b>Integrity check.</b> The CPCB repository served one station's data under other station names. The pipeline now stops if any two stations match in more than half of their hours; the largest match in the final data is {R["max_identical_share"] * 100:.1f}%.</div>
    </section>

    <section id="s3">
      <h2><span class="n">03</span>Design: let the wind decide</h2>
      <div class="prose reveal">
        <p>Each fire is weighted by how directly that day's wind blows from it towards Delhi. The same fires, weighted the opposite way, form a <b>downwind placebo</b>: if smoke is the cause, only the upwind version should matter.</p>
      </div>
      <div class="formula reveal">FireUp<sub>d</sub> = Σ<sub>fires</sub> max(0, cos(wind<sub>d</sub> − bearing<sub>fire</sub>)) / 1000</div>
      <div class="prose reveal">
        <p>Station-day PM2.5 (October–November, {int(allp.days)} days, 1,822 station-days) is regressed on upwind and downwind fires (same day, 1 and 2 days before) with <b>one fixed effect for each calendar week of each year</b>, 8 wind sectors, temperature, humidity, rain, wind speed, weekday, station, and Diwali and Dussehra days. Standard errors are Driscoll–Kraay. Because one satellite detection does not stand for the same burning in every year (section 5), the effect is estimated separately for 2018–2023 and 2024–2025.</p>
      </div>
      <ul class="chips reveal"><li>Week × year fixed effects</li><li>Driscoll–Kraay SE</li><li>Downwind placebo</li><li>Permutation test</li><li>Event study</li><li>Dose–response</li><li>2 satellites</li></ul>
    </section>

    <section id="s4">
      <h2><span class="n">04</span>Crop fires</h2>
      <div class="stats reveal">
        <div class="stat"><span class="eyebrow">Share of Oct–Nov PM2.5</span><b>{p(allp.share, 1)}</b><span class="muted">95% CI {p(allp.share_ci_low, 1)}–{p(allp.share_ci_high, 1)} · ≈{allp.fire_contrib:.0f} µg/m³</span></div>
        <div class="stat"><span class="eyebrow">Placebo (downwind)</span><b>{p(prim["placebo_share"], 1)}</b><span class="muted">CI {p(prim["placebo_ci_low"], 1)} to {p(prim["placebo_ci_high"], 1)} · no effect</span></div>
        <div class="stat"><span class="eyebrow">Permutation test</span><b>p = {perm["p_value"]:.2f}</b><span class="muted">shuffled winds average {p(perm["null_mean"], 1)} vs real {p(perm["observed_share"], 1)}</span></div>
      </div>
      <div class="figure reveal">
        <h3>Upwind fires raise PM2.5 in both eras; downwind fires do not</h3>
        <svg id="lags" viewBox="0 0 700 260" role="img" aria-label="Upwind and downwind fire effects by detection period"></svg>
        <p class="cap">3-day effect per 1,000 weighted detections, 95% CI. 2018–23: upwind +{up["2018-2023"].estimate:.1f} (p = {up["2018-2023"].p_value:.3f}), downwind {dn["2018-2023"].estimate:.1f}. 2024–25: upwind +{up["2024-2025"].estimate:.1f} (p = {up["2024-2025"].p_value:.3f}), downwind {dn["2024-2025"].estimate:.1f}. Smoke arrives the same day and is gone by day 2.</p>
      </div>
      <div class="figure reveal">
        <h3>Around the heaviest upwind-fire days PM2.5 rises; around the heaviest downwind-fire days it does not</h3>
        <svg id="es" viewBox="0 0 900 250" role="img" aria-label="Event study around fire spikes"></svg>
        <p class="cap">Top 10% of upwind-fire days in each year (56 days) vs top 10% of downwind-fire days. PM2.5 relative to its 21-day mean; band = 95% bootstrap CI.</p>
      </div>
      <div class="figure reveal" id="ct-fig">
        <h3>How much of each day was smoke</h3>
        <div class="toggle" role="group" aria-label="Year">{year_buttons}</div>
        <svg id="ct" viewBox="0 0 900 260" role="img" aria-label="Daily PM2.5 split into crop-fire smoke and everything else"></svg>
        <p class="cap" id="ctcap"></p>
      </div>
    </section>

    <section id="s5">
      <h2><span class="n">05</span>Fewer detections, the same smoke</h2>
      <div class="prose reveal">
        <p>October–November fire detections fell from {int(det.loc[2021, "detections"]):,} in 2021 to {int(det.loc[2025, "detections"]):,} in 2025, a {drop * 100:.0f}% drop. Delhi's PM2.5 did not fall, and neither did the smoke's share. What changed is what one detection means: the effect per 1,000 detections is <b>{up["2024-2025"].estimate:.0f}</b> in 2024–25 against <b>{up["2018-2023"].estimate:.0f}</b> in 2018–23 (difference p = {diff.p_value:.3f}).</p>
        <p>The detections themselves also changed: the night share rose from {det.loc[2018:2023, "night_share"].min() * 100:.1f}–{det.loc[2018:2023, "night_share"].max() * 100:.1f}% to about {det.loc[2024:2025, "night_share"].mean() * 100:.0f}%, and median fire power fell from {det.loc[2018:2023, "median_frp_mw"].min():.1f}–{det.loc[2018:2023, "median_frp_mw"].max():.1f} to {det.loc[2024:2025, "median_frp_mw"].mean():.1f} MW. That is consistent with burning moved away from the satellite's 13:30 pass. A model with one effect for all years would put the 2024–25 share at {p(lad.iloc[2]["share_2024-2025"], 0)}; that is an undercount.</p>
      </div>
      <div class="figure reveal">
        <h3>Detections fell ~{drop * 100:.0f}%; the smoke's share did not</h3>
        <svg id="byyear" viewBox="0 0 900 250" role="img" aria-label="Fire share by year with satellite detections"></svg>
        <p class="cap">Bars: crop-fire share of October–November PM2.5 with 95% CI. Line: S-NPP detections, October–November.</p>
      </div>
    </section>

    <section id="s6">
      <h2><span class="n">06</span>Checks</h2>
      <div class="figure reveal">
        <h3>How the design was reached, and every check</h3>
        <svg id="forest" viewBox="0 0 900 600" role="img" aria-label="Fire share and placebo share across specifications and checks"></svg>
        <p class="cap">● fire share, ■ placebo share from downwind fires, 95% CI. Rows 1–3 assume one effect for all years and miss the 2024–25 smoke. * Delhi monitors' wind sensors differ from NASA wind by a median {swd["median_abs_deg"]:.0f}° (only {swd["share_within_45"] * 100:.0f}% of days within 45°), so they cannot tell which fires are upwind.</p>
      </div>
      <div class="figure reveal">
        <h3>The heaviest smoke days carry the effect</h3>
        <svg id="dose" viewBox="0 0 700 250" role="img" aria-label="Dose-response by fifths of upwind exposure"></svg>
        <p class="cap">PM2.5 vs days with no upwind fire, by fifths of same-day upwind exposure within each year. Only the heaviest fifth is significant.</p>
      </div>
      <div class="prose reveal">
        <p><b>What did not go cleanly, and is reported as it came out.</b></p>
        <ul>
          <li><b>Future fires in 2024–25.</b> Fires 1–2 days ahead predict today's PM2.5 in 2024–25 (+{lead["2024-2025"]["estimate"]:.0f}, p &lt; 0.001) but not in 2018–23 (+{lead["2018-2023"]["estimate"]:.0f}, p = {lead["2018-2023"]["p_value"]:.2f}). This fits the same timing shift: burning missed by today's pass is detected tomorrow. The share stays at {p(tab("12_checks.csv").set_index("analysis").loc["Future fires (1-2 days ahead) added", "fire_share"], 1)} with them added.</li>
          <li><b>Carbon monoxide</b> does not rise with upwind fires ({co_a.estimate:+.2f} mg/m³, p = {co_a.p_value:.2f}); Delhi's CO is dominated by traffic.</li>
          <li><b>Wheat season.</b> April–May fires add {p(wheat["fire_share"], 1)} (CI {p(wheat["fire_ci_low"], 1)}–{p(wheat["fire_ci_high"], 1)}).</li>
        </ul>
      </div>
    </section>

    <section id="s7">
      <h2><span class="n">07</span>Festivals</h2>
      <div class="figure reveal" id="fe-fig">
        <h3>Diwali night versus an ordinary night</h3>
        <div class="toggle" role="group" aria-label="Festival"><button type="button" data-f="Diwali" aria-pressed="true">Diwali</button><button type="button" data-f="Dussehra" aria-pressed="false">Dussehra</button></div>
        <svg id="fe" viewBox="0 0 900 280" role="img" aria-label="Hourly PM2.5 around the festival compared with nearby ordinary days"></svg>
        <p class="cap" id="fecap"></p>
      </div>
      <div class="cards reveal">
        <div class="card"><span class="badge no">Diwali</span><h3>{di.night_ratio_of_means:.1f}× on the night, in all 8 years</h3><p class="muted">20:00–02:00 averages {di.night_pm25:.0f} µg/m³ against {di.night_baseline:.0f} on ordinary nights (sign test p = {di.sign_test_p:.3f}); the peak hour reached {di.peak_hour_ratio_max:.1f}× in {int(di.peak_hour_ratio_max_year)}. Diwali accounts for {p(di.share_week)} of the following week, {p(di.share_month, 1)} of its month and {p(reg.loc["Diwali", "share_of_oct_nov"], 1)}–{p(di.share_season, 1)} of the season. In calm years (wind &lt; 2.5 m/s) it was {p(di.share_month_calm, 1)} of its month; in windy years about 0%.</p></div>
        <div class="card"><span class="badge mid">Dussehra</span><h3>No measurable effect</h3><p class="muted">The night is {du.night_ratio_of_means:.1f}× an ordinary night (above baseline in {int(du.nights_above_baseline)} of 8 years, p = {du.sign_test_p:.2f}), and the two-day regression effect is {reg.loc["Dussehra", "two_day_effect"]:.0f} µg/m³ (p = {reg.loc["Dussehra", "p_value"]:.2f}).</p></div>
      </div>
    </section>

    <section id="s8">
      <h2><span class="n">08</span>Weather and the whole season</h2>
      <div class="stats reveal">
        <div class="stat"><span class="eyebrow">Ventilated → stagnant day</span><b>{W["p90_minus_p10"]:.0f}</b><span class="muted">µg/m³ swing within the same week</span></div>
        <div class="stat"><span class="eyebrow">Relative to the season</span><b>{p(W["p90_minus_p10_pct_of_mean"])}</b><span class="muted">of the Oct–Nov mean ({W["oct_nov_mean_pm25"]:.0f} µg/m³)</span></div>
      </div>
      <div class="figure reveal">
        <h3>Where the season's PM2.5 comes from</h3>
        <svg id="comp" viewBox="0 0 900 170" role="img" aria-label="Composition bar of October-November PM2.5"></svg>
        <p class="cap">Crop fires and festivals are measured here. Delhi's own emissions (36%, range 26–50%) are an outside estimate (TERI–ARAI 2018). The remainder is NCR, other regional sources and secondary aerosol.</p>
      </div>
    </section>

    <section id="s9">
      <h2><span class="n">09</span>Would acting a month earlier help?</h2>
      <div class="figure reveal">
        <h3>Severe days come after 1 November; unsafe air starts in October</h3>
        <svg id="before" viewBox="0 0 900 270" role="img" aria-label="October and November mean PM2.5 by year with severe days before 1 November"></svg>
        <p class="cap">Of {int(bf.severe_days_oct_nov.sum())} severe days (above 250 µg/m³) in Oct–Nov 2018–2025, {int(bf.severe_before_1_nov.sum())} came before 1 November. October averaged {oct_ratio.min():.1f}–{oct_ratio.max():.1f}× India's 24-hour standard every year.</p>
      </div>
      <div class="figure reveal" id="pol-fig">
        <h3>Try it: what does an October cut buy?</h3>
        <label class="slider"><span>Cut in Delhi's own emissions from 1 October: <b id="cutv">30%</b></span><input id="cut" type="range" min="0" max="50" step="5" value="30"></label>
        <svg id="pol" viewBox="0 0 900 250" role="img" aria-label="Percent reduction in PM2.5 by lever"></svg>
        <p class="cap">GRAP from 1 September, a month before crop burning: Study 1's best case, as a share of Sep–Jan PM2.5 (at Study 1's estimate the effect is zero; at its upper bound PM2.5 would be 9–10% higher). Delhi's own emissions: share 36% (bar), range 26–50% (whisker), an assumption-based bound. Crop fires halved: measured October fire share.</p>
      </div>
    </section>

    <section id="s10">
      <h2><span class="n">10</span>Conclusion</h2>
      <blockquote class="reveal">Crop-fire smoke causes about {p(allp.share)} of Delhi's October–November PM2.5, a share that held steady even as satellite fire counts fell by {drop * 100:.0f}%, which means falling fire counts are not proof of less burning. Diwali is a sharp one-night spike, Dussehra is not visible, and weather decides how much pollution stays over the city. Starting the emergency plan a month earlier would change little; real cuts in October, at home and in the fields, are what would move the number.</blockquote>
    </section>
  </article>
</div>
<footer><div class="wrap">Delhi's winter smog · Aishwarya Srivastava · Data: CPCB CAAQMS, NASA FIRMS VIIRS, NASA POWER · Every number and chart is drawn from the study's result tables (python run_all.py).</div></footer>
"""
    hero = {"share": allp.share * 100, "lo": allp.share_ci_low * 100, "hi": allp.share_ci_high * 100}
    data = "const D = " + json.dumps(D, default=str) + ";\nconst HERO = " + json.dumps(hero) + ";\n"
    head = (
        '<title>Delhi Winter Smog Study</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800'
        '&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">\n'
    )
    if standalone:
        return (
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + head
            + "<style>\n"
            + css
            + "\n</style>\n</head>\n<body>\n"
            + body
            + "\n<script>\n"
            + data
            + js
            + "\n</script>\n</body>\n</html>\n"
        )
    return head + "<style>\n" + css + "\n</style>\n" + body + "\n<script>\n" + data + js + "\n</script>\n"


if __name__ == "__main__":
    out = os.path.join(ROOT, "reports")
    with open(os.path.join(out, "report.html"), "w", encoding="utf-8") as fh:
        fh.write(build(standalone=True))
    print("written:", os.path.join(out, "report.html"))
