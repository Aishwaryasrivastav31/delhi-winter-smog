"""figures.py - every chart in the report, drawn from the result tables (one function per figure)."""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BG, INK, MUTED, GRID = "#f4f6f6", "#1d2a2e", "#7d8a8d", "#dfe4e4"
HAZE, CLEAN, SMOKE, FEST = "#c8721f", "#2a7f74", "#8c4a2f", "#6b5aa6"
plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "font.size": 10.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.titleweight": "bold",
        "axes.axisbelow": True,
        "axes.titlesize": 12.5,
        "axes.titlelocation": "left",
        "legend.frameon": False,
    }
)


def _save(fig, out, name):
    fig.savefig(os.path.join(out, name), dpi=160, bbox_inches="tight")
    plt.close(fig)


def timeline(out, net, panel, years, pol):
    fe = pd.read_csv(
        os.path.join(os.path.dirname(os.path.dirname(out)), "data", "external", "festivals.csv"), parse_dates=["date"]
    )
    up = panel.drop_duplicates("date").set_index("date")["fire_up"]
    fig, axes = plt.subplots(len(years), 1, figsize=(11, 3.3 * len(years)), squeeze=False)
    for ax, y in zip(axes[:, 0], years, strict=False):
        rng = slice(f"{y}-09-15", f"{y}-12-15")
        pm = net.loc[rng]
        ax2 = ax.twinx()
        u = up.loc[rng]
        ax2.bar(
            u.index, u.values, width=1.0, color=SMOKE, alpha=0.30, label="Upwind fire index (scaled within each year)"
        )
        ax2.set_ylim(0, max(u.max(), 0.01) * 1.7)
        ax2.set_yticks([])
        ax2.grid(False)
        ax2.spines["right"].set_visible(False)
        ax.plot(pm.index, pm.values, color=HAZE, lw=1.8, label="Delhi PM2.5 (4-station mean)")
        ax.axhline(250, color=MUTED, lw=0.8, ls=":")
        ax.text(pm.index[1], 254, "severe (>250)", color=MUTED, fontsize=8.5, va="bottom")
        for _, r in fe[fe.date.dt.year == y].iterrows():
            ax.axvline(r.date, color=FEST, lw=1, ls="--")
            ax.text(r.date, pm.max() * 1.02, " " + r.festival, color=FEST, fontsize=8.5, va="bottom")
        g = pol[(pol.policy.str.startswith("GRAP")) & (pol.year == y)]
        for _, r in g.iterrows():
            ax.axvline(r.date, color=CLEAN, lw=1.6)
            ax.text(r.date, pm.max() * 0.80, " GRAP III", color=CLEAN, fontsize=8.5, fontweight="bold")
        ax.axvline(pd.Timestamp(f"{y}-11-01"), color=CLEAN, lw=1, ls=":")
        ax.text(pd.Timestamp(f"{y}-11-01"), pm.max() * 0.66, " 1 Nov", color=CLEAN, fontsize=8.5)
        ax.set_ylim(0, pm.max() * 1.15)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
        ax.set_title(f"{y}: smoke days, festivals and policy dates", pad=6)
        ax.set_ylabel("PM2.5 (µg/m³)")
        if y == years[0]:
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9)
    fig.tight_layout()
    _save(fig, out, "fig1_timeline.png")


def effects_fig(out, eff):
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ks = [k for k in eff.period.unique() if "minus" not in k]
    for i, k in enumerate(ks):
        for j, (t, col) in enumerate((("upwind", SMOKE), ("downwind (placebo)", MUTED))):
            r = eff[(eff.period == k) & (eff.term == t)].iloc[0]
            x = i + (j - 0.5) * 0.28
            ax.errorbar(
                x,
                r.estimate,
                yerr=[[r.estimate - r.ci_low], [r.ci_high - r.estimate]],
                fmt="o" if j == 0 else "s",
                color=col,
                capsize=4,
                lw=2,
                ms=7,
                label=t.capitalize() if i == 0 else None,
            )
            ax.text(x + 0.05, r.estimate, f" {r.estimate:.0f}", va="center", fontsize=9, color=col)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(len(ks)), [f"Detections {k}" for k in ks])
    ax.set_ylabel("µg/m³ per 1,000 weighted detections\n(3-day effect)")
    ax.set_title("Upwind fires raise PM2.5 in both eras; one detection counts ~8x more after 2024")
    ax.legend(loc="upper left")
    _save(fig, out, "fig2_effects.png")


