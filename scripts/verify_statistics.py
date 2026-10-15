#!/usr/bin/env python3
"""Recompute the headline statistics of the MAS-ArkTSCode dataset from the CSV and compare them
with the values stated in README.md and in the paper. Exit code 0 when all match."""
import sys, hashlib
import pandas as pd

csv = sys.argv[1] if len(sys.argv) > 1 else "mas_arkts_dataset.csv"
df = pd.read_csv(csv)
code = df["final_code"].fillna("")
compiled = df[df["compilation_success"]]
exp = {
    "records": (len(df), 6034),
    "distinct_prompts": (df["prompt"].nunique(), 5974),
    "repeated_prompts": (int(df.duplicated(subset="prompt").sum()), 60),
    "compiled": (len(compiled), 5347),
    "high_quality": (int(df["high_quality_success"].sum()), 5197),
    "technical": (int(df["technical_success"].sum()), 150),
    "failed": (int((~df["compilation_success"]).sum()), 687),
    "compilation_rate_pct": (round(100 * df["compilation_success"].mean(), 2), 88.61),
    "high_quality_rate_pct": (round(100 * df["high_quality_success"].mean(), 2), 86.13),
    "compilation_rate_distinct_prompts_pct": (round(100 * df.drop_duplicates("prompt")["compilation_success"].mean(), 2), 88.57),
    "high_quality_rate_distinct_prompts_pct": (round(100 * df.drop_duplicates("prompt")["high_quality_success"].mean(), 2), 86.06),
    "quality_mean_compiled": (round(compiled["quality_score"].mean(), 2), 7.86),
    "quality_std_compiled": (round(compiled["quality_score"].std(), 2), 0.95),
    "quality_median_compiled": (float(compiled["quality_score"].median()), 8.0),
    "quality_mean_all": (round(df["quality_score"].mean(), 2), 6.96),
    "quality_std_all": (round(df["quality_score"].std(), 2), 2.65),
    "iterations_mean": (round(df["iteration_count"].mean(), 2), 5.22),
    "iterations_std": (round(df["iteration_count"].std(), 2), 7.54),
    "iterations_max": (int(df["iteration_count"].max()), 32),
    "enhancement_attempted": (int(df["enhancement_attempted"].sum()), 1243),
    "enhanced_prompt_present": (int(df["enhanced_prompt"].notna().sum()), 1043),
    "code_length_mean": (round(df["code_length"].mean(), 1), 2060.8),
    "code_length_std": (round(df["code_length"].std(), 1), 934.6),
    "code_length_min_max": ((int(df["code_length"].min()), int(df["code_length"].max())), (140, 7317)),
    "distinct_final_code": (code.nunique(), 5405),
    "records_with_repeated_code": (int(code.duplicated(keep=False).sum()), 873),
}
ok = True
for k, (got, want) in exp.items():
    flag = "OK " if got == want else "MISMATCH"
    ok &= got == want
    print(f"{flag} {k}: computed={got} stated={want}")
print("md5(csv) =", hashlib.md5(open(csv, "rb").read()).hexdigest())
sys.exit(0 if ok else 1)
