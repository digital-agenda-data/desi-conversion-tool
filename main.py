#!/usr/bin/env python3
"""
DESI Conversion Tool
Extracts and processes data from Excel files in .input/ folder
and saves processed outputs to .output/ folder.
"""

import pandas as pd
import re
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

    def identify_file_type(self, file_path: Path) -> str:
        """
        Identify the type of input file based on filename or content.
        """
        filename = file_path.name.lower()
        file_types = []

        for file_type, rules in config.FILE_TYPE_RULES.items():
            if re.search(rules["filename_pattern"], filename, re.IGNORECASE):
                file_types.append(file_type)
        if len(file_types) == 0:
            raise ValueError(f"Unknown file type: '{file_path.name}'")
        return file_types

    def extract_reporting_year(self, file_path: Path) -> Optional[int]:
        """Extract reporting year from input file name if present."""
        import re

        match = re.search(r"(20\d{2})", file_path.stem)
        if match:
            return int(match.group(1))
        return None

    def process_broadband(self, file_path: Path, reporting_year: Optional[int] = None) -> Dict[str, pd.DataFrame]:
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
        df = df[df["Geography level"].isin(rules["breakdown_mapping"].keys())]

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

        # Map country names to codes and rename column
        df_long["country"] = df_long["Country"].map(config.EU27_COUNTRIES)

        # Map breakdown values
        df_long["breakdown"] = df_long["Geography level"].map(rules["breakdown_mapping"])

        # Add indicator column using specific mappings
        df_long["indicator"] = df_long["Metric"].map(config.INDICATOR_MAPPINGS)
        # Only keep metrics that have explicit output mappings
        df_long = df_long.dropna(subset=["indicator"])

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
        result = {}
        common_rules = config.PROCESSING_RULES["common"]
        for indicator in df_long["indicator"].unique():
            indicator_df = df_long[df_long["indicator"] == indicator].copy()

            # Reorder columns
            indicator_df = indicator_df[common_rules["output_columns"]]

            # Sort the data
            indicator_df = indicator_df.sort_values(by=common_rules["sorting"], ascending=common_rules["sorting_ascending"])

            result[indicator] = indicator_df

        return result

    def process_egovernment(self, file_path: Path, reporting_year: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Process eGovernment files and return a dictionary of indicator-specific DataFrames.
        """
        print(f"Processing eGovernment {reporting_year} file: {file_path.name}")

        rules = config.PROCESSING_RULES["egovernment"]

        period_value = f"desi_{reporting_year}"
        reference_period_value = reporting_year - 1

        # Read the specific sheet
        df = pd.read_excel(file_path, sheet_name=rules["sheet_name"], header=None)

        # Find indicator positions dynamically
        indicator_positions = {}
        for i, row in df.iterrows():
            cell_value = row[3]  # Column D
            # if pd.notna(cell_value) and cell_value in rules["indicators"]:
            if pd.notna(cell_value) and cell_value in config.EGOVERNMENT_INDICATORS.keys():
                indicator_positions[cell_value] = i

        print(f"Found {len(indicator_positions)} indicators: {list(indicator_positions.keys())}")

        result = {}

        # Process each indicator
        for indicator_name, row_idx in indicator_positions.items():
            # Skip the description row and find the data start
            start_row = row_idx + 1

            # Find the end of this indicator's data (next indicator or end of file)
            next_indicators = [pos for pos in indicator_positions.values() if pos > row_idx]
            end_row = min(next_indicators) if next_indicators else len(df)

            # Extract data for this indicator
            indicator_data = []

            # Derive breakdown mapping for this indicator
            breakdown_mapping = config.EGOVERNMENT_INDICATORS[indicator_name]["breakdown_mappings"]

            # Prepare effective breakdown mapping for column index values
            breakdowns = {}
            for col_idx in rules["value_columns"]:
                col_letter = chr(65 + col_idx)  # 0 -> A, 1 -> B, etc.
                breakdowns[col_idx] = breakdown_mapping[col_letter]

            # Parse rows as data rows when country code looks productive
            for i in range(start_row, end_row):
                country_value = df.iloc[i, rules["country_column"]]
                ## skip secondary heading rows that don't have a country value
                if pd.notna(country_value):
                    country_value = str(country_value).strip()
                    for col_idx, breakdown in breakdowns.items():
                        value = df.iloc[i, col_idx]
                        if pd.notna(value):
                            indicator_data.append(
                                {
                                    "country": config.EU27_COUNTRIES.get(country_value, country_value),
                                    "breakdown": breakdown,
                                    "value": float(value),
                                }
                            )

            indicator_code = config.INDICATOR_MAPPINGS[indicator_name]
            common_rules = config.PROCESSING_RULES["common"]
            if indicator_data:
                # Create DataFrame for this indicator
                indicator_df = pd.DataFrame(indicator_data)

                # Add required columns
                indicator_df["period"] = period_value
                indicator_df["reference_period"] = reference_period_value
                indicator_df["indicator"] = indicator_code
                indicator_df["unit"] = rules["unit_value"]
                indicator_df["flags"] = None
                indicator_df["remarks"] = None

                # Reorder columns
                indicator_df = indicator_df[common_rules["output_columns"]]

                # Sort the data
                indicator_df = indicator_df.sort_values(by=common_rules["sorting"], ascending=common_rules["sorting_ascending"])

                result[indicator_code] = indicator_df
                print(f"Extracted {len(indicator_df)} rows for {indicator_name} -> {indicator_code}")

        return result


    def egov_kpi(self, file_path: Path, reporting_year: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Process eGovernment KPI files and return a dictionary of metric-specific DataFrames
        in the transformed long format.
        """
        print(f"Processing eGovernment KPI file: {file_path.name}")

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

    def save_indicators(self, df: pd.DataFrame, indicator: str, reporting_year: Optional[int] = None):
        """Save individual indicators to output directory."""
        date_str = datetime.now().strftime("%Y%m%d")
        pattern = config.OUTPUT_NAMING_PATTERNS[indicator]
        output_filename = pattern.format(date=date_str, year=reporting_year)
        output_path = self.output_dir / output_filename

        df.to_excel(output_path, index=False)
        print(f"Saved {indicator} output to: {output_path}")

    def save_consolidated_output(
        self,
        metric_dfs: Dict[str, pd.DataFrame],
        file_type: str,
        reporting_year: Optional[int] = None,
    ):
        """Create a consolidated DataFrame containing all metrics."""
        if not metric_dfs:
            return None

        # Combine all metric DataFrames into one
        consolidated_df = pd.concat(metric_dfs.values(), ignore_index=True)

        # Sort the consolidated data consistently
        common_rules = config.PROCESSING_RULES["common"]
        consolidated_df = consolidated_df.sort_values(
            by=common_rules["sorting"], ascending=common_rules["sorting_ascending"]
        )

        # Save the consolidated output to output directory
        date_str = datetime.now().strftime("%Y%m%d")
        year_str = f"_{reporting_year}" if reporting_year else ""
        output_filename = f"desi_{file_type}_consolidated{year_str}_{date_str}.xlsx"
        output_path = self.output_dir / output_filename

        consolidated_df.to_excel(output_path, index=False)
        print(f"Saved consolidated {file_type} output to: {output_path}")


    def process_file(self, file_path: Path):
        """Process a single Excel file."""
        try:
            file_types = self.identify_file_type(file_path)
            reporting_year = self.extract_reporting_year(file_path)
            for file_type in file_types:
                process_method = getattr(self, f"process_{file_type}")
                indicator_dfs = process_method(file_path, reporting_year)
                for indicator, df in indicator_dfs.items():
                    self.save_indicators(df, indicator, reporting_year)
                # Create and save consolidated output
                self.save_consolidated_output(indicator_dfs, file_type, reporting_year)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def run(self):
        """Main processing function."""
        excel_files = [f for f in self.input_dir.glob("*.xlsx") if not f.name.startswith("~$")]

        print(f"Found {len(excel_files)} Excel file(s) to process")

        for file_path in excel_files:
            print(f"\nFound file: {file_path.name}")
            self.process_file(file_path)


def main():
    tool = DESIConversionTool()
    tool.run()


if __name__ == "__main__":
    main()