def checks_fig(out, ladder, checks):
    rows = [(r.analysis.replace("PRIMARY: ", ""), r, "ladder") for r in ladder.itertuples()]
    rows += [(r.analysis, r, "check") for r in checks.itertuples() if not r.analysis.startswith("PRIMARY")]
    fig, ax = plt.subplots(figsize=(10.5, 0.46 * len(rows) + 1.6))
    for i, (name, r, _kind) in enumerate(rows[::-1]):
        prim = "per detection period" in name
        ax.plot([r.fire_ci_low * 100, r.fire_ci_high * 100], [i, i], color=SMOKE, lw=2.4 if prim else 1.6)
        ax.plot(r.fire_share * 100, i, "o", color=SMOKE, ms=8 if prim else 6)
        if np.isfinite(getattr(r, "placebo_share", np.nan)):
            ax.plot([r.placebo_ci_low * 100, r.placebo_ci_high * 100], [i - 0.24, i - 0.24], color=MUTED, lw=1.2)
            ax.plot(r.placebo_share * 100, i - 0.24, "s", color=MUTED, ms=4.5)
    ax.set_yticks(range(len(rows)), [n for n, _, _ in rows[::-1]], fontsize=9)
    for lbl in ax.get_yticklabels():
        if "per detection period" in lbl.get_text():
            lbl.set_fontweight("bold")
    ax.axhline(len(rows) - len(ladder) - 0.5, color=MUTED, lw=0.6)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel(
        "Share of Oct-Nov PM2.5 (%)   ● from upwind fires   ■ placebo: 'share' from downwind fires   lines = 95% CI"
    )
    ax.set_title(
        "A one-effect model hides the 2024-25 smoke; with per-period effects the share is 12-18% in every check using NASA wind"
    )
    ax.text(
        0,
        -0.1,
        "* Delhi monitors' wind sensors disagree with NASA wind by a median ~95° on Oct-Nov days, so they cannot tell which fires are upwind.",
        transform=ax.transAxes,
        fontsize=8.5,
        color=MUTED,
    )
    _save(fig, out, "fig3_checks.png")


def by_year_fig(out, by_year):
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(by_year))
    ax.bar(x, by_year.share * 100, color=SMOKE, width=0.55, alpha=0.9, label="Crop-fire share of Oct-Nov PM2.5")
    ax.errorbar(
        x,
        by_year.share * 100,
        yerr=[(by_year.share - by_year.share_ci_low) * 100, (by_year.share_ci_high - by_year.share) * 100],
        fmt="none",
        color=INK,
        capsize=3,
        lw=1,
    )
    ax.set_ylabel("Fire share of PM2.5 (%)")
    ax.set_xticks(x, by_year.year)
    ax2 = ax.twinx()
    ax2.plot(
        x,
        by_year.snpp_detections_oct_nov / 1000,
        color=HAZE,
        marker="o",
        lw=2.2,
        label="Satellite fire detections, Oct-Nov (thousands)",
    )
    ax2.set_ylabel("Detections (thousands)", color=HAZE)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax2.set_ylim(0, by_year.snpp_detections_oct_nov.max() / 1000 * 1.25)
    ax.set_ylim(0, max(35, (by_year.share_ci_high.max() * 100) * 1.1))
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=9)
    ax.set_title("Detections fell ~90% after 2021; the smoke's share of Delhi PM2.5 did not")
    _save(fig, out, "fig4_share_by_year.png")


def event_fig(out, es):
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    for ev, col, mk in (("upwind spike", SMOKE, "o"), ("downwind spike (placebo)", MUTED, "s")):
        g = es[es.event == ev]
        ax.fill_between(g.offset, g.ci_low, g.ci_high, color=col, alpha=0.15)
        ax.plot(
            g.offset, g.pm25_vs_21day_mean, color=col, marker=mk, lw=2, label=f"{ev} days (n={int(g.events.max())})"
        )
    ax.axhline(0, color=INK, lw=0.8)
    ax.axvline(0, color=INK, lw=0.6, ls=":")
    ax.set_xlabel("Days from the fire spike")
    ax.set_ylabel("PM2.5 vs its 21-day mean (µg/m³)")
    ax.set_title("Around heavy upwind-fire days PM2.5 rises; around heavy downwind-fire days it does not")
    ax.legend(loc="upper left", fontsize=9)
    _save(fig, out, "fig5_event_study.png")


