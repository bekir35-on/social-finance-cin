"""
Social Finance (Digital Labs) - case study for the Data Scientist I application
CIN (Child in Need) population analysis

Author: Bekir Onal
Purpose: Exploratory analysis of a UK Local Authority Children's Services
dataset, with a focus on comparing children with exactly 1 CIN episode
against children with 3+ CIN episodes, and how this varies by age.

Run: python3 analysis.py [path_to_data_file.xlsx]
If no path is given, the script looks for the data file in the current
working directory (matching its original filename).
Outputs: prints summary stats to console + saves charts to ./charts/
"""

import sys
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

DEFAULT_FILENAME = "Data_Scientist_I_-_case_study_-_data_file.xlsx"
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILENAME
OUT_DIR = "charts"
os.makedirs(OUT_DIR, exist_ok=True)

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Could not find '{DATA_PATH}'. Pass the path to the data file as an "
        f"argument, e.g.: python3 analysis.py /path/to/{DEFAULT_FILENAME}"
    )

# ---- Style ----
NAVY = "#1B2A4A"
TEAL = "#2E8B8B"
CORAL = "#E07A5F"
GREY = "#8C9096"
LGREY = "#D9DCE1"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": LGREY,
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

# =========================================================
# 1. LOAD & PREPARE
# =========================================================
df = pd.read_excel(DATA_PATH, sheet_name="Sheet1", header=1)

FLAG_COLS = ["ChildOffender", "ASB", "ASBLegalAction", "Absence",
             "AbsenteeismInLast3Terms", "Exclusion", "PRU",
             "ExcludedFromSchool_FixedPeriod", "ExcludedFromSchool_Permanent",
             "DWP", "HousingBenefit", "CouncilTaxArrears", "FreeSchoolMeals",
             "AdultOffender", "NEET", "SEN_Flag"]

COUNT_COLS = ["NumberOfChildOffences", "NumberOfASBLegalActions",
              "NumberOfASBs", "NumberOfAdultOffences"]

FLAG_LABELS = {
    "ChildOffender": "Child is an offender",
    "ASB": "Anti-social behaviour",
    "ASBLegalAction": "ASB legal action taken",
    "Absence": "School absence",
    "AbsenteeismInLast3Terms": "Absent in last 3 terms",
    "Exclusion": "Ever excluded from school",
    "PRU": "Attends Pupil Referral Unit",
    "ExcludedFromSchool_FixedPeriod": "Fixed-period exclusion",
    "ExcludedFromSchool_Permanent": "Permanent exclusion",
    "DWP": "Carer on unemployment benefits",
    "HousingBenefit": "Carer on housing benefit",
    "CouncilTaxArrears": "Carer in council tax arrears",
    "FreeSchoolMeals": "Free school meals",
    "AdultOffender": "Carer has criminal conviction",
    "NEET": "NEET (not in educ./emp./training)",
    "SEN_Flag": "Special educational needs",
}

def age_band(age):
    if pd.isna(age):
        return np.nan
    elif 0 <= age <= 4:
        return "0-4 (Early years)"
    elif 5 <= age <= 10:
        return "5-10 (Primary)"
    elif 11 <= age <= 15:
        return "11-15 (Secondary)"
    elif 16 <= age <= 17:
        return "16-17 (Post-16)"
    else:
        return np.nan

df["AgeBand"] = df["Age"].apply(age_band)
AGE_BAND_ORDER = ["0-4 (Early years)", "5-10 (Primary)", "11-15 (Secondary)", "16-17 (Post-16)"]

# =========================================================
# 1b. DATA QUALITY CHECKS
# =========================================================
print("="*70)
print("DATA QUALITY CHECKS")
print("="*70)

required_cols = ["Child Key", "Age", "NumberOfCinEvents", *FLAG_COLS, *COUNT_COLS]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

print(f"Rows: {len(df):,} | Columns: {df.shape[1]}")
print(f"Duplicate Child Keys: {df['Child Key'].duplicated().sum():,}")
print(f"Fully duplicated rows: {df.duplicated().sum():,}")
print(f"Missing ages: {df['Age'].isna().sum():,}")
print(f"Ages outside 0-17: {(~df['Age'].between(0, 17)).sum():,}")
print(f"Missing CIN counts: {df['NumberOfCinEvents'].isna().sum():,}")
print(f"Rows dropped by AgeBand assignment (invalid/missing age): {df['AgeBand'].isna().sum():,}")

