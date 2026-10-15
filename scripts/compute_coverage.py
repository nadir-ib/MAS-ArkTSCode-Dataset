#!/usr/bin/env python3
"""
Coverage extractor for the MAS-ArkTSCode dataset.

Reads mas_arkts_dataset.csv and writes machine-readable coverage tables
(CSV + JSON) into the coverage/ directory. All extraction is lexical
(regular expressions over the ArkTS source text); no compiler or parser
is invoked. The patterns used are listed in coverage/extractor_schema.json
so that every number can be re-derived independently.

Usage:
    python3 scripts/compute_coverage.py [--csv mas_arkts_dataset.csv] [--out coverage]

Dependencies: pandas, numpy, scipy
"""
import argparse, hashlib, json, os, re, collections
import numpy as np
import pandas as pd
from scipy import sparse

DECORATORS = ["@Entry", "@Component", "@ComponentV2", "@Reusable", "@Preview", "@CustomDialog",
              "@State", "@Prop", "@Link", "@Provide", "@Consume", "@Watch", "@ObjectLink", "@Observed",
              "@Track", "@Local", "@Param", "@Once", "@Event", "@Require", "@Monitor", "@Computed",
              "@StorageLink", "@StorageProp", "@LocalStorageLink", "@LocalStorageProp",
              "@PersistStorageProp", "@Builder", "@BuilderParam", "@Styles", "@Extend", "@AnimatableExtend",
              "@Concurrent", "@Sendable"]
LIFECYCLE = ["aboutToAppear", "aboutToDisappear", "onPageShow", "onPageHide", "onBackPress",
             "onDidBuild", "aboutToReuse", "aboutToRecycle", "onWillApplyTheme"]
ARKUI_COMPONENTS = ["Column", "Row", "Stack", "Flex", "RelativeContainer", "GridRow", "GridCol",
                    "Text", "Button", "Image", "TextInput", "TextArea", "Search", "Toggle", "Checkbox",
                    "CheckboxGroup", "Radio", "Slider", "Progress", "LoadingProgress", "Rating", "Select",
                    "DatePicker", "TimePicker", "TextPicker", "Divider", "Blank", "Span", "ImageSpan",
                    "RichText", "List", "ListItem", "ListItemGroup", "Grid", "GridItem", "Scroll", "Swiper",
                    "Tabs", "TabContent", "Navigation", "NavDestination", "NavRouter", "Navigator", "Refresh",
                    "WaterFlow", "FlowItem", "Panel", "SideBarContainer", "Badge", "Counter", "Marquee",
                    "QRCode", "Web", "Video", "XComponent", "Canvas", "Circle", "Rect", "Line", "Path",
                    "Polygon", "Polyline", "Ellipse", "Shape", "Gauge", "DataPanel", "Menu", "MenuItem",
                    "Stepper", "StepperItem", "AlphabetIndexer", "PatternLock", "Hyperlink", "SymbolGlyph",
                    "ForEach", "LazyForEach", "Repeat"]
CONTROL_FLOW = {
    "if_statement": r"\bif\s*\(",
    "else_clause": r"\belse\b",
    "for_loop": r"\bfor\s*\(",
    "while_loop": r"\bwhile\s*\(",
    "switch_statement": r"\bswitch\s*\(",
    "ternary_operator": r"\?[^.?:]+:",
    "try_catch": r"\btry\s*\{",
    "async_function": r"\basync\b",
    "await_expression": r"\bawait\b",
    "promise_usage": r"\bPromise\b",
    "arrow_function": r"=>",
    "class_declaration": r"\bclass\s+[A-Za-z_]\w*",
    "interface_declaration": r"\binterface\s+[A-Za-z_]\w*",
    "enum_declaration": r"\benum\s+[A-Za-z_]\w*",
    "type_alias": r"\btype\s+[A-Za-z_]\w*\s*=",
    "generic_type_argument": r"\b(?:Array|Map|Set|Promise|Record|Partial|Readonly)<",
    "type_annotation": r"[A-Za-z_]\w*\s*:\s*(?:string|number|boolean|void|any|[A-Z]\w*)(?:\[\])?\b",
    "null_safety_operator": r"\?\.|\?\?",
    "spread_operator": r"\.\.\.",
    "template_literal": r"`[^`]*\$\{",
}
UI_PATTERNS = {
    "list_view": r"\b(?:List|LazyForEach)\s*\(",
    "list_detail_or_navigation": r"\b(?:router\.(?:pushUrl|push|back|replaceUrl)|Navigation|NavDestination|NavPathStack|Navigator)\b",
    "tabbed_interface": r"\bTabs\s*\(",
    "swiper_carousel": r"\bSwiper\s*\(",
    "grid_layout": r"\bGrid\s*\(",
    "scrollable_content": r"\bScroll\s*\(",
    "form_input": r"\b(?:TextInput|TextArea|Search|Checkbox|Radio|Toggle|Slider|Select|DatePicker|TimePicker)\s*\(",
    "dialog_or_toast": r"\b(?:promptAction\.\w+|AlertDialog|CustomDialogController|@CustomDialog)\b",
    "local_component_state": r"@State\b",
    "parent_child_state_sharing": r"@(?:Prop|Link|Provide|Consume|ObjectLink)\b",
    "app_or_persistent_storage": r"\b(?:AppStorage|LocalStorage|PersistentStorage|@StorageLink|@StorageProp|@LocalStorageLink|@LocalStorageProp|@PersistStorageProp)\b",
    "animation": r"\b(?:animateTo|animation\s*\(|\.transition\s*\(|animator)\b",
    "gesture_handling": r"\b(?:TapGesture|LongPressGesture|PanGesture|PinchGesture|RotationGesture|SwipeGesture|GestureGroup)\b",
    "resource_reference": r"\$r\s*\(",
    "conditional_rendering": r"\bif\s*\([^)]*\)\s*\{[^}]*\b(?:Text|Column|Row|Image|Button)\s*\(",
    "reusable_builder": r"@Builder\b",
}
IDENT = r"[A-Za-z_$][\w$]*"

