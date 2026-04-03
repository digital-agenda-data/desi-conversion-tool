# eGovernment Survey Data Processing

This document describes the processing rules and specifications for **eGovernment Survey** input files (eGovernment benchmark data from the European Commission).

## File Type Identification

**File Type:** "egovernment" (identified by keywords: "eGovernment")

**Filename Validation Pattern:** `eGovernment_YYYY.xlsx` (case insensitive, where YYYY is the reporting year)

## Input Processing

- **Source Sheet:** "8. DESI & Digital Decade" from Excel files
- **Data Structure:** Vertical format with countries in rows, multiple value columns for different breakdowns
- **Time Range:** Single year data (2025 for current files)
- **Country Coverage:** EU27 countries + EU27 aggregate (mapped to "EU")

## Data Transformations

### Dynamic Indicator Detection

- **Scanning Method:** Searches column D for exact indicator names to locate data sections
- **Flexible Positioning:** Indicator positions can vary between files due to explanatory text insertions
- **Automatic Detection:** Processes all configured indicators found in the file

### Breakdown Structure

Each indicator has explicit breakdown mappings for the data columns:

**Default Breakdowns (used by desi_dps_cit, desi_dps_biz, desi_us):**
- **Column D:** "total"
- **Column E:** "national"
- **Column F:** "cross_border"
- **Column G:** "service_design"

**Ad-hoc Services Breakdowns (used by desi_pff, desi_mff):**
- **Column D:** "all_egov_le"
- **Column E:** "national"
- **Column F:** "cross_border"
- **Column G:** "service_design"

**Custom Breakdowns (used by desi_tdpd - DESI Transparency):**
- **Column D:** "total"
- **Column E:** "service_delivery"
- **Column F:** "personal_data"
- **Column G:** "service_design"

Not all indicators use all columns - the actual breakdowns present depend on the data in the file.

### Data Extraction
- **Row Detection:** Identifies data rows by checking for valid country codes in column B
- **Value Validation:** Converts values to numeric, skips invalid/non-numeric entries
- **Country Mapping:** Maps "AVERAGE_EU27" to "EU" for consistency with other datasets

## Output Format

**Standard Columns:** period, reference_period, country, indicator, breakdown, unit, value, flags, remarks

**Key Differences from Broadband:**
- **Unit:** "egov_score" (instead of "pc_hh")
- **Breakdowns:** "total", "national", "cross_border" (instead of geographic levels)
- **Single Year:** Fixed reference_period of 2025

**Sorting:** reference_period DESC, country ASC, breakdown ASC

**File Naming:** desi_{indicator}_2026_{date}.xlsx (includes reporting year from filename)

## Indicators Processed

The following eGovernment indicators are extracted:

- **desi_dps_cit** → Digital Decade - Public services for citizens
- **desi_dps_biz** → Digital Decade - Digital public services for businesses
- **desi_pff** → DESI Pre-filled forms
- **desi_tdpd** → DESI Transparency
- **desi_us** → DESI User Support (has multiple breakdowns)
- **desi_mf** → DESI Mobile Friendliness

## Consolidated Output

**File Name:** desi_egovernment_consolidated_2026_{date}.xlsx

**Content:** All eGovernment indicators combined into one dataset

**Row Count:** Sum of all individual indicator file rows

**Breakdown Coverage:** Includes all available breakdowns (total, national, cross_border) for each indicator

## Example Output

### Individual Indicator File (desi_us_2026_20260325.xlsx)
```
period     reference_period  country  indicator  breakdown      unit       value  flags  remarks
desi_2026         2025         AT     desi_us    total        egov_score   93.65   NaN    NaN
desi_2026         2025         AT     desi_us    national     egov_score   98.41   NaN    NaN
desi_2026         2025         AT     desi_us    cross_border egov_score   88.89   NaN    NaN
desi_2026         2025         BE     desi_us    total        egov_score   92.86   NaN    NaN
...
```

### Consolidated File (desi_egovernment_consolidated_2026_20260325.xlsx)
```
period     reference_period  country  indicator     breakdown       unit      value  flags  remarks
desi_2026         2025         AT     desi_dps_biz  total         egov_score  83.73   NaN    NaN
desi_2026         2025         AT     desi_dps_cit  total         egov_score  88.80   NaN    NaN
desi_2026         2025         AT     desi_pff      total         egov_score  82.88   NaN    NaN
desi_2026         2025         AT     desi_tdpd     total         egov_score  77.66   NaN    NaN
desi_2026         2025         AT     desi_us       total         egov_score  93.65   NaN    NaN
desi_2026         2025         AT     desi_us       national      egov_score  98.41   NaN    NaN
desi_2026         2025         AT     desi_us       cross_border  egov_score  88.89   NaN    NaN
desi_2026         2025         AT     desi_mf       total         egov_score  99.75   NaN    NaN
...
```

## Data Quality

- **Dynamic Processing:** Adapts to varying row positions and explanatory text insertions
- **Multiple Breakdowns:** Handles indicators with different numbers of breakdown columns
- **Value Validation:** Filters out non-numeric values and invalid entries
- **Country Coverage:** Processes all EU27 countries plus EU aggregate
- **Consistent Output:** Maintains standardized DESI format across all indicators

## Configuration

Processing rules are defined in `config.py` under the "egovernment" key in `PROCESSING_RULES`. Key configuration elements:

- Sheet name and scanning parameters
- Indicator name mappings
- Breakdown column mappings
- Value column specifications
- Output column ordering and sorting rules