for col in FLAG_COLS:
    bad = ~df[col].isin([0, 1]) & df[col].notna()
    if bad.any():
        print(f"WARNING: {col} has {bad.sum()} values outside 0/1")

# Cross-check CIN 1-5 flags against NumberOfCinEvents (the field our two
# comparison groups are built from) - if these disagree, the group
# definitions below would be unreliable.
print("\nCIN flag consistency vs. NumberOfCinEvents:")
for col, threshold in {"CIN 1": 1, "CIN 2": 2, "CIN 3": 3, "CIN 4": 4, "CIN 5": 5}.items():
    if col in df.columns:
        expected = (df["NumberOfCinEvents"] >= threshold).astype(int)
        mismatch = (df[col].notna() & (df[col] != expected)).sum()
        print(f"  {col}: {mismatch:,} mismatches")

# DWP, AdultOffender, NumberOfAdultOffences and NEET are 0 for every child in
# this extract (checked across all ages, not just a subset) - they carry no
# signal here and are reported as "unpopulated", not "0% prevalence".
ZERO_SIGNAL_COLS = [c for c in FLAG_COLS + COUNT_COLS if df[c].sum() == 0]
print(f"\nFields with zero signal (100% zero, all ages): {ZERO_SIGNAL_COLS}")


# =========================================================
# 2. POPULATION OVERVIEW
# =========================================================
print("="*70)
print("SECTION 1: POPULATION OVERVIEW")
print("="*70)
n_total = len(df)
n_cin = (df["NumberOfCinEvents"] >= 1).sum()
print(f"Total children in dataset: {n_total:,}")
print(f"Children with >=1 CIN episode: {n_cin:,} ({n_cin/n_total*100:.1f}%)")
print(f"Children with 0 CIN episodes (wider vulnerable pop.): {n_total-n_cin:,} ({(n_total-n_cin)/n_total*100:.1f}%)")

# Chart 1: Age distribution overall
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df["Age"], bins=range(0, 19), color=TEAL, edgecolor="white", align="left", rwidth=0.85)
ax.set_xlabel("Age")
ax.set_ylabel("Number of children")
ax.set_title("Age distribution of full vulnerable-children population", fontsize=14, color=NAVY, weight="bold")
ax.set_xticks(range(0, 18, 2))
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/age_distribution.png", dpi=150)
plt.close()

# Chart 2: Distribution of number of CIN events (among those with >=1)
cin_counts = df.loc[df["NumberOfCinEvents"] >= 1, "NumberOfCinEvents"].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(10, 5))
colors = [CORAL if (v == 1 or v >= 3) else LGREY for v in cin_counts.index]
bars = ax.bar(cin_counts.index.astype(str), cin_counts.values, color=colors, edgecolor="white")
ax.set_xlabel("Number of CIN episodes")
ax.set_ylabel("Number of children")
ax.set_title("Distribution of CIN episode counts (children with \u22651 episode)", fontsize=14, color=NAVY, weight="bold")
for b, v in zip(bars, cin_counts.values):
    offset = max(cin_counts.max() * 0.015, 1)
    ax.text(b.get_x()+b.get_width()/2, v+offset, f"{v:,}", ha="center", fontsize=9, color=NAVY)
ax.set_ylim(0, cin_counts.max() * 1.12)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/cin_episode_distribution.png", dpi=150)
plt.close()

# =========================================================
# 3. DEFINE COMPARISON GROUPS
# =========================================================
print()
print("="*70)
print("SECTION 2: GROUP DEFINITIONS")
print("="*70)
g1 = df[df["NumberOfCinEvents"] == 1].copy()
g3 = df[df["NumberOfCinEvents"] >= 3].copy()
g1["Group"] = "Exactly 1 episode"
g3["Group"] = "3+ episodes"
comp = pd.concat([g1, g3], ignore_index=True)

print(f"Group A - exactly 1 CIN episode: n={len(g1):,}")
print(f"Group B - 3 or more CIN episodes: n={len(g3):,}")

