"""
Configuration and rules for DESI Conversion Tool
"""

# File type identification rules
FILE_TYPE_RULES = {
    "broadband": {
        # "keywords": ["broadband", "CCE", "connectivity"],
        "description": "Broadband coverage data files",
        "filename_pattern": r"(broadband|CCE|connectivity)",
    },
    "egovernment": {
        "keywords": ["eGovernment", "egov"],
        "description": "eGovernment benchmark data files (standard naming: eGovernment_YYYY.xlsx)",
        # Standard pattern: "eGovernment_YYYY.xlsx" (case insensitive)
        "filename_pattern": r"(eGovernment|egov).*_\d{4}\.xlsx$",
    },
    "egov_kpi": {
        "keywords": ["eGovernment", "egov"],
        "description": "eGovernment - KPIs only, with breakdowns by life event and multiple years",
        "filename_pattern": r"(eGovernment|egov).*_\d{4}\.xlsx$",
    }
}

# EU27 countries and their codes
EU27_COUNTRIES = {
    "Austria": "AT",
    "Belgium": "BE", 
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "EL",
    "Hungary": "HU",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Netherlands": "NL",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "EU27": "EU",
    "AVERAGE_EU27": "EU",
}

# eGovernment indicator configurations
EGOVERNMENT_INDICATORS = {
    "Digital Decade - Public services for citizens": {
        "indicator": "desi_dps_cit",
        "output_pattern": "desi_dps_cit_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "national",
            "F": "cross_border",
            "G": "n/a"
        }
    },
    "Digital Decade - Digital public services for businesses": {
        "indicator": "desi_dps_biz",
        "output_pattern": "desi_dps_biz_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "national",
            "F": "cross_border",
            "G": "n/a"
        }
    },
    "DESI Pre-filled forms": {
        "indicator": "desi_pff",
        "output_pattern": "desi_pff_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "n/a",
            "F": "n/a",
            "G": "n/a"
        }
    },
    "DESI Transparency": {
        "indicator": "desi_tdpd",
        "output_pattern": "desi_tdpd_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "service_delivery",
            "F": "personal_data",
            "G": "service_design"
        }
    },
    "DESI User Support": {
        "indicator": "desi_us",
        "output_pattern": "desi_us_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "national",
            "F": "cross_border",
            "G": "n/a"
        }
    },
    "DESI Mobile Friendliness": {
        "indicator": "desi_mf",
        "output_pattern": "desi_mf_{year}_{date}.xlsx",
        "breakdown_mappings": {
            "D": "total",
            "E": "n/a",
            "F": "n/a",
            "G": "n/a"
        }
    }
}

# Broadband metric configurations (combines indicator mapping and output naming)
BROADBAND_INDICATORS = {
    "FTTP": {
        "indicator": "desi_fttp",
        "output_pattern": "desi_fttp_{date}.xlsx"
    },
    "5G": {
        "indicator": "desi_5gcov",
        "output_pattern": "desi_5gcov_{date}.xlsx"
    },
    "5G in the 3.4–3.8\xa0GHz band": {
        "indicator": "desi_5gcov_3400_3800",
        "output_pattern": "desi_5gcov_3400_3800_{date}.xlsx"
    },
    "Fixed VHCN coverage (FTTP & DOCSIS 3.1+)": {
        "indicator": "desi_vhcn",
        "output_pattern": "desi_vhcn_{date}.xlsx"
    }
}

ALL_INDICATORS = {**EGOVERNMENT_INDICATORS, **BROADBAND_INDICATORS}

INDICATOR_MAPPINGS = {
    indicator_name: indicator_props["indicator"]
    for indicator_name, indicator_props in ALL_INDICATORS.items()
}

OUTPUT_NAMING_PATTERNS = {
    indicator_props["indicator"]: indicator_props["output_pattern"]
    for indicator_name, indicator_props in ALL_INDICATORS.items()
}

# Processing rules for each file type
PROCESSING_RULES = {
    "broadband": {
        "sheet_name": "Data (%)",
        "header_row": 6,  # 0-indexed, so row 7 in Excel
        "columns_to_extract": ["Country", "Metric", "Geography level", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        # year columns are pivoted in main.py based on their index in columns_to_extract [3:]
        "breakdown_mapping": {
            "Total": "total_pophh",
            "Rural": "hh_deg3"
        },
        "period_prefix": "desi_",
        "indicator_prefix": "desi_",
        "unit_value": "pc_hh",
        "value_multiplier": 100,  # Convert from decimal to percentage
    },
    "egovernment": {
        "sheet_name": "8. DESI & Digital Decade",
        "header_row": None,  # No fixed header, scan dynamically
        "country_column": 1,  # Column B (0-indexed)
        "value_columns": [3, 4, 5, 6],  # Columns D, E, F, G (0-indexed)
        "unit_value": "egov_score",
    },
    "egov_kpi": {
        "sheet_name": "1. Scores 2026",
        "year_row": 4,  # 0-indexed, so row 5 in Excel
        "header_row": 5,  # 0-indexed, so row 6 in Excel
        "country_column": 1,  # Column B (0-indexed)
        "value_columns": range(3, 4 + 2*11),
        "unit_value": "egov_score",
    },
    "common": {
        "output_columns": ["period", "reference_period", "country", "indicator", "breakdown", "unit", "value", "flags", "remarks"],
        "sorting": ["reference_period", "indicator", "country", "breakdown"],
        "sorting_ascending": [False, True, True, True],
    },
}

