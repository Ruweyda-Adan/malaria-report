#Malaria Incidence analysis for East Africa
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


COUNTRIES = ["Kenya", "Uganda", "Tanzania", "Rwanda", "Burundi",
             "South Sudan", "Ethiopia", "Somalia, Federal Republic of"]          
BENCHMARKS = ["Eastern & Southern Africa", "Sub-Saharan Africa"]
FIRST_ORIGIN, LAST_ORIGIN = 2009, 2021         
HORIZONS = (1, 2, 3)                           
WINDOW = 10                                    
FORECAST_YEARS = (2025, 2026, 2027)
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)



def load(path):
    df = pd.read_csv(path)
    wide = df.pivot(index="TIME_PERIOD", columns="REF_AREA_LABEL",
                    values="OBS_VALUE").sort_index()
    missing = [c for c in COUNTRIES + BENCHMARKS if c not in wide.columns]
    if missing:
        raise SystemExit(f"Not found in file: {missing}")
    return wide[COUNTRIES + BENCHMARKS]


# Descriptives
def describe(wide):
    rows = []
    for c in COUNTRIES + BENCHMARKS:
        s = wide[c]
        rows.append({
            "area": c,
            "2000": s.loc[2000], "2024": s.loc[2024],
            "change_pct": 100 * (s.loc[2024] / s.loc[2000] - 1),
            "peak_year": int(s.idxmax()), "peak_value": s.max(),
            "low_year": int(s.idxmin()), "low_value": s.min(),
        })
    return pd.DataFrame(rows).round(1)


# trends 
def log_linear_trend(series):
    """OLS of log(incidence) on year. Slope -> annual % change, with 95% CI."""
    y = np.log(series.values)
    x = series.index.values.astype(float)
    res = stats.linregress(x, y)
    t = stats.t.ppf(0.975, len(x) - 2)
    lo, hi = res.slope - t * res.stderr, res.slope + t * res.stderr
    pct = lambda b: 100 * (np.exp(b) - 1)
    return pct(res.slope), pct(lo), pct(hi), res.pvalue, res.rvalue ** 2


def trends(wide):
    rows = []
    for c in COUNTRIES + BENCHMARKS:
        for label, (a, b) in {"2000-2024": (2000, 2024),
                              "2015-2024": (2015, 2024)}.items():
            s = wide.loc[a:b, c]
            pct, lo, hi, p, r2 = log_linear_trend(s)
            rows.append({"area": c, "period": label, "annual_change_pct": pct,
                         "ci95_low": lo, "ci95_high": hi, "p_value": p, "r2": r2})
    return pd.DataFrame(rows).round(3)


# forecasts 
def f_naive(train, h):
    return train.iloc[-1]


def f_mean3(train, h):
    return train.iloc[-3:].mean()


def f_trend(train, h):
    """Log-linear trend over the last WINDOW years, extrapolated h years."""
    s = train.iloc[-WINDOW:]
    res = stats.linregress(s.index.values.astype(float), np.log(s.values))
    return float(np.exp(res.intercept + res.slope * (train.index[-1] + h)))


MODELS = {"naive (last value)": f_naive,
          "mean of last 3 years": f_mean3,
          f"log-linear trend (last {WINDOW} yrs)": f_trend}


def backtest(wide):
    rows = []
    for c in COUNTRIES:
        s = wide[c]
        for origin in range(FIRST_ORIGIN, LAST_ORIGIN + 1):
            train = s.loc[:origin]
            for h in HORIZONS:
                if origin + h > s.index.max():
                    continue
                actual = s.loc[origin + h]
                for name, f in MODELS.items():
                    pred = f(train, h)
                    rows.append({"country": c, "origin": origin, "h": h,
                                 "model": name, "actual": actual, "pred": pred,
                                 "ape": abs(pred - actual) / actual * 100,
                                 "log_ratio": np.log(actual / pred)})
    return pd.DataFrame(rows)


def summarise_backtest(bt):
    by_model = bt.groupby("model").agg(MAPE=("ape", "mean"),
                                       median_APE=("ape", "median")).round(1)
    by_model_h = bt.pivot_table(index="model", columns="h", values="ape",
                                aggfunc="mean").round(1)
    by_country = bt.pivot_table(index="country", columns="model",
                                values="ape", aggfunc="mean").round(1)
    return by_model, by_model_h, by_country


