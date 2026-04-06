# eGovernment KPI Survey Data Processing

This document describes the processing rules and specifications for **eGovernment KPI** input files (eGovernment benchmark KPI scores with breakdowns by life events).

## File Type Identification

**File Type:** "egov_kpi" (identified by keywords: "eGovernment")

**Filename Validation Pattern:** `eGovernment Benchmark YYYY.xlsx` (case insensitive, where YYYY is the reporting year)

## Input Processing

- **Source Sheet:** Dynamically constructed as `"1. Scores {YYYY}"` where YYYY is the reporting year extracted from filename
- **Data Structure:** Wide format with countries in column B, score labels in column C, and 9 life event breakdowns in columns G-O
- **Time Range:** Single year data per file (extracted from filename)
- **Country Coverage:** EU27 countries + EU27 aggregate (mapped to "EU")
- **Data Start Row:** Row 7 (index 6) - skips header and metadata rows

## Data Transformations

### Life Event Breakdowns

The 9 life events are standardized to DESI breakdown codes:

| Original Label | DESI Code |
|----------------|-----------|
| Economic | egov_le_economic |
| Health | egov_le_health |
| Moving | egov_le_moving |
| Justice | egov_le_justice |
| Transport | egov_le_transport |
| Business Start-Up | egov_le_startup |
| Career | egov_le_career |
| Family | egov_le_family |
| Studying | egov_le_studying |

### Indicator Grouping

Life events are grouped into two indicator types:

**Business Indicators (desi_dps_biz):**
- egov_le_economic
- egov_le_startup

**Citizen Indicators (desi_dps_cit):**
- egov_le_health
- egov_le_moving
- egov_le_justice
- egov_le_transport
- egov_le_career
- egov_le_family
- egov_le_studying

### Score Label Processing

Two score labels are recognized and processed with specific aggregation rules:

#### 1. "1.1.1 Online Availability"
**Processing Type:** National availability - average of life events

**Output Breakdowns:**
- "national" breakdown containing the average of all life events from this score label

**Aggregation Logic:**
- Calculate average across all life events in each group
- Single "national" row per country per indicator

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=national, value=98.44
country=AT, indicator=desi_dps_cit, breakdown=national, value=76.50
```

#### 2. "1.1.2 Cross-border Online Availability"
**Processing Type:** Cross-border availability - average of life events

**Output Breakdowns:**
- "cross_border" breakdown containing the average of all life events from this score label

**Aggregation Logic:**
- Calculate average across all life events in each group
- Single "cross_border" row per country per indicator

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=cross_border, value=76.94
country=AT, indicator=desi_dps_cit, breakdown=cross_border, value=75.85
```

#### Combined Processing for Individual Life Events and Total

**Individual Life Event Breakdowns:**
- Each life event gets its own breakdown containing the average of that event from both score labels
- Aggregation: `(value_from_1.1.1 + value_from_1.1.2) / 2`

