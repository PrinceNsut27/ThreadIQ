"""Dataset Acquisition and Verification Script for ThreadIQ.

This script checks for the presence of the required raw datasets:
1. Olist Brazilian E-Commerce Dataset (9 CSV files in data/raw/olist/)
2. Fashion Product Images Dataset (styles.csv in data/raw/fashion/)

It provides guidance on manual download as well as programmatic download via the Kaggle API.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.threadiq.config import (
    FASHION_FILES,
    FASHION_RAW_DIR,
    OLIST_FILES,
    OLIST_RAW_DIR,
)


def check_dataset_files(directory: Path, expected_files: list[str], dataset_name: str) -> dict:
    """Check if expected files exist in the target directory and return status."""
    print(f"\n==================================================")
    print(f"Checking {dataset_name} in: {directory}")
    print(f"==================================================")
    
    if not directory.exists():
        print(f"[!] Directory does not exist: {directory}")
        return {"exists": False, "found": [], "missing": expected_files}
    
    found = []
    missing = []
    for filename in expected_files:
        file_path = directory / filename
        if file_path.exists() and file_path.is_file():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            found.append((filename, size_mb))
            print(f"  [OK] {filename} ({size_mb:.2f} MB)")
        else:
            missing.append(filename)
            print(f"  [MISSING] {filename}")
            
    return {
        "exists": len(found) > 0,
        "complete": len(missing) == 0,
        "found": found,
        "missing": missing,
    }


def print_kaggle_setup_instructions():
    """Print instructions on configuring Kaggle credentials."""
    print("\n--------------------------------------------------")
    print("KAGGLE AUTHENTICATION & DOWNLOAD INSTRUCTIONS")
    print("--------------------------------------------------")
    print("To download datasets using the Kaggle API:")
    print("1. Log in to https://www.kaggle.com and navigate to 'Account Settings' -> 'API'.")
    print("2. Click 'Create New Token'. This downloads 'kaggle.json'.")
    print("3. Place 'kaggle.json' in your home directory:")
    print("   - Windows: C:\\Users\\<Your-Username>\\.kaggle\\kaggle.json")
    print("   - Linux/macOS: ~/.kaggle/kaggle.json")
    print("   OR set environment variables: KAGGLE_USERNAME and KAGGLE_KEY.")
    print("\nAlternatively, download manually via browser:")
    print("1. Olist Brazilian E-Commerce Dataset:")
    print("   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
    print(f"   Extract all 9 CSV files into: {OLIST_RAW_DIR}")
    print("\n2. Fashion Product Images Dataset:")
    print("   https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset")
    print(f"   Extract 'styles.csv' into: {FASHION_RAW_DIR}")
    print("--------------------------------------------------\n")


def try_kaggle_download():
    """Attempt download using the kaggle package if credentials exist."""
    try:
        import kaggle
        print("[*] Kaggle Python package is available. Authenticating...")
        kaggle.api.authenticate()
        print("[+] Kaggle authentication successful.")
        
        # Download Olist
        print(f"[*] Downloading olistbr/brazilian-ecommerce into {OLIST_RAW_DIR}...")
        OLIST_RAW_DIR.mkdir(parents=True, exist_ok=True)
        kaggle.api.dataset_download_files(
            "olistbr/brazilian-ecommerce", path=str(OLIST_RAW_DIR), unzip=True
        )
        print("[+] Olist dataset downloaded and extracted.")

        # Download Fashion Product Images (styles.csv only)
        print(f"[*] Downloading paramaggarwal/fashion-product-images-dataset into {FASHION_RAW_DIR}...")
        FASHION_RAW_DIR.mkdir(parents=True, exist_ok=True)
        kaggle.api.dataset_download_file(
            "paramaggarwal/fashion-product-images-dataset",
            file_name="styles.csv",
            path=str(FASHION_RAW_DIR),
            force=False,
            quiet=False,
        )
        print("[+] Fashion dataset metadata downloaded.")
        return True
    except ImportError:
        print("[i] 'kaggle' package is not installed. You can install it via: pip install kaggle")
        print_kaggle_setup_instructions()
        return False
    except Exception as e:
        print(f"[!] Kaggle API download failed: {e}")
        print_kaggle_setup_instructions()
        return False


def main():
    print("ThreadIQ - Dataset Status Audit")
    
    olist_status = check_dataset_files(OLIST_RAW_DIR, OLIST_FILES, "Olist E-Commerce Dataset")
    fashion_status = check_dataset_files(FASHION_RAW_DIR, FASHION_FILES, "Fashion Product Images Dataset")
    
    if olist_status["complete"] and fashion_status["complete"]:
        print("\n[+] All required dataset files are present in data/raw/!")
        sys.exit(0)
    else:
        print("\n[!] One or more raw datasets are incomplete or missing.")
        # Check if Kaggle download can be attempted
        if not try_kaggle_download():
            print("[*] Waiting for raw dataset files to be acquired.")
            sys.exit(1)


if __name__ == "__main__":
    main()