# =========================================================
# 4. COMPARE INDICATOR PREVALENCE BETWEEN GROUPS
# =========================================================
# Note: these are treated as ASSOCIATED / CO-OCCURRING INDICATORS, not causal
# risk factors - the data has no dates, so we cannot tell whether an
# indicator preceded or followed a CIN episode. Every binary flag here forms
# a 2x2 table (group x flag), so we use Fisher's exact test throughout rather
# than chi-square - several flags are rare (e.g. permanent exclusion, ASB
# legal action) where chi-square's asymptotic approximation is unreliable
# with small expected cell counts, and Fisher's exact test is valid for a
# 2x2 table regardless of sample size.
print()
print("="*70)
print("SECTION 3: ASSOCIATED INDICATOR COMPARISON (Group A vs Group B)")
print("="*70)

results = []
for col in FLAG_COLS:
    p1 = g1[col].mean()
    p3 = g3[col].mean()
    table = pd.crosstab(comp["Group"], comp[col]).reindex(
        index=["Exactly 1 episode", "3+ episodes"], columns=[0, 1], fill_value=0
    )
    odds_ratio, p = stats.fisher_exact(table.values)
    results.append({
        "Flag": FLAG_LABELS[col],
        "col": col,
        "Group A (1 episode) %": p1*100,
        "Group B (3+ episodes) %": p3*100,
        "Difference (pp)": (p3-p1)*100,
        "Odds ratio": odds_ratio,
        "p_value": p
    })

res_df = pd.DataFrame(results).sort_values("Difference (pp)", ascending=False)
pd.set_option("display.width", 140)
pd.set_option("display.float_format", lambda x: f"{x:.2f}")
print(res_df[["Flag", "Group A (1 episode) %", "Group B (3+ episodes) %", "Difference (pp)", "Odds ratio", "p_value"]].to_string(index=False))
res_df.to_csv(f"{OUT_DIR}/indicator_comparison.csv", index=False)

# Continuous count comparisons
print()
print("-- Count variables (mean, Mann-Whitney U test) --")
count_results = []
for col in COUNT_COLS:
    m1, m3 = g1[col].mean(), g3[col].mean()
    u, p = stats.mannwhitneyu(g1[col], g3[col], alternative="two-sided")
    count_results.append({"Variable": col, "Group A mean": m1, "Group B mean": m3, "p_value": p})
    print(f"{col}: Group A mean={m1:.2f}, Group B mean={m3:.2f}, p={p:.4g}")

# Chart 3: Indicator comparison - horizontal bar chart
fig, ax = plt.subplots(figsize=(11, 8))
plot_df = res_df.sort_values("Group B (3+ episodes) %")
y = np.arange(len(plot_df))
ax.barh(y-0.2, plot_df["Group A (1 episode) %"], height=0.4, color=GREY, label="Exactly 1 episode")
ax.barh(y+0.2, plot_df["Group B (3+ episodes) %"], height=0.4, color=CORAL, label="3+ episodes")
ax.set_yticks(y)
ax.set_yticklabels(plot_df["Flag"], fontsize=10)
ax.set_xlabel("% of children with indicator")
ax.set_title("Prevalence of associated indicators: 1 CIN episode vs 3+ CIN episodes", fontsize=14, color=NAVY, weight="bold")
ax.legend(loc="lower right", frameon=False)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/indicator_comparison.png", dpi=150)
plt.close()

# =========================================================
# 5. AGE ANALYSIS
# =========================================================
print()
print("="*70)
print("SECTION 4: HOW DOES THIS VARY BY AGE?")
print("="*70)

# Age band composition of each group
age_dist = pd.crosstab(comp["Group"], comp["AgeBand"], normalize="index")[AGE_BAND_ORDER] * 100
print("\nAge-band composition of each group (%):")
print(age_dist)

age_group_counts = comp.groupby(["AgeBand", "Group"], observed=True).size().unstack(fill_value=0).reindex(AGE_BAND_ORDER)
print("\nSample size (n) by age band and CIN group - small cells below make percentages noisier:")
print(age_group_counts)

fig, ax = plt.subplots(figsize=(10, 5.5))
x = np.arange(len(AGE_BAND_ORDER))
w = 0.35
ax.bar(x-w/2, age_dist.loc["Exactly 1 episode"], width=w, color=GREY, label="Exactly 1 episode")
ax.bar(x+w/2, age_dist.loc["3+ episodes"], width=w, color=CORAL, label="3+ episodes")
ax.set_xticks(x)
ax.set_xticklabels(AGE_BAND_ORDER)
ax.set_ylabel("% of group")
ax.set_title("Age profile: 1 episode vs 3+ episodes", fontsize=14, color=NAVY, weight="bold")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/age_profile.png", dpi=150)
plt.close()