def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)

def count_functions(src):
    body = strip_comments(src)
    methods = re.findall(r"^\s*(?:private\s+|public\s+|protected\s+|static\s+|async\s+)*(" + IDENT + r")\s*\([^()]*\)\s*(?::\s*[^{;]+)?\{", body, flags=re.M)
    methods = [m for m in methods if m not in ("if", "for", "while", "switch", "catch", "constructor")]
    arrows = len(re.findall(r"=>", body))
    return len(methods), arrows

def max_nesting(src):
    d = m = 0
    for ch in strip_comments(src):
        if ch == "{": d += 1; m = max(m, d)
        elif ch == "}": d = max(0, d - 1)
    return m

def normalize(src):
    s = strip_comments(src)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def shingles(s, k=5):
    toks = re.findall(r"[A-Za-z_$][\w$]*|\d+|[^\s\w]", s)
    return {hash(" ".join(toks[i:i + k])) for i in range(max(1, len(toks) - k + 1))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="mas_arkts_dataset.csv")
    ap.add_argument("--out", default="coverage")
    ap.add_argument("--near-dup-threshold", type=float, default=0.80)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    df = pd.read_csv(a.csv)
    code = df["final_code"].fillna("").astype(str)
    n = len(df)
    compiled = df["compilation_success"].astype(bool).values

    def table(counter_per_sample, names, fname, label):
        rows = []
        for name in names:
            occ = np.array([c.get(name, 0) for c in counter_per_sample])
            rows.append({label: name, "total_occurrences": int(occ.sum()),
                         "samples_with_at_least_one": int((occ > 0).sum()),
                         "share_of_samples_pct": round(100 * (occ > 0).mean(), 2),
                         "samples_with_at_least_one_compiled_only": int(((occ > 0) & compiled).sum())})
        t = pd.DataFrame(rows).sort_values("samples_with_at_least_one", ascending=False)
        t.to_csv(os.path.join(a.out, fname + ".csv"), index=False)
        return t

    # 1. decorators
    dec_counts = [collections.Counter(re.findall(r"@[A-Z][A-Za-z0-9]*", c)) for c in code]
    all_dec = sorted({d for c in dec_counts for d in c} | set(DECORATORS))
    t_dec = table(dec_counts, all_dec, "decorators", "decorator")
    t_dec = t_dec[t_dec.total_occurrences > 0]
    t_dec.to_csv(os.path.join(a.out, "decorators.csv"), index=False)

    # 2. lifecycle handlers
    lc_counts = [collections.Counter(m for m in re.findall(r"\b(" + "|".join(LIFECYCLE) + r")\s*\(", c)) for c in code]
    t_lc = table(lc_counts, LIFECYCLE, "lifecycle_handlers", "handler")

    # 3. imports / API namespaces
    imports = [re.findall(r"import\s+[^;\n]*?\s+from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]", c) for c in code]
    imp_counts = [collections.Counter(x or y for x, y in lst) for lst in imports]
    all_mods = sorted({m for c in imp_counts for m in c})
    t_imp = table(imp_counts, all_mods, "import_modules", "module")
    fam = [collections.Counter(("@kit" if m.startswith("@kit") else "@ohos." + m.split(".")[1] if m.startswith("@ohos.") and len(m.split(".")) > 1 else "other") for m in c.elements()) for c in imp_counts]
    all_fam = sorted({f for c in fam for f in c})
    t_fam = table(fam, all_fam, "import_families", "family")
    # co-occurrence of top modules
    top = list(t_imp.head(15)["module"])
    co = pd.DataFrame(0, index=top, columns=top, dtype=int)
    for c in imp_counts:
        present = [m for m in top if m in c]
        for i in present:
            for j in present:
                co.loc[i, j] += 1
    co.to_csv(os.path.join(a.out, "import_cooccurrence_top15.csv"))

    # 4. ArkUI built-in components
    comp_counts = [collections.Counter(m for m in re.findall(r"\b(" + "|".join(ARKUI_COMPONENTS) + r")\s*\(", c)) for c in code]
    t_comp = table(comp_counts, ARKUI_COMPONENTS, "arkui_components", "component")
    t_comp = t_comp[t_comp.total_occurrences > 0]
    t_comp.to_csv(os.path.join(a.out, "arkui_components.csv"), index=False)

    # 5. control flow & typing constructs
    cf_counts = [collections.Counter({k: len(re.findall(p, strip_comments(c))) for k, p in CONTROL_FLOW.items()}) for c in code]
    t_cf = table(cf_counts, list(CONTROL_FLOW), "control_flow_and_typing", "construct")

    # 6. UI patterns
    ui_counts = [collections.Counter({k: len(re.findall(p, c, flags=re.S)) for k, p in UI_PATTERNS.items()}) for c in code]
    t_ui = table(ui_counts, list(UI_PATTERNS), "ui_patterns", "pattern")

    # 7. size / complexity / style
    rows = []
    for sid, c in zip(df["sample_id"], code):
        lines = c.split("\n")
        nonblank = [l for l in lines if l.strip()]
        comment_lines = sum(1 for l in lines if l.strip().startswith("//")) + len(re.findall(r"/\*.*?\*/", c, flags=re.S))
        nm, na = count_functions(c)
        structs = len(re.findall(r"\bstruct\s+" + IDENT, c))
        rows.append({"sample_id": sid, "chars": len(c), "lines_total": len(lines), "lines_nonblank": len(nonblank),
                     "comment_lines": comment_lines, "comment_ratio_pct": round(100 * comment_lines / max(1, len(nonblank)), 2),
                     "methods": nm, "arrow_functions": na, "structs": structs,
                     "custom_component_instantiations": 0, "max_brace_nesting": max_nesting(c)})
    per = pd.DataFrame(rows)
    # custom component instantiations: struct names defined in the sample that are called elsewhere in it
    inst = []
    for c in code:
        names = re.findall(r"\bstruct\s+(" + IDENT + ")", c)
        k = 0
        for nme in names:
            k += max(0, len(re.findall(r"\b" + re.escape(nme) + r"\s*\(", c)) - 0)
        inst.append(k)
    per["custom_component_instantiations"] = inst
    per.to_csv(os.path.join(a.out, "size_complexity_per_sample.csv"), index=False)
    summ = per.drop(columns=["sample_id"]).describe().T[["mean", "std", "min", "50%", "max"]].round(2)
    summ.to_csv(os.path.join(a.out, "size_complexity_summary.csv"))

    # 8. consistency validation
    checks = {
        "rows": n,
        "sample_id_is_1_to_n": bool((df["sample_id"].values == np.arange(1, n + 1)).all()),
        "compilation_success_equals_hq_or_technical": bool(((df["high_quality_success"] | df["technical_success"]) == df["compilation_success"]).all()),
        "hq_implies_score_ge_7": bool((df.loc[df["high_quality_success"], "quality_score"] >= 7).all()),
        "technical_implies_score_lt_7": bool((df.loc[df["technical_success"], "quality_score"] < 7).all()),
        "failed_samples_have_score_0": bool((df.loc[~df["compilation_success"], "quality_score"] == 0).all()),
        "code_length_equals_len_final_code": bool((df["code_length"] == code.str.len()).all()),
        "line_count_equals_newline_count_plus_1": bool((df["line_count"] == code.str.count("\n") + 1).all()),
        "component_count_equals_regex_count": bool((df["component_count"] == code.str.count(r"@Component\b")).all()),
        "state_count_equals_regex_count": bool((df["state_count"] == code.str.count(r"@State\b")).all()),
        "import_count_equals_regex_count": bool((df["import_count"] == code.str.count(r"(?m)^\s*import\b")).all()),
        "enhanced_prompt_present_count": int(df["enhanced_prompt"].notna().sum()),
        "enhancement_attempted_true_count": int(df["enhancement_attempted"].sum()),
        "empty_final_code": int((code.str.len() == 0).sum()),
    }

    # 9. deduplication / near-duplicate control
    exact_prompt_dups = int(df.duplicated(subset="prompt").sum())
    exact_row_dups = int(df.duplicated().sum())
    norm = [normalize(c) for c in code]
    h_raw = [hashlib.sha256(c.encode()).hexdigest() for c in code]
    h_norm = [hashlib.sha256(s.encode()).hexdigest() for s in norm]
    exact_code_dups = n - len(set(h_raw)); norm_code_dups = n - len(set(h_norm))
    # near-duplicates: Jaccard over 5-token shingles via sparse incidence matrix
    sh = [shingles(s) for s in norm]
    vocab = {}
    rows_i, cols_j = [], []
    for i, s in enumerate(sh):
        for g in s:
            j = vocab.setdefault(g, len(vocab)); rows_i.append(i); cols_j.append(j)
    M = sparse.csr_matrix((np.ones(len(rows_i), dtype=np.int32), (rows_i, cols_j)), shape=(n, len(vocab)))
    inter = (M @ M.T).toarray()
    sizes = np.asarray(M.sum(axis=1)).ravel()
    union = sizes[:, None] + sizes[None, :] - inter
    jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    np.fill_diagonal(jac, 0.0)
    iu = np.triu_indices(n, 1)
    vals = jac[iu]
    thr = a.near_dup_threshold
    pairs = [(int(df.sample_id[i]), int(df.sample_id[j]), round(float(jac[i, j]), 4)) for i, j in zip(*np.where(np.triu(jac, 1) >= thr))]
    flagged = {p for pr in pairs for p in pr[:2]}
    hist = {f">= {t:.2f}": int((vals >= t).sum()) for t in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0)}
    dedup = {
        "method": "exact: SHA-256 of raw and of comment/whitespace-normalized final_code; near-duplicate: Jaccard similarity of 5-token shingle sets over normalized code, all pairs",
        "near_duplicate_threshold": thr,
        "records": n, "distinct_prompts": int(df["prompt"].nunique()),
        "exact_duplicate_prompts": exact_prompt_dups, "exact_duplicate_full_rows": exact_row_dups,
        "exact_duplicate_code_raw": exact_code_dups, "exact_duplicate_code_normalized": norm_code_dups,
        "near_duplicate_pairs_at_threshold": len(pairs), "records_in_at_least_one_near_duplicate_pair": len(flagged),
        "pair_count_by_jaccard_threshold": hist,
        "note": "The 60 prompts that appear twice are identical in every field including final_code (see README); they are counted under exact_duplicate_prompts, and their code pairs appear in pair_count_by_jaccard_threshold at 1.0 only if their final_code is byte-identical.",
    }
    pd.DataFrame(pairs, columns=["sample_id_a", "sample_id_b", "jaccard"]).sort_values("jaccard", ascending=False).to_csv(os.path.join(a.out, "near_duplicate_pairs.csv"), index=False)

    summary = {"source_csv": os.path.basename(a.csv), "records": n, "compiled_records": int(compiled.sum()),
               "consistency_checks": checks, "deduplication": dedup,
               "decorators_top": t_dec.head(10).to_dict(orient="records"),
               "lifecycle_handlers": t_lc.to_dict(orient="records"),
               "import_families": t_fam.to_dict(orient="records"),
               "arkui_components_top": t_comp.head(15).to_dict(orient="records"),
               "control_flow_and_typing": t_cf.to_dict(orient="records"),
               "ui_patterns": t_ui.to_dict(orient="records"),
               "size_complexity_summary": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in summ.to_dict(orient="index").items()}}
    json.dump(summary, open(os.path.join(a.out, "coverage_summary.json"), "w"), indent=2, ensure_ascii=False)
    schema = {"extraction_level": "lexical (regular expressions over source text); no parser or compiler is used, so construct counts are approximations of AST-level counts",
              "decorators_pattern": r"@[A-Z][A-Za-z0-9]*", "lifecycle_handlers": LIFECYCLE, "arkui_components": ARKUI_COMPONENTS,
              "import_pattern": r"import ... from '<module>' | import '<module>'", "control_flow_and_typing": CONTROL_FLOW, "ui_patterns": UI_PATTERNS,
              "size_complexity": {"methods": "named function/method headers followed by '{', excluding control keywords", "arrow_functions": "count of '=>'", "comment_lines": "lines starting with // plus /* */ blocks", "max_brace_nesting": "maximum depth of '{' nesting after comment removal", "custom_component_instantiations": "calls of struct names defined in the same sample"},
              "deduplication": dedup["method"], "columns_in_every_table": ["total_occurrences", "samples_with_at_least_one", "share_of_samples_pct", "samples_with_at_least_one_compiled_only"]}
    json.dump(schema, open(os.path.join(a.out, "extractor_schema.json"), "w"), indent=2)
    print(json.dumps({"records": n, "checks": checks, "dedup": {k: v for k, v in dedup.items() if k not in ("method", "note")}}, indent=2))

if __name__ == "__main__":
    main()