def forecast(wide, bt, best_model):
    """Point forecast from the best backtested model, with 80% intervals taken
    from that model's own backtest errors at each horizon (pooled)."""
    f = MODELS[best_model]
    # Empirical 10th/90th percentile of log(actual/forecast) at each horizon,
    # forced to widen (never narrow) as the horizon grows.
    q = {}
    for h in HORIZONS:
        e = bt[(bt.model == best_model) & (bt.h == h)].log_ratio
        q[h] = np.quantile(e, [0.10, 0.90])
    lows = np.minimum.accumulate([q[h][0] for h in HORIZONS])
    highs = np.maximum.accumulate([q[h][1] for h in HORIZONS])
    rows = []
    for c in COUNTRIES:
        s = wide[c]
        for yr in FORECAST_YEARS:
            h = yr - int(s.index.max())
            point = f(s, h)
            rows.append({"country": c, "year": yr, "forecast": point,
                         "low80": point * np.exp(lows[h - 1]),
                         "high80": point * np.exp(highs[h - 1])})
    return pd.DataFrame(rows).round(1)


# figures 
def fig_series(wide):
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True)
    for ax, c in zip(axes.flat, COUNTRIES):
        ax.plot(wide.index, wide[c], color="#b2182b", lw=2, label=c)
        ax.plot(wide.index, wide["Sub-Saharan Africa"], color="grey",
                lw=1.2, ls="--", label="Sub-Saharan Africa")
        ax.set_title(c, fontsize=11)
        ax.grid(alpha=.25)

    axes.flat[0].legend(fontsize=8, frameon=False)
    fig.supylabel("Cases per 1,000 population at risk")
    fig.suptitle("Malaria incidence, 2000-2024", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_incidence_by_country.png", dpi=160)
    plt.close(fig)


def fig_trends(tr):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    for ax, period in zip(axes, ["2000-2024", "2015-2024"]):
        d = tr[(tr.period == period) & tr.area.isin(COUNTRIES)].sort_values(
            "annual_change_pct")
        err = [d.annual_change_pct - d.ci95_low, d.ci95_high - d.annual_change_pct]
        ax.barh(d.area, d.annual_change_pct, xerr=err, color="#2166ac", alpha=.8,
                capsize=3)
        ax.axvline(0, color="k", lw=.8)
        ax.set_title(period)
        ax.set_xlabel("Average annual change in incidence (%), 95% CI")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_trend_estimates.png", dpi=160)
    plt.close(fig)


def fig_forecast(wide, fc):
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True)
    for ax, c in zip(axes.flat, COUNTRIES):
        ax.plot(wide.index, wide[c], color="#b2182b", lw=2)
        d = fc[fc.country == c]
        ax.plot(d.year, d.forecast, color="#2166ac", lw=2, ls="--")
        ax.fill_between(d.year, d.low80, d.high80, color="#2166ac", alpha=.2)
        ax.set_title(c, fontsize=11)
        ax.grid(alpha=.25)
    axes.flat[-1].axis("off")
    fig.supylabel("Cases per 1,000 population at risk")
    fig.suptitle("Forecast 2025-2027 with 80% intervals from backtest errors",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_forecast.png", dpi=160)
    plt.close(fig)


# main 
def main(path):
    wide = load(path)

    desc = describe(wide)
    tr = trends(wide)
    bt = backtest(wide)
    by_model, by_model_h, by_country = summarise_backtest(bt)
    best = by_model["MAPE"].idxmin()
    fc = forecast(wide, bt, best)

    desc.to_csv(OUT / "table1_descriptives.csv", index=False)
    tr.to_csv(OUT / "table2_trends.csv", index=False)
    by_model.to_csv(OUT / "table3_backtest_by_model.csv")
    by_model_h.to_csv(OUT / "table3b_backtest_by_horizon.csv")
    by_country.to_csv(OUT / "table3c_backtest_by_country.csv")
    fc.to_csv(OUT / "table4_forecast_2025_2027.csv", index=False)

    fig_series(wide)
    fig_trends(tr)
    fig_forecast(wide, fc)

    pd.set_option("display.width", 200)
    print("\nDESCRIPTIVES\n", desc.to_string(index=False))
    print("\nTRENDS\n", tr.to_string(index=False))
    print("\nBACKTEST (mean absolute % error)\n", by_model)
    print(by_model_h)
    print(by_country)
    print(f"\nBest model by backtest: {best}")
    print("\nFORECAST\n", fc.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "WB_WDI_SH_MLR_INCD_P3.csv")