# Children in Need (CIN) Population Analysis

Exploratory data analysis of a UK Local Authority Children's Services dataset,
examining how children with a **single** Child in Need (CIN) episode differ from
those with **repeated** episodes — and how those differences change with age.

Completed as a Data Scientist case study for **Social Finance** (July 2026).

**Tools:** Python · Pandas · NumPy · SciPy · Matplotlib

---

## Overview

A "Child in Need" (CIN) episode is a period during which Children's Services has
formally determined that a child is acutely vulnerable and requires action, short
of statutory child protection. Understanding which children go on to have
*repeated* episodes helps a Local Authority act earlier and more precisely.

This project turns frontline intuition into empirical, fact-based evidence by
answering two questions:

1. What distinguishes a child with **exactly 1** CIN episode from a child with **3 or more**?
2. How do those distinctions change with the child's **age**?

## The data

| | |
|---|---|
| Children in the dataset | **74,247** |
| Fields per child | **28** |
| Children with ≥1 CIN episode | **30.3%** |
| Duplicate / missing key records | **0** |

The dataset is a **single Local Authority, point-in-time snapshot** with no dates.
Each row is one child, with an age, a count of CIN episodes, and a set of binary
indicator flags (e.g. free school meals, school absence, exclusions, benefits).

> **Data confidentiality:** the underlying dataset contains sensitive children's
> services records and is **not** included in this repository. Only the analysis
> code, the resulting charts, and the presentation are shared here.

## Method

- **Data quality checks first** — duplicates, missing/invalid ages, out-of-range
  flags, and cross-checks of the CIN flags against the episode count. Fields that
  were 100% zero across all 74,247 children (DWP, AdultOffender, NEET) were
  identified as *unpopulated* and excluded from conclusions rather than reported
  as "0% prevalence".
- **Two comparison groups:** Group A = exactly 1 episode (n = 5,455),
  Group B = 3+ episodes (n = 7,428).
- **Statistical testing:** Fisher's exact test for each binary indicator (chosen
  over chi-square because several indicators are rare and chi-square's
  approximation is unreliable with small counts); Mann-Whitney U for count
  variables; Welch's t-test for the age difference.
- **Age analysis** across four bands (0–4, 5–10, 11–15, 16–17), plus a simple
  descriptive count of co-occurring indicators ("multiple disadvantage").

## Key findings

**1. Repeat-episode children show more associated indicators across the board.**
The widest gaps are housing benefit (+15.5pp), free school meals (+13.6pp) and
school absence (+8.2pp) — all statistically significant (Fisher's exact, p < 0.01).

![Indicator prevalence: 1 episode vs 3+ episodes](images/indicator_comparison.png)

**2. Disadvantage tends to stack.** Children with 3+ episodes carry on average
**1.8× more** co-occurring indicators (1.11 vs 0.63) — repeat CIN involvement
looks like one marker within a wider cluster of household-level disadvantage,
not an isolated event.

**3. Age changes the story.** Under-5s are far more common in the single-episode
group (22.5% vs 12.5%) — their involvement looks more likely to resolve after one
episode. Recurrence concentrates in primary-school age (42% of the 3+ group is
aged 5–10). The attendance gap between the two groups also **widens sharply
through the teenage years.**

![Associated indicators by age band](images/indicators_by_age.png)

## Recommendations to the Local Authority

1. **Watch the housing-benefit / free-school-meals / attendance signal** — the
   three widest gaps — as the starting point for an early-warning indicator.
2. **Focus early support on primary-age children**, where recurrence is heaviest.
3. **Clarify data recording before building further** (fix an exclusion-flag
   inconsistency; confirm why three fields are unpopulated) so any future
   predictive model rests on reliable fields.

## Limitations

- **No timing information** — we can describe association, not cause and effect.
- **No demographic or geographic detail** (gender, ethnicity, deprivation), which
  limits equity and targeting analysis.
- **Single Local Authority** — findings reflect one area's population and
  recording practices and may not generalise.

## Repository structure

```
social-finance-cin/
├── analysis.py          # Full analysis: data checks, stats, charts
├── images/              # Charts produced by the analysis
└── presentation/        # Stakeholder slide deck (.pptx)
```

## How to run

```bash
pip install pandas numpy scipy matplotlib openpyxl
python analysis.py path/to/data_file.xlsx
```

The script prints summary statistics to the console and saves all charts to a
`charts/` folder. (The data file itself is not distributed — see the
confidentiality note above.)

---

*Bekir Onal — Data Analyst · Python, SQL, Pandas · Leicester, UK*
