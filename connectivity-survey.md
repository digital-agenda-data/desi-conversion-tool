# Connectivity Survey Data Processing

This document describes the processing rules and specifications for **Connectivity Survey** input files (broadband coverage data from CCE datasets).

## File Type Identification

**File Type:** "broadband" (identified by keywords: "broadband", "CCE", "connectivity")

## Input Processing

- **Source Sheet:** "Data (%)" from Excel files
- **Geographic Filter:** EU27 countries + EU27 aggregate
- **Geography Levels:** Both "Total" and "Rural" levels included
- **Time Range:** Data for years 2019-2025

## Data Transformations

### Pivot Operation

- **Input Format:** Wide format with Country + Year columns
- **Output Format:** Long format with one row per country/year/metric combination

### Column Mappings

- **Country Names:** Converted to ISO country codes (AT, BE, BG, etc.)
- **Geography Levels:**
  - "Total" → "total_pophh"
  - "Rural" → "hh_deg3"
- **Values:** Multiplied by 100 (decimal 0.918 → percentage 91.8)

### New Columns Added

- `period`: "desi_" + (year + 1) e.g., "desi_2025" for reference year 2024
- `reference_period`: The actual year (2019, 2020, etc.)
- `indicator`: "desi_" + cleaned metric name (e.g., "desi_fttp")
- `unit`: "pc_hh" for all rows
- `flags` & `remarks`: Empty columns

## Output Format

**Standard Columns:** period, reference_period, country, indicator, breakdown, unit, value, flags, remarks

**Sorting:** reference_period DESC, country ASC, breakdown ASC

**File Naming:** desi_{metric}_{date}.xlsx (e.g., desi_fttp_20260325.xlsx)

## Example Output (FTTP)

```
period     reference_period  country  indicator  breakdown   unit   value  flags  remarks
desi_2026         2025         AT     desi_fttp   hh_deg3    pc_hh  36.96   NaN    NaN
desi_2026         2025         AT     desi_fttp   total_pophh pc_hh  50.88   NaN    NaN
desi_2026         2025         BE     desi_fttp   hh_deg3    pc_hh   4.63   NaN    NaN
...
```

## Metrics Processed

The following broadband metrics are extracted into separate output files:

- **FTTP** → `desi_fttp_{date}.xlsx` (indicator: `desi_fttp`)
- **5G** → `desi_5gcov_{date}.xlsx` (indicator: `desi_5gcov`)
- **5G in the 3.4–3.8 GHz band** → `desi_5gcov_3400_3800_{date}.xlsx` (indicator: `desi_5gcov_3400_3800`)
- **Fixed VHCN coverage (FTTP & DOCSIS 3.1+)** → `desi_vhcn_{date}.xlsx` (indicator: `desi_vhcn`)

## Consolidated Output

In addition to individual metric files, a **consolidated broadband output file** is generated containing all metrics in a single dataset:

- **File Name:** `desi_broadband_consolidated_{date}.xlsx`
- **Content:** All broadband metrics combined into one comprehensive dataset
- **Row Count:** Sum of all individual metric file rows
- **Sorting:** Same as individual files (reference_period DESC, country ASC, breakdown ASC)
- **Purpose:** Provides a single comprehensive view of all broadband coverage data

### Example Consolidated Output

```
period     reference_period  country  indicator            breakdown   unit   value  flags  remarks
desi_2026         2025         AT     desi_vhcn            hh_deg3    pc_hh  42.05   NaN    NaN
desi_2026         2025         AT     desi_fttp            hh_deg3    pc_hh  36.96   NaN    NaN
desi_2026         2025         AT     desi_5gcov           hh_deg3    pc_hh  98.90   NaN    NaN
desi_2026         2025         AT     desi_5gcov_3400_3800 hh_deg3    pc_hh  53.22   NaN    NaN
...
```

## Data Quality

- **Invalid Value Filtering:** Rows with NaN, #N/A, or non-numeric values are automatically excluded
- **EU27 Coverage:** Only data for EU27 countries and EU aggregate is processed
- **Geographic Levels:** Both total population and rural household breakdowns included
- **Time Series:** Complete coverage from 2019 to 2025

## Configuration

Processing rules are defined in `config.py` under the "broadband" key in `PROCESSING_RULES`. Key configuration elements:

- Sheet name and header row specification
- Column extraction rules
- Country and geography filtering
- Value transformation multipliers
- Output column mappings and sorting rules
