# Reproducibility notes

This document records the configuration under which the MAS-ArkTSCode dataset was generated, as
reported in the accompanying paper. The framework source code is not public; the information below is
what is needed to interpret the records and to re-run an equivalent evaluation of the released code.

## Software and model versions

| Component | Version / identifier |
|---|---|
| ArkTS compiler | HarmonyOS SDK 5.0.0.71 (API version 12), DevEco Studio command-line tools (`hvigor`) |
| Generation and scoring model | DeepSeek V3, `deepseek/deepseek-chat-v3-0324`, accessed through the OpenRouter API; the same model serves all six agents |
| Multi-agent orchestration | Agno 1.7.11 |
| Retrieval store | Qdrant 1.12.5 (collection of ArkTS code snippets) |
| Embeddings | `mxbai-embed-large` served by Ollama 0.9.6 |
| Result store | MongoDB (workflow states, scores, timings) |
| Runtime | Python 3.12.3 |
| Package management for the compile project | ohpm |

## Workflow and bounds

Six agents, coordinated by a deterministic state machine: Code Analyzer → Code Generator → compiler →
(on failure) Error Analyzer → Code Fixer, repeated for at most **10 correction attempts**; on success the
Quality Scorer rates the code, and if the score is below the threshold the Prompt Enhancer rewrites the
prompt and the pipeline restarts, for at most **2 enhancement passes**. Retrieval supplies the two most
similar ArkTS examples from the Qdrant collection to the generator. The quality threshold is **7** on
the 1–10 scale.

Resulting record fields: `iteration_count` is the number of agent iterations recorded for the workflow;
`enhancement_attempted` marks records on which the Prompt Enhancer ran; `enhanced_prompt` holds the
rewritten prompt where one was stored.

## Compilation protocol

The generated code is written as the page file `entry/src/main/ets/pages/Index.ets` of a standard
DevEco Studio "Empty Ability" project and the module is built with the HarmonyOS hvigor build system
(`assembleHap`). A record is `compilation_success = true` when the build completes without error. A
clean build is run for every attempt; the project file is restored after each attempt so that
concurrent runs do not interfere. Compiler diagnostics are consumed by the Error Analyzer agent and were
not exported to the CSV.

## Quality scoring protocol

The Quality Scorer agent receives the prompt and the code and returns a JSON object with an integer
score 1–10 and per-criterion comments. Its role and instruction texts, reproduced verbatim from
Appendix A of the paper:

**Role**

```
You are an expert ArkTS/ArkUI Code Quality Analyst with deep knowledge of HarmonyOS
development best practices, performance optimization, and code quality standards.
You are a meticulous and impartial code reviewer bringing precision and fairness
to every evaluation, ensuring that all code meets the highest standards.
```

**Instructions**

```
You will receive:
- prompt: A natural-language description of desired ArkTS functionality (provided for context only)
- code: An ArkTS implementation attempting to fulfill that prompt

Your task is to evaluate the code on a scale of 1-10 based on:
1. Import correctness: Verify that all necessary imports for the code to function are present, and there are no unused or redundant imports.
2. Syntax correctness: Verify that the code is syntactically valid and does not contain syntax errors.
3. Logic correctness: Check if the code logically fulfills the requirements of the given prompt.
4. Readability and maintainability: Assess if the code is well-structured, uses meaningful variable names, and follows best practices for maintainability.

CRITICAL: Your output MUST be ONLY the raw JSON with:
- NO markdown formatting whatsoever
- NO triple backticks (```)
- NO language tags like ```json
- NO descriptions, explanations, or comments outside the JSON
- NO "Here's the evaluation:" or similar phrases

Output format:
You must output a valid JSON object with the following structure:
{
  "score": 1-10,
  "details": {
    "import_correctness": "Detailed comments about import correctness...",
    "syntax_correctness": "Detailed comments about syntax correctness...",
    "logic_correctness": "Detailed observations about logic correctness...",
    "readability": "Detailed feedback about readability and maintainability...",
    "suggestions": ["Suggestion 1", "Suggestion 2", "..."]
  }
}

```

Each record is scored once, in a single pass. Records that never compiled carry `quality_score = 0`.
`high_quality_success` is `compilation_success and quality_score >= 7`; `technical_success` is
`compilation_success and quality_score < 7`.

## Validation of the scorer

- **Automated validation**: a stratified random sample of 200 generated records (bins: score ≥ 8.0,
  6.0–7.9, < 6.0) was re-assessed with the same 1–10 rubric (mean 7.87 ± 0.74; correlation r = 0.89
  between the scores and objective measures such as compilation success, code length and API usage).
- **Human validation**: a stratified sample of 150 compiled records was rated independently by two
  HarmonyOS developers with more than three years of professional experience, on the same 1–10 rubric.
  Agreement between the automated score and the human mean: Pearson r = 0.84, Spearman ρ = 0.82,
  ICC(2,1) = 0.81 (all p < 0.001). The automated scores were on average 0.69 points higher than the human
  scores; the rank order was preserved. The study validates the ordering produced by the scorer, not the
  absolute high-quality rate.

## Recomputing the released statistics

```
python3 scripts/verify_statistics.py          # headline numbers, exits 0 when all match
python3 scripts/compute_coverage.py           # regenerates coverage/ (needs pandas, numpy, scipy)
md5sum -c checksums.md5                       # file integrity
```

All numbers in `README.md` and `dataset_schema.json` are derived from `mas_arkts_dataset.csv` by these
scripts. The timing, cost and baseline-comparison figures of the paper come from the workflow database
and from the baseline runs; they cannot be recomputed from this CSV.
