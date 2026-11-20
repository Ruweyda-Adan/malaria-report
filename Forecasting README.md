# Malaria Forecasting (Python)

This part extends the Power BI dashboard from describing incidence to quantifying trends and testing how well simple models can forecast them.

**Data:** World Bank WDI indicator `SH.MLR.INCD.P3`, incidence of malaria per 1,000 population *at risk*, national level, annual, 2000-2024. Countries: Kenya, Uganda, Tanzania, Rwanda, Burundi, South Sudan, Ethiopia and Somalia, with the Eastern & Southern Africa and Sub-Saharan Africa aggregates as benchmarks.

## Methods

1. **Descriptives.** 2000 and 2024 values, percentage change, peak and lowest years.
2. **Trend estimation.** For each country, an OLS regression of log(incidence) on year gives the average annual % change with a 95% confidence interval. It is fitted over the full period (2000-2024) and the recent decade (2015-2024) because several series change direction partway through.
3. **Backtest.** A rolling-origin evaluation: for each forecast origin from 2009 to 2021, each model is fitted on data up to that year and forecasts 1, 2 and 3 years ahead, scored by mean absolute percentage error (MAPE). Three models are compared:
   - naive: repeat the last observed value
   - mean of the last 3 years
   - log-linear trend over the last 10 years, extrapolated
4. **Forecast 2025-2027.** The model with the lowest backtest error produces the forecast. The 80% intervals are the 10th and 90th percentiles of that model's backtest errors at each horizon, pooled across countries.

## Key findings

| Country | 2000 | 2024 | Change | Annual trend 2000-2024 (95% CI) | Annual trend 2015-2024 (95% CI) |
|---|---|---|---|---|---|
| Kenya | 220.3 | 74.2 | -66% | -4.5% (-5.8, -3.1) | -0.1% (-2.0, +1.8) |
| Uganda | 482.8 | 264.2 | -45% | -3.2% (-3.6, -2.8) | -0.8% (-1.7, +0.1) |
| Tanzania | 334.6 | 136.7 | -59% | -4.1% (-5.1, -3.1) | +0.5% (-1.6, +2.7) |
| Rwanda | 180.4 | 77.1 | -57% | +0.7% (-3.4, +5.0) | not meaningful (see below) |
| Burundi | 427.5 | 314.9 | -26% | -0.2% (-1.2, +0.8) | +0.5% (-1.2, +2.3) |
| South Sudan | 344.6 | 254.1 | -26% | -0.9% (-1.2, -0.6) | -0.4% (-1.2, +0.5) |
| Ethiopia | 189.2 | 138.5 | -27% | -5.2% (-7.3, -2.9) | +1.2% (-11.9, +16.2) |
| Somalia | 133.2 | 53.3 | -60% | -4.2% (-6.2, -2.2) | -0.3% (-0.7, +0.1) |

- **Most of the long-run decline happened early.** Kenya fell from 243 in 2001 to 80 in 2008, then stayed between about 72 and 89 for the next 16 years, with a small rise in 2020-2021. The 2015-2024 trend is statistically indistinguishable from zero. Tanzania and Uganda show the same pattern: a steep fall to the mid-2010s and a plateau since.
- **Uganda, Burundi and South Sudan remain the highest-burden countries** in this group (264, 315 and 254 per 1,000 at risk in 2024), about three to four times Kenya's and Rwanda's levels and roughly five to six times Somalia's.
- **Somalia has the lowest incidence in the group.** It fell from 133 in 2000 to a low of 34 in 2011, and was 53 in 2024. The 2015-2024 trend is not statistically different from zero.
- **Burundi has no clear long-run trend.** It fell to 232 in 2012, rose to 351 in 2018 and was 315 in 2024.
- **Rwanda and Ethiopia are volatile.** Rwanda spiked to 711 in 2017 before falling back to 77, so a straight-line trend is not an appropriate summary for it (the 2015-2024 fit gives -22.5% a year, but only because the window starts just before the spike). Ethiopia fell to 34 in 2019 and rose to 139 by 2024.
- **Regional context.** Eastern & Southern Africa fell from 288 to 196 (-32%) and Sub-Saharan Africa from 340 to 229 (-33%). Both bottomed out in 2019.

## Backtest results

| Model | MAPE, all horizons | 1 year | 2 years | 3 years |
|---|---|---|---|---|
| Naive (last value) | **24.3%** | 13.8% | 25.8% | 33.2% |
| Mean of last 3 years | 32.6% | 22.3% | 33.6% | 41.8% |
| Log-linear trend (10 yrs) | 60.1% | 33.7% | 57.9% | 88.7% |

Extrapolating a trend performed worst, because the direction of change shifted over time (for example the plateau after 2015). The naive model was the most accurate, so the forecast below holds each country at its 2024 level. **Its useful content is the uncertainty range, not the point estimate.**

## Forecast 2025-2027 (cases per 1,000 population at risk)

| Country | Point forecast | 80% interval, 2025 | 80% interval, 2027 |
|---|---|---|---|
| Kenya | 74 | 60-87 | 49-102 |
| Uganda | 264 | 214-311 | 175-364 |
| Tanzania | 137 | 111-161 | 91-188 |
| Rwanda | 77 | 63-91 | 51-106 |
| Burundi | 315 | 255-370 | 209-434 |
| South Sudan | 254 | 206-299 | 168-350 |
| Ethiopia | 139 | 112-163 | 92-191 |
| Somalia | 53 | 43-63 | 35-73 |

## Limitations

- **Unit of measurement.** The indicator is per 1,000 population *at risk*, not per total population, so values are not cases per capita. The size of the at-risk population can change over time.
- **Modelled national estimates.** Values are national-level estimates reported through WDI, so they hide differences between regions and districts, and may be revised. See the indicator's WDI metadata for source details.
- **Short series.** There are 25 annual points per country, which limits how complex a model can be.
- **Simple models, no drivers.** The models use only past incidence. They do not include rainfall, bed-net coverage, funding, conflict or drug resistance, which shape malaria trends. The analysis shows what changed, not why.
- **Pooled intervals.** The same relative interval widths are applied to every country. They are likely too wide for stable series (Kenya, South Sudan) and too narrow for volatile ones (Rwanda, Ethiopia).
- **Not for operational use.** These forecasts are an exercise in method and should not guide decisions on interventions.

## Figures and tables

- `outputs/fig1_incidence_by_country.png`: incidence by country against the Sub-Saharan Africa benchmark
- `outputs/fig2_trend_estimates.png`: annual trend estimates with 95% CIs
- `outputs/fig3_forecast.png`: forecast with 80% intervals
- `outputs/table1_descriptives.csv`, `table2_trends.csv`, `table3*_backtest*.csv`, `table4_forecast_2025_2027.csv`