def dose_fig(out, dose):
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    x = np.arange(len(dose))
    ax.bar(x, dose.estimate, color=SMOKE, alpha=0.85, width=0.6)
    ax.errorbar(
        x,
        dose.estimate,
        yerr=[dose.estimate - dose.ci_low, dose.ci_high - dose.estimate],
        fmt="none",
        color=INK,
        capsize=4,
    )
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x, ["lightest\n20%", "2nd", "3rd", "4th", "heaviest\n20%"])
    ax.set_xlabel("Same-day upwind fire exposure (fifths within each year)")
    ax.set_ylabel("PM2.5 vs no-upwind-fire days (µg/m³)")
    ax.set_title("The heavier the upwind smoke, the higher Delhi's PM2.5")
    _save(fig, out, "fig6_dose.png")


def perm_fig(out, null, obs):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.hist(np.asarray(null) * 100, bins=40, color=MUTED, alpha=0.8, label=f"Shuffled winds ({len(null)} runs)")
    ax.axvline(obs * 100, color=SMOKE, lw=2.5, label=f"Real winds: {obs:.1%}")
    ax.set_xlabel("Fire share of Oct-Nov PM2.5 (%)")
    ax.set_ylabel("Runs")
    ax.set_title("Shuffling wind within each week rarely reproduces the real share")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, out, "fig7_permutation.png")


def festival_fig(out, prof):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
    for ax, f, col in zip(axes, ("Diwali", "Dussehra"), (FEST, CLEAN), strict=False):
        g = prof[prof.festival == f]
        m = g.groupby("hour")[["pm25", "baseline"]].mean()
        for _, gy in g.groupby("year"):
            ax.plot(gy.hour, gy.pm25, color=col, alpha=0.18, lw=1)
        ax.axvspan(20, 26, color=col, alpha=0.07)
        ax.plot(m.index, m.baseline, color=MUTED, lw=2, ls="--", label="Same hours, ordinary days ±4-10 days")
        ax.plot(m.index, m.pm25, color=col, lw=2.4, label=f"{f} (8 years, mean)")
        ax.set_xticks([0, 12, 20, 24, 36, 48], ["00h", "12h", "20h", "00h", "12h", "00h"])
        ax.set_title(f)
        ax.legend(loc="upper left", fontsize=9)
    axes[0].set_ylabel("PM2.5 (µg/m³), hourly")
    fig.tight_layout()
    _save(fig, out, "fig8_festivals.png")


def composition_fig(out, compo):
    c = compo.copy()
    fest = c[c.component.str.contains("Diwali|Dussehra")]
    c = pd.concat(
        [
            c[~c.component.str.contains("Diwali|Dussehra")].iloc[:1],
            pd.DataFrame([{"component": "Diwali + Dussehra", "share": fest.share.sum()}]),
            c[~c.component.str.contains("Diwali|Dussehra")].iloc[1:],
        ],
        ignore_index=True,
    )
    fig, ax = plt.subplots(figsize=(10, 2.6))
    cols = [SMOKE, FEST, CLEAN, "#c9cfcf"]
    left = 0
    for r, col in zip(c.itertuples(), cols, strict=False):
        w = max(r.share, 0)
        ax.barh(0, w, left=left, color=col, height=0.55, edgecolor=BG, lw=1.5)
        if w > 0.04:
            ax.text(
                left + w / 2,
                0,
                f"{r.share:.0%}",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                fontsize=12,
            )
            ax.text(left + w / 2, -0.45, r.component.replace(": ", ":\n"), ha="center", va="center", fontsize=8.8)
        else:
            ax.annotate(
                f"{r.component}: <1% of the season",
                (left + w / 2, 0.28),
                (left + 0.06, 0.62),
                fontsize=8.8,
                color=FEST,
                arrowprops={"arrowstyle": "-", "color": FEST, "lw": 0.8},
            )
        left += w
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.8, 0.8)
    ax.axis("off")
    ax.set_title("Where Delhi's October-November PM2.5 comes from (Delhi's own 36% is an outside estimate, TERI-ARAI)")
    _save(fig, out, "fig9_composition.png")


