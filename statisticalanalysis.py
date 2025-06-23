##############################################################################
# 0 ─── requirements ─────────────────────────────────────────────────────────
##############################################################################

import pathlib, re, numpy as np, pandas as pd
from statsmodels.stats.multitest import multipletests
from functools import partial
from sklearn.utils import resample
from sklearn.metrics import (
    balanced_accuracy_score, precision_score, recall_score, f1_score
)

##############################################################################
# 1 ─── Configuration ────────────────────────────────────────────────────────
##############################################################################
ROOT      = pathlib.Path("Z:/EKFZ/TransdiagnosticPPB_Vincent Promotion/Prompting_optimization/Results/predictions/merged_csvs")        # where GT.csv + run*/ live
RUN_FOLDERS = sorted(ROOT.glob("run*"))      # run1, run2, run3 …
GT_FILE   = ROOT / "GT_eng.csv"                  # adjust if the file is named differently
PROMPT_RE = re.compile(r"^Prompt \d+$")      # boolean columns only (skip “… Reasoning”)

metric_funcs = {
    "balanced_accuracy": balanced_accuracy_score,
    "precision": partial(precision_score, zero_division=0),
    "recall":    partial(recall_score,    zero_division=0),
    "f1":        partial(f1_score,        zero_division=0),
}

BOOT_ITERATIONS = 2_000                        # patient-level bootstrap size
RANDOM_STATE    = 42                         # makes the bootstrap reproducible
alpha = 0.05

##############################################################################
# 1 ─── Load ground truth ────────────────────────────────────────────────────
##############################################################################
gt = pd.read_csv(GT_FILE)                    # expected columns: id, Addiction, Anxiety, …
gt = gt.set_index("id")                      # index by patient_id for quick joins

# ------------------------------------------------------
print("── duplicate-row / duplicate-column check ──")

# a) duplicate patient-ID rows
dupe_ids = gt.index[gt.index.duplicated()].unique()
print("duplicate ids:", dupe_ids[:5], "… total =", len(dupe_ids))

# b) duplicate columns (same domain header twice)
dupe_cols = gt.columns[gt.columns.duplicated()].unique()
print("duplicate columns:", dupe_cols)

# c) duplicate (id, domain) pairs after melting
gt_long_tmp = (
    gt.reset_index()
      .melt(id_vars="id", var_name="domain", value_name="y_true")
)
dupe_pairs = gt_long_tmp[gt_long_tmp.duplicated(["id", "domain"], keep=False)]
print("duplicate (id, domain) pairs:", len(dupe_pairs))
print(dupe_pairs.head())
print("────────────────────────────────────────────")
# ------------------------------------------------------

##############################################################################
# 2 ─── Read every run/domain CSV and build one tidy DataFrame ──────────────
##############################################################################
records = []

for run_path in RUN_FOLDERS:
    run_name = run_path.name                 # e.g. "run1"
    
    for csv in run_path.glob("*.csv"):
        # infer the domain name from the file, e.g. “…_Addiction.csv” → "Addiction"
        # 1.   extract domain robustly
        match   = re.search(r"prompts\d+-\d+_(.+?)\.csv$", csv.name)
        domain  = match.group(1) if match else None
        
        df = pd.read_csv(csv)
        df = df.set_index("id")              # patient id column
        
        # keep only the columns that are pure boolean prompts (drop reasoning)
        prompt_cols = [c for c in df.columns if PROMPT_RE.match(c)]
        df = df[prompt_cols]

        # reshape: id × prompt → long format
        df_long = (
            df
            .reset_index()
            .melt(id_vars="id", var_name="prompt", value_name="y_pred")
            .assign(run=run_name, domain=domain)
        )
        records.append(df_long)

# stack all runs → one master DF
pred = pd.concat(records, ignore_index=True)

##############################################################################
# 3 ─── Merge ground truth & verify alignment ────────────────────────────────
##############################################################################
# ❶ reshape GT: id × domain → long
gt_long = (
    gt.reset_index()                                # id back to column
      .melt(id_vars="id",
            var_name="domain",
            value_name="y_true")                    # id · domain · y_true
)

# ❷ join on *both* keys
pred = (
    pred
      .merge(gt_long, on=["id", "domain"], how="left", validate="many_to_one")
)

missing = pred[pred["y_true"].isna()]

if not missing.empty:
    print("First few missing rows:")
    print(missing.head())
    print("\nCount by domain:")
    print(missing["domain"].value_counts().to_frame("n_missing"))

assert pred["y_true"].notna().all(), "Some (id, domain) pairs missing in GT!"

##############################################################################
# 4 ─── Point estimates per (domain, prompt, metric) averaged over runs ────
##############################################################################
group_cols = ["domain", "prompt", "run"]

point_est = (
    pred.groupby(group_cols)
        [["y_true", "y_pred"]]
        .apply(lambda g: {
            m: f(g.y_true, g.y_pred) for m, f in metric_funcs.items()
        })
        .apply(pd.Series)
        .groupby(["domain", "prompt"])       # collapse the three runs
        .mean()
)

##############################################################################
# 5 ─── Patient-level bootstrap CIs ─────────────────────────────────────────
##############################################################################
rng = np.random.default_rng(RANDOM_STATE)
patients = pred["id"].unique()
boot_results = {m: [] for m in metric_funcs}

