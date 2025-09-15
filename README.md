# MAS-ArkTSCode Dataset

## Overview

The MAS-ArkTSCode dataset is a comprehensive collection of 6,034 ArkTS code samples generated using a multi-agent framework. This dataset addresses the critical data scarcity challenge for specialized programming languages like ArkTS (HarmonyOS development).

## Quick Start

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('mas_arkts_dataset.csv')

# Basic statistics
print(f"Dataset size: {len(df):,} samples")
print(f"Compilation success rate: {df['compilation_success'].mean():.1%}")
print(f"High-quality success rate: {df['high_quality_success'].mean():.1%}")
print(f"Mean quality score: {df['quality_score'].mean():.2f}")

# Filter high-quality samples
high_quality = df[df['high_quality_success'] == True]
print(f"High-quality samples: {len(high_quality):,}")
```

## Dataset Statistics

- **Total Samples**: 6,034
- **Compilation Success Rate**: 88.6%
- **High-Quality Success Rate**: 86.1%
- **Mean Quality Score**: 7.86 ± 0.95
- **Language**: ArkTS
- **Domain**: HarmonyOS Development

## Key Metrics (from Paper)

Based on the comprehensive evaluation in our paper:

- **Compilation Success Rate**: 88.6%
- **High-Quality Success Rate**: 86.1%
- **Mean Iterations**: ~5.22 ± 7.54 per sample
- **Enhancement Usage**: ~20.6% of samples
- **Human Correlation**: r=0.84 (automated vs human scoring)

## File Structure

```
MAS-ArkTSCode-Dataset/
├── mas_arkts_dataset.csv      # Main dataset (this file contains everything)
├── dataset_schema.json        # Field definitions and statistics
├── README.md                  # This file
├── LICENSE                    # Open source license
└── checksums.md5             # File integrity verification
```

## Dataset Fields

### Core Fields (4)
- **sample_id**: Sequential identifier (1-6034)
- **prompt**: Original natural language prompt
- **enhanced_prompt**: Enhanced prompt (if enhancement was used)
- **final_code**: Generated ArkTS code

### Success Metrics (4)
- **compilation_success**: Overall compilation success (boolean)
- **high_quality_success**: High-quality success (score ≥ 7.0)
- **technical_success**: Technical success (compiles but score < 7.0)
- **quality_score**: Overall quality score (1-10 scale)



### Processing Details (2)
- **iteration_count**: Number of iterations required
- **enhancement_attempted**: Whether prompt enhancement was used

### Code Characteristics (5)
- **code_length**: Code length in characters
- **line_count**: Number of lines
- **component_count**: Number of @Component decorators
- **state_count**: Number of @State decorators
- **import_count**: Number of import statements

## Usage Examples

### Filter by Quality
```python
# High-quality samples only
high_quality = df[df['quality_score'] >= 7.0]

# Successful compilations
successful = df[df['compilation_success'] == True]

# Enhanced samples
enhanced = df[df['enhancement_attempted'] == True]
```

### Analyze Code Characteristics
```python
# Code length distribution
df['code_length'].describe()

# Component usage
df['component_count'].value_counts()

# Quality vs iterations
df.groupby('iteration_count')['quality_score'].mean()
```

### Quality Analysis
```python
# Quality score analysis
df['quality_score'].describe()

# Quality by success type
high_quality = df[df['high_quality_success'] == True]['quality_score']
technical = df[df['technical_success'] == True]['quality_score']
print(f'High-quality samples: {high_quality.mean():.2f} ± {high_quality.std():.2f}')
print(f'Technical success samples: {technical.mean():.2f} ± {technical.std():.2f}')
```

## Data Quality

- **Compilation Verified**: All successful samples verified with ArkTS compiler
- **Quality Scored**: Multi-dimensional quality assessment (1-10 scale)
- **Human Validated**: 150 samples validated by ArkTS experts (r=0.84 correlation)
- **Deduplicated**: Hash-based deduplication applied
- **Error Analyzed**: Failed samples include error diagnostics

## Intended Use

### ✅ Appropriate Uses
- ArkTS code generation research
- LLM training and evaluation
- Educational applications
- Benchmarking specialized language models
- Academic research on code generation

### ❌ Inappropriate Uses
- Production code deployment without review
- Malicious code generation
- Applications outside ArkTS/HarmonyOS domain

## Limitations

- **Language Specific**: Designed specifically for ArkTS
- **Synthetic Data**: Generated code may not reflect all real-world constraints
- **Temporal**: Reflects ArkTS patterns as of dataset creation date
- **Bias**: May reflect biases from training data and generation process

## Citation

If you use this dataset in your research, please cite:

```bibtex
@article{mas_arkts_2025,
  title={MAS-ArkTSCode: A Multi-Agent Synthetic Dataset for ArkTS Code Generation},
  author={İbrahimoğlu, Nadir and Demirezen, Mustafa Umut},
  year={2025},
  note={Dataset available at: [DOI/URL to be added]}
}
```

## License

This dataset is released under [LICENSE_TYPE] license. See LICENSE file for details.

## Contact

For questions or issues regarding this dataset, please contact:
- Nadir İbrahimoğlu: nadiribrahimoglu@hotmail.com
- Mustafa Umut Demirezen: umut@demirezen.tech

---

**Dataset Version**: 1.0
**Creation Date**: 2025-09-15
**Total Size**: 6,034 samples
**Quality Assurance**: Compiler-verified, multi-agent generated, human-validated