# Mean age comparison
print(f"\nMean age - Group A (1 episode): {g1['Age'].mean():.2f}")
print(f"Mean age - Group B (3+ episodes): {g3['Age'].mean():.2f}")
t, p = stats.ttest_ind(g1["Age"], g3["Age"], equal_var=False)
print(f"t-test on age difference: t={t:.2f}, p={p:.4g}")

# Key associated indicators x age band, for both groups (does the gap change with age?)
KEY_FLAGS = ["Absence", "AbsenteeismInLast3Terms", "Exclusion", "FreeSchoolMeals",
             "DWP", "SEN_Flag", "ChildOffender", "ASB"]

age_flag_rows = []
for band in AGE_BAND_ORDER:
    for col in KEY_FLAGS:
        a_rate = g1.loc[g1["AgeBand"] == band, col].mean() * 100 if (g1["AgeBand"] == band).any() else np.nan
        b_rate = g3.loc[g3["AgeBand"] == band, col].mean() * 100 if (g3["AgeBand"] == band).any() else np.nan
        age_flag_rows.append({"AgeBand": band, "Flag": FLAG_LABELS[col], "col": col,
                               "Group A %": a_rate, "Group B %": b_rate, "Gap (pp)": b_rate - a_rate})
age_flag_df = pd.DataFrame(age_flag_rows)
age_flag_df.to_csv(f"{OUT_DIR}/age_flag_breakdown.csv", index=False)
print("\nIndicator gap (Group B - Group A) by age band, key indicators:")
print(age_flag_df.pivot(index="Flag", columns="AgeBand", values="Gap (pp)")[AGE_BAND_ORDER].round(1))

# Chart 5: small multiples - gap by age band for a few headline indicators
headline = ["Absence", "AbsenteeismInLast3Terms", "SEN_Flag", "FreeSchoolMeals"]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, col in zip(axes.flat, headline):
    sub = age_flag_df[age_flag_df["col"] == col].set_index("AgeBand").loc[AGE_BAND_ORDER]
    x = np.arange(len(AGE_BAND_ORDER))
    ax.plot(x, sub["Group A %"], marker="o", color=GREY, label="1 episode")
    ax.plot(x, sub["Group B %"], marker="o", color=CORAL, label="3+ episodes")
    ax.set_xticks(x)
    ax.set_xticklabels([b.split(" ")[0] for b in AGE_BAND_ORDER], fontsize=9)
    ax.set_title(FLAG_LABELS[col], fontsize=11, color=NAVY, weight="bold")
    ax.set_ylabel("%")
axes.flat[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Prevalence of associated indicators by age band: 1 episode vs 3+ episodes", fontsize=14, color=NAVY, weight="bold")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/indicators_by_age.png", dpi=150)
plt.close()

# =========================================================
# 6. NUMBER OF CO-OCCURRING INDICATORS ("MULTIPLE DISADVANTAGE") COMPARISON
# =========================================================
# NOTE: this is a simple descriptive count of co-occurring indicators, not a
# validated risk score - indicators are not weighted, and some are related
# (e.g. Absence / AbsenteeismInLast3Terms), so this should be read as a
# rough signal of clustering, not a precise index.
print()
print("="*70)
print("SECTION 5: CUMULATIVE INDICATORS ('MULTIPLE DISADVANTAGE')")
print("="*70)
comp["RiskCount"] = comp[FLAG_COLS].sum(axis=1)
print("Mean number of co-occurring indicators (descriptive count, not a validated risk score):")
print(comp.groupby("Group")["RiskCount"].mean())

fig, ax = plt.subplots(figsize=(9, 5))
for grp, color in [("Exactly 1 episode", GREY), ("3+ episodes", CORAL)]:
    sub = comp[comp["Group"] == grp]["RiskCount"]
    ax.hist(sub, bins=range(0, 12), alpha=0.6, color=color, label=grp, density=True, edgecolor="white")
ax.set_xlabel("Number of co-occurring indicators (out of 16)")
ax.set_ylabel("Proportion of group")
ax.set_title("Cumulative disadvantage: 1 episode vs 3+ episodes", fontsize=14, color=NAVY, weight="bold")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/cumulative_disadvantage.png", dpi=150)
plt.close()

print("\nDone. Charts saved to ./charts/")
