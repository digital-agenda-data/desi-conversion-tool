# DESI Conversion Tool

A Python tool for extracting and processing data from Excel files with different processing rules for each file type, producing standardized output formats for DESI broadband indicators.

## Project Structure

```
.
├── main.py                    # Main application script
├── config.py                  # Configuration and processing rules
├── connectivity-survey.md     # Connectivity Survey data processing specs
├── egovernment-survey.md      # eGovernment Survey data processing specs
├── pyproject.toml             # Project dependencies
├── .input/                    # Input Excel files directory
├── .output/                   # Processed output files directory
└── .examples/                 # Example manually produced outputs
```

## Setup

### Dependencies

This project uses `pyproject.toml` to manage dependencies. The main dependencies are:

- `openpyxl` - For Excel file processing
- `pandas` - For data manipulation

### Installation

Choose one of the following installation methods:

#### Option 1: Using pip

```bash

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

#### Option 2: Using uv (recommended)

```bash
# Install uv if not already installed
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates virtual environment automatically)
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Adding New Dependencies

To add new dependencies to the project:

#### Using uv

```bash
uv add package-name
```

#### Using pip

```bash
pip install package-name
# Then update pyproject.toml manually or use pip-tools
```

### Usage

1. Place your Excel input files in the `.input/` directory.

2. Run the tool:

   ```bash
   python main.py
   ```

3. Processed output files will be created in the `.output/` directory.

## File Type Identification

The tool automatically identifies file types based on filename keywords defined in `config.py`. Currently supported types:

- **broadband**: Files containing "broadband", "CCE", or "connectivity" in the filename (Connectivity Survey data)
  - **Standard naming:** `broadband_YYYY.xlsx` (case insensitive)
- **egovernment**: Files containing "eGovernment" in the filename (eGovernment Survey data)
  - **Standard naming:** `eGovernment_YYYY.xlsx` (case insensitive)
- **default**: Any other files

For detailed processing specifications for each file type, see the respective documentation files:

- [Connectivity Survey Data](connectivity-survey.md)
- [eGovernment Survey Data](egovernment-survey.md)

## Output Format

All processed data follows a standardized DESI output format regardless of input file type:

**Standard Columns:** period, reference_period, country, indicator, breakdown, unit, value, flags, remarks

**Common Features:**

- Country codes use ISO 3166-1 alpha-2 format
- Values are converted to appropriate units (typically percentages)
- Invalid values (NaN, #N/A, non-numeric) are filtered out
- Consistent sorting: reference_period DESC, country ASC, breakdown ASC

## Output Naming

Output files are named using patterns defined in `config.py`. The default pattern includes:

- Original filename (without extension)
- File type
- Timestamp

Example: `processed_input_file_type1_20231201_143022.xlsx`

## Development

### Adding Support for New File Types

To add support for a new data source with different input format but same output structure:

1. Create a new documentation file (e.g., `new-source.md`) describing the processing specifications
2. Add identification rules in `FILE_TYPE_RULES` in `config.py`
3. Define processing rules in `PROCESSING_RULES` in `config.py`
4. Add output naming pattern in `OUTPUT_NAMING_PATTERNS` in `config.py`
5. Implement specific processing logic in `main.py` if needed
6. Update this README to reference the new documentation file

### Current Data Sources

- [Connectivity Survey Data](connectivity-survey.md) - Broadband coverage data from CCE datasets
- [eGovernment Survey Data](egovernment-survey.md) - eGovernment benchmark data from European Commission

## Examples

Place example output files in the `.examples/` directory to use as reference for expected results.