for _ in range(BOOT_ITERATIONS):
    sample_ids = rng.choice(patients, size=len(patients), replace=True)
    boot = pred[pred["id"].isin(sample_ids)]

    # metric → DataFrame (domain, prompt) index
    for m, func in metric_funcs.items():
        vals = (
            boot.groupby(group_cols)
                [["y_true", "y_pred"]]
                .apply(lambda g: func(g.y_true, g.y_pred))
                .groupby(["domain", "prompt"])
                .mean()                    # average three runs
        )
        boot_results[m].append(vals)

# convert lists → (domain, prompt) × BOOT_ITERATIONS matrices
ci_frames = {}
for m, lst in boot_results.items():
    mat = pd.concat(lst, axis=1)     # rows: (domain, prompt)  ·  cols: replicates

    ci = pd.DataFrame({
        "ci_low":  mat.quantile(0.025, axis=1),   # 2.5 % quantile,  keeps index
        "ci_high": mat.quantile(0.975, axis=1)    # 97.5 % quantile
    })
    ci.index.names = ["domain", "prompt"]         # make sure names are set
    ci_frames[m] = ci

##############################################################################
# 8 ─── p-values: best vs worst prompt per domain & metric ───────────────────
##############################################################################
# We reuse:
#   point_est[m]     — Series indexed by (domain, prompt) with mean metric
#   boot_results[m]  — list of length BOOT_ITERATIONS,
#                      each is a Series with same index

pval_frames = []

for m, boot_list in boot_results.items():
    # ❶ locate the best and worst prompt *by point estimate* (averaged over runs)
    #    — one winner and loser for each domain
    best_idx = point_est[m].groupby("domain").idxmax()   # e.g. ('Anxiety','Prompt 3')
    worst_idx = point_est[m].groupby("domain").idxmin()

    # ❷ stack bootstrap replicates into a DataFrame
    mat = pd.concat(boot_list, axis=1)   # index: (domain, prompt) ; columns: replicates

    rows = []
    for dom in best_idx.index:           # iterate over domains
        idx_best  = best_idx[dom]              # ('Anxiety','Prompt 3'), …
        idx_worst = worst_idx[dom]
        idx_p1    = (dom, "Prompt 1")
        idx_p7    = (dom, "Prompt 7")

        # ---------- best  vs  worst ----------------------------------------
        diff_bw = mat.loc[idx_best] - mat.loc[idx_worst]
        p_bw = 2 * min((diff_bw <= 0).mean(), (diff_bw >= 0).mean())

        # ---------- best  vs  Prompt x ------------------------------------
        if idx_p1 in mat.index and idx_best != idx_p1:
            diff_p1 = mat.loc[idx_best] - mat.loc[idx_p1]
            p_b1 = 2 * min((diff_p1 <= 0).mean(), (diff_p1 >= 0).mean())
        else:                                # P1 absent *or* already best
            p_b1 = np.nan                    # keep table shape

        rows.append({
            "metric": m,
            "domain": dom,
            "best_prompt":   idx_best[1],
            "worst_prompt":  idx_worst[1],
            "p_best_vs_worst":        p_bw,
            "p_best_vs_prompt1":      p_b1,
        })

    pval_frames.append(pd.DataFrame(rows))

pvals = pd.concat(pval_frames, ignore_index=True)

p_cols = ["p_best_vs_worst", "p_best_vs_prompt1"]

for col in p_cols:
    mask = pvals[col].notna()                       # skip NaNs
    adj_p = multipletests(
                pvals.loc[mask, col], alpha=alpha,
                method="fdr_bh"                     # or "bonferroni"
            )[1]
    pvals.loc[mask, col] = adj_p

pvals["sig_bw"] = pvals["p_best_vs_worst"]   < alpha
pvals["sig_b1"] = pvals["p_best_vs_prompt1"] < alpha

##############################################################################
# 6 ─── Assemble final tidy table: point, ci_low, ci_high ───────────────────
##############################################################################
outs = []

for m in metric_funcs:
    # 1️⃣  point estimates – flatten *completely*
    df_point = (
        point_est[m]                       # Series indexed by (domain,prompt)
        .rename("point")
        .reset_index(drop=False)           # domain + prompt become columns
    )

    # 2️⃣  CI limits – flatten *completely*
    df_ci = (
        ci_frames[m]                       # DataFrame, same MultiIndex
        .reset_index(drop=False)           # -> columns domain, prompt, ci_low, ci_high
    )

    # 3️⃣  explicit two-column merge (no index involved)
    df = (
        df_point
          .merge(df_ci, on=["domain", "prompt"], how="left", validate="one_to_one")
          .assign(metric=m)
    )
    outs.append(df)

result = (
    pd.concat(outs, ignore_index=True)
      .merge(pvals, on=["metric", "domain"], how="left")  
      .set_index(["metric", "domain", "prompt"])
      .sort_index()
)

##############################################################################
# 7 ─── Inspect / export ────────────────────────────────────────────────────
##############################################################################

print(result)                   # or result.loc["balanced_accuracy"]

# CSV for the manuscript:
out_path = ROOT / f"bootstrap_metrics_by_prompt_B{BOOT_ITERATIONS}_pvals_vsBaseline.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)   # no error if already there
result.to_csv(out_path, float_format="%.5f", index=True)
print(f"✔ Saved: {out_path}")
