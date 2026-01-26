# dicomHeterogeneity

This project evaluates how closely real-world DICOM metadata conforms to the DICOM standard and quantifies heterogeneity across institutions and manufacturers. It compares actual metadata against standard references (2025c/2014c) to compute tag presence, value presence, standardization rate, and value diversity.

## Structure

- `DicomStandardEvaluator/`
  - `DicomStandardEvaluator_example.ipynb`: evaluation walkthrough
  - `Evaluator/`
    - `DicomCodeStandardEvaluator.py`: main evaluator class
    - `DicomCodeStandardEvaluator_withoutVR.py`: evaluator variant without VR
    - `DicomCodeStandardEvaluator.md`: class description
- `DicomStandardRetrieval/`
  - `DicomStandardRetrieval_2014c.ipynb`: 2014c reference processing
- `files/`
  - `DicomStandardReference_2014c/`: 2014c reference Excel files
  - `DicomStandardReference_2025c/`: 2025c reference Excel files

## Quick Start

1. Prepare a Python environment
   - Recommended packages: `pandas`, `numpy`, `openpyxl`, `pyarrow`
2. Load standard references
   - Use the Excel files under `files/DicomStandardReference_2025c/`
3. Load metadata
   - Provide metadata as Parquet or a DataFrame
4. Run evaluation
   - See `DicomStandardEvaluator/DicomStandardEvaluator_example.ipynb`

## Input Schema

`df_metadata` (real-world DICOM metadata) required columns:
- `study_id`, `series_id`, `file_id`
- `IOD`: IOD derived from SOP Class UID
- `Tag`: DICOM Tag
- `Value`: Tag value
- `AttributeName` (recommended)
- `Manufacturer`, `ScannerModel` (optional)

`df_standard` (DICOM standard definition) required columns:
- `IOD`, `Tag`, `Attribute Name`, `Type`, `Type_Group`
- `Standard Terms` (Enumerated/Defined Terms)

## Key Metrics

- Tag presence rate: fraction of files where a tag exists
- Value presence rate: fraction of files with a value when the tag exists
- Value standardization rate: fraction matching Enumerated/Defined Terms
- Value diversity: number of unique values

## Example

```python
from Evaluator.DicomCodeStandardEvaluator import DicomCodeStandardEvaluator

evaluator = DicomCodeStandardEvaluator(df_metadata, df_standard)
rates_df, stats_df = evaluator.analyze_rates_with_stats(
    group_cols=['IOD', 'study_id']
)
```

## Reference

- DICOM standard: https://dicom.nema.org/medical/dicom/current/output/chtml/