def policy_fig(out, grap, curve):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw={"width_ratios": [1.1, 1.3]})
    ax = axes[0]
    g = grap[grap.earlier_start.astype(str).str.endswith("09-01")]
    x = np.arange(len(g))
    best, worst = g.best_pct_of_sep_jan * 100, g.worst_pct_of_sep_jan * 100
    for i in range(len(g)):
        ax.plot([i, i], [worst.iloc[i], best.iloc[i]], color=CLEAN, lw=2.2)
        ax.plot([i - 0.06, i + 0.06], [best.iloc[i]] * 2, color=CLEAN, lw=2.2)
        ax.plot([i - 0.06, i + 0.06], [worst.iloc[i]] * 2, color=CLEAN, lw=2.2)
        ax.plot(i, 0, "o", color=CLEAN, ms=8)
        ax.text(i + 0.08, best.iloc[i], f" best case {best.iloc[i]:.1f}%", fontsize=8.5, va="center")
        ax.text(i + 0.08, 0, " no detectable effect", fontsize=8.5, va="center")
        ax.text(i + 0.08, worst.iloc[i], f" worst case {worst.iloc[i]:.1f}%", fontsize=8.5, va="center")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x, g.season)
    ax.set_xlim(-0.5, len(g) - 0.2)
    ax.set_ylabel("% lower PM2.5, Sep-Jan\n(negative = higher)")
    ax.set_title("GRAP from 1 September (Study 1 range)")
    ax = axes[1]
    cv = curve.groupby(["emission_cut", "delhi_share"]).pct_reduction_october.mean().unstack()
    ax.fill_between(
        cv.index * 100, cv["low"] * 100, cv["high"] * 100, color=CLEAN, alpha=0.18, label="Delhi share 26-50%"
    )
    ax.plot(cv.index * 100, cv["central"] * 100, color=CLEAN, lw=2.4, label="Delhi share 36% (central)")
    ax.set_xlabel("Cut in Delhi's own emissions during October (%)")
    ax.set_ylabel("% lower October PM2.5")
    ax.set_title("Cutting Delhi's own emissions from 1 October")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    _save(fig, out, "fig10_policy.png")


def before_fig(out, before):
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(len(before))
    ax.bar(x, before.mean_pm25_october, color=HAZE, alpha=0.85, width=0.38, label="October mean")
    ax.bar(x + 0.4, before.mean_pm25_november, color=SMOKE, alpha=0.85, width=0.38, label="November mean")
    for i, r in enumerate(before.itertuples()):
        ax.text(
            i + 0.2,
            max(r.mean_pm25_october, r.mean_pm25_november) + 8,
            f"{r.severe_before_1_nov} severe\nbefore 1 Nov",
            ha="center",
            fontsize=8.2,
            color=INK,
        )
    ax.axhline(60, color=CLEAN, lw=1.2, ls="--", zorder=5)
    ax.text(-0.45, 64, "India 24-h standard (60)", color=CLEAN, fontsize=8.5, ha="left", zorder=6, fontweight="bold")
    ax.set_xticks(x + 0.2, before.year)
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_ylim(0, before[["mean_pm25_october", "mean_pm25_november"]].max().max() * 1.3)
    r = before.mean_pm25_october / 60
    ax.set_title(
        f"Severe days are rare before 1 November, but October already averages {r.min():.1f}-{r.max():.1f}x the daily standard"
    )
    ax.legend(loc="upper right", fontsize=9, ncol=2, bbox_to_anchor=(1, 1.02))
    _save(fig, out, "fig11_before_policy.png")


def make_all(
    out,
    net,
    panel,
    years,
    pol,
    eff,
    ladder,
    checks,
    dose,
    es,
    null,
    obs,
    by_year,
    c,
    prof,
    compo,
    grap,
    curve,
    before,
    fest_events,
):
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    timeline(out, net, panel, [y for y in (2018, 2021, 2024, 2025) if y in years], pol)
    effects_fig(out, eff)
    checks_fig(out, ladder, checks)
    by_year_fig(out, by_year)
    event_fig(out, es)
    dose_fig(out, dose)
    perm_fig(out, null, obs)
    festival_fig(out, prof)
    composition_fig(out, compo)
    policy_fig(out, grap, curve)
    before_fig(out, before)