**Total Breakdown:**
- "egov_le_biz" breakdown for desi_dps_biz containing the average of national and cross_border values
- "egov_le_cit" breakdown for desi_dps_cit containing the average of national and cross_border values
- Aggregation: `(national + cross_border) / 2`

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=egov_le_economic, value=82.22 (avg of 87.50 + 76.94)
country=AT, indicator=desi_dps_biz, breakdown=egov_le_startup, value=81.47 (avg of 85.00 + 77.94)
country=AT, indicator=desi_dps_biz, breakdown=egov_le_biz, value=87.69 (avg of 98.44 + 76.94)
country=AT, indicator=desi_dps_cit, breakdown=egov_le_cit, value=76.18 (avg of 76.50 + 75.85)
```

## Data Extraction Pipeline

1. **Read Input File:** Load Excel file with dynamically constructed sheet name
2. **Extract Rows:** Filter to data starting from row 7, extract country, score_label, and 9 breakdowns
3. **Map Countries:** Convert country names/codes to EU27 codes, filter to valid EU27 countries
4. **Filter Score Labels:** Pre-filter to only "1.1.1 Online Availability" and "1.1.2 Cross-border Online Availability"
5. **Melt Breakdown Columns:** Convert 9 breakdown columns to long format
6. **Map Breakdown Codes:** Convert life event labels to DESI codes
7. **Apply Transformations:** Process data using pandas groupby operations:
   - National: average of life events from 1.1.1
   - Cross-border: average of life events from 1.1.2
   - Individual events: average of each event from both score labels
   - Total: average of national and cross-border
8. **Combine Results:** Merge all transformations into single output per indicator
9. **Sort and Output:** Sort by reference_period DESC, country/indicator/breakdown ASC

## Output Format

**Standard Columns:** period, reference_period, country, indicator, breakdown, unit, value, flags, remarks

**Key Specifications:**
- **Unit:** "egov_score"
- **Period Format:** `desi_{year}` (e.g., "desi_2026")
- **Reference Period:** Automatically set to `{year} - 1` (e.g., 2025 for 2026 data)
- **Country Mapping:** EU27 country codes (AT, BE, BG, etc.) + EU aggregate

**Sorting Order:**
1. reference_period (descending)
2. country (ascending)
3. indicator (ascending)
4. breakdown (ascending)

## Output Indicators

Two main indicators are generated:

### desi_dps_biz (Digital Public Services - Businesses)
- **Breakdowns:**
  - "national": average of 2 life events from 1.1.1 Online Availability
  - "cross_border": average of 2 life events from 1.1.2 Cross-border Online Availability
  - "egov_le_economic": average of economic event from both score labels
  - "egov_le_startup": average of startup event from both score labels
  - "egov_le_biz": average of national and cross_border
- **Total breakdowns per country:** 5
- **Expected rows:** 28 countries × 5 breakdowns = 140 rows

### desi_dps_cit (Digital Public Services - Citizens)
- **Breakdowns:**
  - "national": average of 7 life events from 1.1.1 Online Availability
  - "cross_border": average of 7 life events from 1.1.2 Cross-border Online Availability
  - 7 individual life events: average of each event from both score labels
  - "egov_le_cit": average of national and cross_border
- **Total breakdowns per country:** 10 (national + cross_border + 7 events + egov_le_cit)
- **Expected rows:** 28 countries × 10 breakdowns = 280 rows

## Consolidated Output

**File Name:** desi_egov_kpi_consolidated_{year}_{date}.xlsx

**Content:** All transformations combined for both desi_dps_biz and desi_dps_cit

**Row Count:** 140 (business) + 280 (citizen) = 420 rows per year

**Breakdown Coverage:** Includes all 5 business breakdowns and 10 citizen breakdowns

## Example Output

### Individual Indicator File (desi_dps_biz_20260406.xlsx)
```
period     reference_period  country  indicator  breakdown          unit       value  flags  remarks
desi_2026         2025         AT     desi_dps_biz  egov_le_economic   egov_score  82.22   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  egov_le_startup    egov_score  81.47   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  national           egov_score  98.44   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  cross_border       egov_score  76.94   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  egov_le_biz        egov_score  87.69   NaN    NaN
desi_2026         2025         BE     desi_dps_biz  egov_le_economic   egov_score  83.15   NaN    NaN
...
```

### Individual Citizen Indicator File (desi_dps_cit_20260406.xlsx)
```
period     reference_period  country  indicator  breakdown          unit       value  flags  remarks
desi_2026         2025         AT     desi_dps_cit  egov_le_health    egov_score  75.60   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_moving    egov_score  72.40   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_justice   egov_score  78.90   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_transport egov_score  79.20   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_career    egov_score  74.80   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_family    egov_score  73.50   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_studying  egov_score  77.30   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  egov_le_cit       egov_score  76.10   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  national          egov_score  76.35   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  cross_border      egov_score  75.85   NaN    NaN
desi_2026         2025         BE     desi_dps_cit  egov_le_health    egov_score  77.80   NaN    NaN
...
```

## Consolidated Output (desi_egov_kpi_consolidated_2026_20260406.xlsx)
Combines both desi_dps_biz and desi_dps_cit data into a single file with 420 rows total, sorted by reference_period DESC, country ASC, indicator ASC, and breakdown ASC.
