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

**Total and type of user (used by desi_us):**
- **Column D:** "egov_le_all"
- **Column E:** "national"
- **Column F:** "cross_border"

**Total only (used by desi_pff, desi_mf):**
- **Column D:** "egov_le_all"

**Total and custom breakdowns (used by desi_tdpd - DESI Transparency):**
- **Column D:** "egov_le_all"
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

**Sorting:** reference_period DESC, country ASC, breakdown ASC

**File Naming:** desi_{indicator}_2026_{date}.xlsx (includes reporting year from filename)

## Indicators Processed

The following eGovernment indicators are extracted:

- **desi_dps_cit** → Digital Decade - Public services for citizens *(now processed via egov_kpi pipeline)*
- **desi_dps_biz** → Digital Decade - Digital public services for businesses *(now processed via egov_kpi pipeline)*
- **desi_pff** → DESI Pre-filled forms
- **desi_tdpd** → DESI Transparency
- **desi_us** → DESI User Support (has multiple breakdowns)
- **desi_mf** → DESI Mobile Friendliness

**Note:** `desi_dps_biz` and `desi_dps_cit` indicators are now processed through the `egov_kpi` pipeline instead of the `egovernment` pipeline. The `egov_kpi` pipeline provides more detailed breakdowns by life events and computes aggregated totals from national and cross-border scores.

## Consolidated Output

**File Name:** desi_egovernment_consolidated_2026_{date}.xlsx

**Content:** All eGovernment indicators combined into one dataset

**Row Count:** Sum of all individual indicator file rows

**Breakdown Coverage:** Includes all available breakdowns (egov_le_all, national, cross_border) for each indicator

## Example Output

### Individual Indicator File (desi_us_2026_20260325.xlsx)
```
period     reference_period  country  indicator  breakdown      unit       value  flags  remarks
desi_2026         2025         AT     desi_us    egov_le_all  egov_score   93.65   NaN    NaN
desi_2026         2025         AT     desi_us    national     egov_score   98.41   NaN    NaN
desi_2026         2025         AT     desi_us    cross_border egov_score   88.89   NaN    NaN
desi_2026         2025         BE     desi_us    egov_le_all  egov_score   92.86   NaN    NaN
...
```

### Consolidated File (desi_egovernment_consolidated_2026_20260325.xlsx)
```
period     reference_period  country  indicator     breakdown       unit      value  flags  remarks
desi_2026         2025         AT     desi_pff      egov_le_all   egov_score  82.88   NaN    NaN
desi_2026         2025         AT     desi_tdpd     egov_le_all   egov_score  77.66   NaN    NaN
desi_2026         2025         AT     desi_us       egov_le_all   egov_score  93.65   NaN    NaN
desi_2026         2025         AT     desi_us       national      egov_score  98.41   NaN    NaN
desi_2026         2025         AT     desi_us       cross_border  egov_score  88.89   NaN    NaN
desi_2026         2025         AT     desi_mf       egov_le_all   egov_score  99.75   NaN    NaN
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
