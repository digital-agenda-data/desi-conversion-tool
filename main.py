#!/usr/bin/env python3
"""
DESI Conversion Tool
Extracts and processes data from Excel files in .input/ folder
and saves processed outputs to .output/ folder.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import config


class DESIConversionTool:
    def __init__(self, input_dir: str = ".input", output_dir: str = ".output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def get_excel_files(self) -> List[Path]:
        """Get all Excel files from input directory."""
        return list(self.input_dir.glob("*.xlsx")) + list(self.input_dir.glob("*.xls"))

    def identify_file_type(self, file_path: Path) -> str:
        """
        Identify the type of input file based on filename or content.
        """
        filename = file_path.stem.lower()

        for file_type, rules in config.FILE_TYPE_RULES.items():
            if any(keyword.lower() in filename for keyword in rules["keywords"]):
                return file_type

        return "default"

    def extract_reporting_year(self, file_path: Path) -> Optional[int]:
        """Extract reporting year from input file name if present."""
        import re

        match = re.search(r"(20\d{2})", file_path.stem)
        if match:
            return int(match.group(1))
        return None

    def process_file_generic(self, df: pd.DataFrame, filename: str, file_type: str) -> pd.DataFrame:
        """
        Generic file processing using configured rules.
        """
        print(f"Processing {filename} as {file_type} file")

        if file_type not in config.PROCESSING_RULES:
            print(f"Warning: No processing rules defined for {file_type}")
            return df

        rules = config.PROCESSING_RULES[file_type]

        # Extract specified columns if defined
        if rules["columns_to_extract"]:
            available_columns = [col for col in rules["columns_to_extract"] if col in df.columns]
            if available_columns:
                df = df[available_columns]
            else:
                print(f"Warning: None of the specified columns {rules['columns_to_extract']} found in {filename}")

        # Apply transformations (placeholder for now)
        for transformation in rules["transformations"]:
            # Apply transformation logic here
            pass

        return df

    def process_broadband(self, file_path: Path) -> Dict[str, pd.DataFrame]:
        """
        Process broadband files and return a dictionary of metric-specific DataFrames
        in the transformed long format.
        """
        print(f"Processing broadband file: {file_path.name}")

        rules = config.PROCESSING_RULES["broadband"]

        # Validate that the expected sheet exists
        try:
            xl = pd.ExcelFile(file_path)
            if rules["sheet_name"] not in xl.sheet_names:
                raise ValueError(
                    f"Expected sheet '{rules['sheet_name']}' not found in broadband file '{file_path.name}'. Available sheets: {xl.sheet_names}"
                )
        except Exception as e:
            raise ValueError(f"Cannot read broadband file '{file_path.name}': {e}")

        column_names = rules["columns_to_extract"]
        header_peek = pd.read_excel(file_path, sheet_name=rules["sheet_name"], header=rules["header_row"], nrows=0)

        header_peek.columns = header_peek.columns.astype(str)

        # Validate that required columns are present
        missing_columns = [col for col in column_names if col not in header_peek.columns]
        if missing_columns:
            raise ValueError(f"Broadband file '{file_path.name}' is missing required columns: {missing_columns}")

        target_indexes = [header_peek.columns.get_loc(col) for col in column_names]

        df = pd.read_excel(
            file_path,
            sheet_name=rules["sheet_name"],
            header=rules["header_row"],
            names=column_names,
            usecols=target_indexes,
        )

        # Validate that we have some data rows
        if len(df) == 0:
            raise ValueError(f"Broadband file '{file_path.name}' contains no data rows")

        # Skip the header row that gets included in the data
        df = df[df["Country"] != "Country"]

        # Filter to EU27 countries only
        df = df[df["Country"].isin(config.EU27_COUNTRIES.keys())]

        # Filter to specified geography levels
        df = df[df["Geography level"].isin(rules["geography_levels"])]

        # Map country names to codes
        df["Country"] = df["Country"].map(config.EU27_COUNTRIES)

        # Pivot to long format
        df_long = df.melt(
            id_vars=["Country", "Metric", "Geography level"],
            value_vars=column_names[3:],
            var_name="reference_period",
            value_name="value",
        )

        # Filter out rows with invalid/missing values
        # Remove NaN, #N/A, and non-numeric values
        df_long = df_long.dropna(subset=["value"])  # Remove NaN values
        df_long["value"] = pd.to_numeric(
            df_long["value"], errors="coerce"
        )  # Convert to numeric, invalid values become NaN
        df_long = df_long.dropna(subset=["value"])  # Remove rows where conversion failed

        # Convert reference_period to int
        df_long["reference_period"] = df_long["reference_period"].astype(int)

        # Map breakdown values
        df_long["breakdown"] = df_long["Geography level"].map(rules["breakdown_mapping"])

        # Add indicator column using specific mappings
        df_long["indicator"] = df_long["Metric"].map(config.INDICATOR_MAPPINGS)

        # Add unit column
        df_long["unit"] = rules["unit_value"]

        # Convert values (multiply by 100 to get percentage)
        df_long["value"] = df_long["value"] * rules["value_multiplier"]

        # Add period column (desi_ + year + 1)
        df_long["period"] = rules["period_prefix"] + (df_long["reference_period"] + 1).astype(str)

        # Add empty flags and remarks columns
        df_long["flags"] = None
        df_long["remarks"] = None

        # Split by metric BEFORE final column operations
        # Only process metrics that have explicit output mappings
        result = {}
        broadband_mappings = config.OUTPUT_NAMING_PATTERNS["broadband"]

        for metric in df_long["Metric"].unique():
            if pd.notna(metric) and metric in broadband_mappings:
                metric_df = df_long[df_long["Metric"] == metric].copy()

                # Now do the final column operations for each metric
                column_mapping = {
                    "Country": "country",
                    "reference_period": "reference_period",
                    "indicator": "indicator",
                    "breakdown": "breakdown",
                    "unit": "unit",
                    "value": "value",
                    "period": "period",
                    "flags": "flags",
                    "remarks": "remarks",
                }
                metric_df = metric_df.rename(columns=column_mapping)
                metric_df = metric_df[rules["output_columns"]]

                # Sort the data
                metric_df = metric_df.sort_values(by=rules["sorting"], ascending=rules["sorting_ascending"])

                result[metric] = metric_df

        return result

    def process_egovernment(self, file_path: Path, reporting_year: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Process eGovernment files and return a dictionary of indicator-specific DataFrames.
        """
        print(f"Processing eGovernment file: {file_path.name}")

        # Validate filename format for eGovernment benchmark files
        import re

        # Standard pattern: "eGovernment_YYYY.xlsx" (case insensitive)
        expected_pattern = r"^eGovernment_\d{4}\.xlsx$"
        if not re.match(expected_pattern, file_path.name, re.IGNORECASE):
            raise ValueError(
                f"Invalid eGovernment filename format: '{file_path.name}'. Expected format: 'eGovernment_YYYY.xlsx' (case insensitive, where YYYY is a 4-digit year)."
            )

        rules = config.PROCESSING_RULES["egovernment"]

        # Determine period and reference_period based on reporting_year
        if reporting_year is not None:
            period_value = f"desi_{reporting_year}"
            reference_period_value = reporting_year - 1
        else:
            # Fallback to config values
            period_value = f"desi_{rules['reference_period'] + 1}"
            reference_period_value = rules["reference_period"]

        print(f"Using period: {period_value}, reference_period: {reference_period_value}")

        # Read the specific sheet
        df = pd.read_excel(file_path, sheet_name=rules["sheet_name"], header=None)

        # Find indicator positions dynamically
        indicator_positions = {}
        for i, row in df.iterrows():
            cell_value = row[3]  # Column D
            if pd.notna(cell_value) and cell_value in rules["indicators"]:
                indicator_positions[cell_value] = i

        print(f"Found {len(indicator_positions)} indicators: {list(indicator_positions.keys())}")

        # Log unusual entries in column D that may indicate new or changed indicators
        all_d_values = df[3].dropna().unique()
        unknown_titles = [
            v
            for v in all_d_values
            if isinstance(v, str)
            and v.strip()
            and v not in rules["indicators"]
            and ("DESI" in v or "Digital Decade" in v)
            and len(v.strip()) < 120
        ]
        if unknown_titles:
            print("WARNING: Found potential unknown indicator titles in column D:")
            for title in unknown_titles:
                print(f"  - {title}")

        result = {}

        # Process each indicator
        for indicator_name, row_idx in indicator_positions.items():
            indicator_code = rules["indicators"][indicator_name]
            print(f"Processing indicator: {indicator_name} -> {indicator_code}")

            # Find the end of this indicator's data (next indicator or end of file)
            next_indicators = [pos for pos in indicator_positions.values() if pos > row_idx]
            end_row = min(next_indicators) if next_indicators else len(df)

            # Extract data for this indicator
            indicator_data = []

            # Skip the description row and find the data start
            data_start_row = row_idx + 1

            # Derive breakdown mapping for this indicator, fallback to defaults
            indicator_specific = rules.get("indicator_breakdown_mappings", {}).get(indicator_name, {})
            default_breakdowns = rules["breakdown_mappings"]

            def column_to_letter(col_idx):
                return chr(65 + col_idx)  # 0 -> A, 1 -> B, etc.

            # Prepare effective breakdown mapping for column index values
            effective_breakdowns = {}
            for col_idx in rules["value_columns"]:
                col_letter = column_to_letter(col_idx)
                if col_letter in indicator_specific:
                    effective_breakdowns[col_idx] = indicator_specific[col_letter]
                elif col_letter in default_breakdowns:
                    effective_breakdowns[col_idx] = default_breakdowns[col_letter]

            # Find first valid country row for this indicator
            valid_countries = []
            for i in range(data_start_row, end_row):
                country_code = df.iloc[i, rules["country_column"]]
                if pd.notna(country_code) and str(country_code).strip() not in [
                    "",
                    "Country",
                ]:
                    valid_countries.append(i)
                    break

            if not valid_countries:
                print(
                    f"WARNING: No country data found for indicator {indicator_name} between rows {data_start_row + 1} and {end_row}"
                )

            # Parse rows as data rows when country code looks productive
            for i in range(data_start_row, end_row):
                country_code = df.iloc[i, rules["country_column"]]
                if pd.notna(country_code) and str(country_code).strip() not in [
                    "",
                    "Country",
                ]:
                    country_value = str(country_code).strip()
                    if (
                        not (len(country_value) == 2 and country_value.isalpha())
                        and country_value != rules["eu27_aggregate"]
                    ):
                        # Log shapes that are unexpected while still processing if values exist
                        has_val = any(pd.notna(df.iloc[i, col]) for col in rules["value_columns"])
                        if has_val:
                            print(
                                f"WARNING: row {i + 1} has non-standard country code '{country_value}' with numeric values"
                            )

                    for col_idx, breakdown in effective_breakdowns.items():
                        value = df.iloc[i, col_idx]
                        if pd.notna(value):
                            try:
                                # Try to convert to float
                                numeric_value = float(value)
                                indicator_data.append(
                                    {
                                        "country": country_value,
                                        "breakdown": breakdown,
                                        "value": numeric_value,
                                    }
                                )
                            except (ValueError, TypeError):
                                # Skip non-numeric values
                                print(f"WARNING: row {i + 1} has non-numeric value '{value}' in col {col_idx}")
                                continue

            if indicator_data:
                # Create DataFrame for this indicator
                indicator_df = pd.DataFrame(indicator_data)

                # Map EU27 aggregate
                indicator_df["country"] = indicator_df["country"].replace(rules["eu27_aggregate"], "EU")

                # Add required columns
                indicator_df["period"] = period_value
                indicator_df["reference_period"] = reference_period_value
                indicator_df["indicator"] = indicator_code
                indicator_df["unit"] = rules["unit_value"]
                indicator_df["flags"] = None
                indicator_df["remarks"] = None

                # Reorder columns
                indicator_df = indicator_df[rules["output_columns"]]

                # Sort the data
                indicator_df = indicator_df.sort_values(by=rules["sorting"], ascending=rules["sorting_ascending"])

                result[indicator_code] = indicator_df
                print(f"  Extracted {len(indicator_df)} rows for {indicator_code}")

        return result

    def process_file(self, file_path: Path):
        """Process a single Excel file."""
        try:
            file_type = self.identify_file_type(file_path)

            if file_type == "broadband":
                # Broadband files return multiple DataFrames (one per metric)
                metric_dfs = self.process_broadband(file_path)
                for metric, df in metric_dfs.items():
                    self.save_broadband_output(df, file_path.name, metric)
                # Create and save consolidated output
                self.create_consolidated_output(metric_dfs, file_path.name, file_type)
            elif file_type == "egovernment":
                # eGovernment files return multiple DataFrames (one per indicator)
                reporting_year = (
                    self.extract_reporting_year(file_path) or rules["reference_period"]
                    if (rules := config.PROCESSING_RULES.get("egovernment"))
                    else None
                )
                indicator_dfs = self.process_egovernment(file_path, reporting_year)
                for indicator, df in indicator_dfs.items():
                    self.save_egovernment_output(df, file_path.name, indicator, reporting_year)
                # Create and save consolidated output
                self.create_consolidated_output(indicator_dfs, file_path.name, file_type, reporting_year)
            else:
                # Other file types return a single DataFrame
                df = pd.read_excel(file_path)
                processed_df = self.process_file_generic(df, file_path.name, file_type)
                if processed_df is not None:
                    self.save_output(processed_df, file_path.name, file_type)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def generate_output_filename(self, input_filename: str, file_type: str) -> str:
        """
        Generate output filename based on input filename and type.
        """
        base_name = Path(input_filename).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        pattern = config.OUTPUT_NAMING_PATTERNS.get(file_type, config.OUTPUT_NAMING_PATTERNS["default"])

        return pattern.format(basename=base_name, timestamp=timestamp)

    def save_output(self, df: pd.DataFrame, input_filename: str, file_type: str):
        """Save processed data to output directory."""
        output_filename = self.generate_output_filename(input_filename, file_type)
        output_path = self.output_dir / output_filename

        df.to_excel(output_path, index=False)
        print(f"Saved output to: {output_path}")

    def save_broadband_output(self, df: pd.DataFrame, input_filename: str, metric: str):
        """Save broadband metric-specific output to output directory."""
        # Generate date string
        date_str = datetime.now().strftime("%Y%m%d")

        # Use the specific pattern for this metric
        if metric in config.OUTPUT_NAMING_PATTERNS["broadband"]:
            pattern = config.OUTPUT_NAMING_PATTERNS["broadband"][metric]
            output_filename = pattern.format(date=date_str)
        else:
            # This shouldn't happen since we only process metrics with mappings
            print(f"Warning: No output pattern defined for metric '{metric}'")
            return

        output_path = self.output_dir / output_filename

        df.to_excel(output_path, index=False)
        print(f"Saved {metric} output to: {output_path}")

    def save_egovernment_output(self, df: pd.DataFrame, input_filename: str, indicator: str, reporting_year: int):
        """Save eGovernment indicator-specific output to output directory."""
        # Generate date string
        date_str = datetime.now().strftime("%Y%m%d")

        # Use the specific pattern for this indicator
        if indicator in config.OUTPUT_NAMING_PATTERNS["egovernment"]:
            pattern = config.OUTPUT_NAMING_PATTERNS["egovernment"][indicator]
            output_filename = pattern.format(year=reporting_year, date=date_str)
        else:
            # This shouldn't happen since we only process indicators with mappings
            print(f"Warning: No output pattern defined for indicator '{indicator}'")
            return

        output_path = self.output_dir / output_filename

        df.to_excel(output_path, index=False)
        print(f"Saved {indicator} output to: {output_path}")

    def create_consolidated_output(
        self,
        metric_dfs: Dict[str, pd.DataFrame],
        input_filename: str,
        file_type: str = "broadband",
        reporting_year: Optional[int] = None,
    ):
        """Create a consolidated DataFrame containing all metrics."""
        if not metric_dfs:
            return None

        # Combine all metric DataFrames into one
        consolidated_df = pd.concat(metric_dfs.values(), ignore_index=True)

        # Sort the consolidated data consistently
        rules = config.PROCESSING_RULES[file_type]
        consolidated_df = consolidated_df.sort_values(by=rules["sorting"], ascending=rules["sorting_ascending"])

        # Save the consolidated output
        self.save_consolidated_output(consolidated_df, input_filename, file_type, reporting_year)

        return consolidated_df

    def save_consolidated_output(
        self,
        df: pd.DataFrame,
        input_filename: str,
        file_type: str = "broadband",
        reporting_year: Optional[int] = None,
    ):
        """Save consolidated output to output directory."""
        # Generate date string
        date_str = datetime.now().strftime("%Y%m%d")

        year_str = str(reporting_year) if reporting_year else ""

        if file_type == "egovernment":
            if year_str:
                output_filename = f"desi_egovernment_consolidated_{year_str}_{date_str}.xlsx"
            else:
                output_filename = f"desi_egovernment_consolidated_{date_str}.xlsx"
        else:
            output_filename = f"desi_broadband_consolidated_{date_str}.xlsx"

        output_path = self.output_dir / output_filename

        df.to_excel(output_path, index=False)
        print(f"Saved consolidated {file_type} output to: {output_path}")

    def run(self):
        """Main processing function."""
        excel_files = self.get_excel_files()

        if not excel_files:
            print(f"No Excel files found in {self.input_dir}")
            return

        print(f"Found {len(excel_files)} Excel file(s) to process")

        for file_path in excel_files:
            print(f"\nProcessing: {file_path.name}")
            self.process_file(file_path)


def main():
    tool = DESIConversionTool()
    tool.run()


if __name__ == "__main__":
    main()
