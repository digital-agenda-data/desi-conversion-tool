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

Three score labels are recognized and processed with specific aggregation rules:

#### 1. "1.1 Digital Public Services"
**Processing Type:** Individual events + total average

**Output Breakdowns:**
- Individual event breakdowns (e.g., egov_le_economic, egov_le_health, etc.)
- "total" breakdown containing the average of all life events in each group

**Aggregation Logic:**
- For each country and life event: extract individual value from raw data
- Create separate row for each event that exists in the data
- Calculate average across all life events in the group for "total" row

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=egov_le_economic, value=87.50
country=AT, indicator=desi_dps_biz, breakdown=egov_le_startup, value=85.00
country=AT, indicator=desi_dps_biz, breakdown=total, value=86.25 (average of economic and startup)

country=AT, indicator=desi_dps_cit, breakdown=egov_le_health, value=75.60
country=AT, indicator=desi_dps_cit, breakdown=egov_le_career, value=78.90
... (other 5 citizen events)
country=AT, indicator=desi_dps_cit, breakdown=total, value=76.50 (average of all 7)
```

#### 2. "1.1.1 Online Availability"
**Processing Type:** Average with "national" breakdown

**Output Breakdowns:**
- "national" breakdown containing the average of all life events

**Aggregation Logic:**
- Calculate average across all life events in each group
- Single "national" row per country per indicator

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=national, value=86.25
country=AT, indicator=desi_dps_cit, breakdown=national, value=76.50
```

#### 3. "1.1.2 Cross-border Online Availability"
**Processing Type:** Average with "cross_border" breakdown

**Output Breakdowns:**
- "cross_border" breakdown containing the average of all life events

**Aggregation Logic:**
- Calculate average across all life events in each group
- Single "cross_border" row per country per indicator

**Example:**
```
country=AT, indicator=desi_dps_biz, breakdown=cross_border, value=86.25
country=AT, indicator=desi_dps_cit, breakdown=cross_border, value=76.50
```

## Data Extraction Pipeline

1. **Read Input File:** Load Excel file with dynamically constructed sheet name
2. **Extract Rows:** Filter to data starting from row 7, extract country, score_label, and 9 breakdowns
3. **Map Countries:** Convert country names/codes to EU27 codes, filter to valid EU27 countries
4. **Melt Breakdown Columns:** Convert 9 breakdown columns to long format (75+ rows per country per score label)
5. **Map Breakdown Codes:** Convert life event labels to DESI codes
6. **Filter Score Labels:** Pre-filter to only recognized score labels
7. **Apply Transformations:** Process each score label with its specific aggregation rules
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
- **Breakdowns per score label:**
  - "1.1 Digital Public Services": 3 breakdowns (egov_le_economic, egov_le_startup, total)
  - "1.1.1 Online Availability": 1 breakdown (national)
  - "1.1.2 Cross-border Online Availability": 1 breakdown (cross_border)
- **Total breakdowns per country:** 5 (economic, startup, total, national, cross_border)
- **Expected rows:** 28 countries × 5 breakdowns = 140 rows (for all 3 score labels combined)

### desi_dps_cit (Digital Public Services - Citizens)
- **Breakdowns per score label:**
  - "1.1 Digital Public Services": 8 breakdowns (7 individual life events + total)
  - "1.1.1 Online Availability": 1 breakdown (national)
  - "1.1.2 Cross-border Online Availability": 1 breakdown (cross_border)
- **Total breakdowns per country:** 10 (7 events + total + national + cross_border)
- **Expected rows:** 28 countries × 10 breakdowns = 280 rows (for all 3 score labels combined)

## Consolidated Output

**File Name:** desi_egov_kpi_consolidated_{year}_{date}.xlsx

**Content:** All score label transformations combined for both desi_dps_biz and desi_dps_cit

**Row Count:** 140 (business) + 280 (citizen) = 420 rows per year

**Breakdown Coverage:** Includes all 5 business breakdowns and 10 citizen breakdowns

## Example Output

### Individual Indicator File (desi_dps_biz_20260406.xlsx)
```
period     reference_period  country  indicator  breakdown          unit       value  flags  remarks
desi_2026         2025         AT     desi_dps_biz  egov_le_economic   egov_score  87.50   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  egov_le_startup    egov_score  85.00   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  total              egov_score  86.25   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  national           egov_score  86.30   NaN    NaN
desi_2026         2025         AT     desi_dps_biz  cross_border       egov_score  85.95   NaN    NaN
desi_2026         2025         BE     desi_dps_biz  egov_le_economic   egov_score  88.25   NaN    NaN
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
desi_2026         2025         AT     desi_dps_cit  total             egov_score  76.10   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  national          egov_score  76.35   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  cross_border      egov_score  75.85   NaN    NaN
desi_2026         2025         BE     desi_dps_cit  egov_le_health    egov_score  77.80   NaN    NaN
...
```

## Consolidated Output (desi_egov_kpi_consolidated_2026_20260406.xlsx)
Combines both desi_dps_biz and desi_dps_cit data into a single file with 420 rows total, sorted by reference_period, country, indicator, and breakdown.
