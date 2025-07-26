"""
Configuration validation utility
Helps validate and troubleshoot configuration issues
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from config import *


def validate_config():
    """Validate configuration settings"""
    print("🔧 Configuration Validation")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    issues = []
    
    # Check environment variables
    env_vars = {
        'AZURE_DEVOPS_ORG_URL': os.getenv('AZURE_DEVOPS_ORG_URL'),
        'AZURE_DEVOPS_PAT': os.getenv('AZURE_DEVOPS_PAT'),
        'AZURE_DEVOPS_DEFAULT_PROJECT': os.getenv('AZURE_DEVOPS_DEFAULT_PROJECT')
    }
    
    print("Environment Variables:")
    for var_name, var_value in env_vars.items():
        if var_value:
            # Mask PAT for security
            display_value = var_value if var_name != 'AZURE_DEVOPS_PAT' else f"{var_value[:8]}{'*' * 20}"
            print(f"  ✅ {var_name}: {display_value}")
        else:
            print(f"  ❌ {var_name}: Not set")
            issues.append(f"Missing environment variable: {var_name}")
    
    # Check config values
    print(f"\nConfiguration Settings:")
    print(f"  ✅ PLAN_ID: {PLAN_ID}")
    print(f"  ✅ SUITE_ID_START: {SUITE_ID_START}")
    print(f"  ✅ SUITE_ID_END: {SUITE_ID_END}")
    print(f"  ✅ EXPORT_FILENAME: {EXPORT_FILENAME}")
    print(f"  ✅ SHEET_NAME: {SHEET_NAME}")
    
    # Validate suite range
    if SUITE_ID_END < SUITE_ID_START:
        issues.append("SUITE_ID_END must be greater than or equal to SUITE_ID_START")
    
    suite_count = SUITE_ID_END - SUITE_ID_START + 1
    print(f"  ✅ Suite Count: {suite_count} suites will be processed")
    
    if suite_count > 100:
        print(f"  ⚠️  Warning: Processing {suite_count} suites may take a long time")
    
    # Check file permissions
    export_path = Path(EXPORT_FILENAME)
    try:
        # Try to create/write to the export file
        test_file = export_path.with_suffix('.test')
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✅ Export path writable: {export_path.absolute()}")
    except Exception as e:
        issues.append(f"Cannot write to export path: {str(e)}")
        print(f"  ❌ Export path not writable: {export_path.absolute()}")
    
    # Summary
    print("\n" + "=" * 40)
    if issues:
        print("❌ Configuration Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Configuration is valid!")
        return True


def show_estimated_runtime():
    """Show estimated runtime based on configuration"""
    suite_count = SUITE_ID_END - SUITE_ID_START + 1
    
    # Rough estimates based on API call time
    estimated_seconds = suite_count * 2  # ~2 seconds per suite (conservative estimate)
    estimated_minutes = estimated_seconds / 60
    
    print(f"\n⏱️  Estimated Runtime:")
    print(f"   Suites to process: {suite_count}")
    print(f"   Estimated time: {estimated_seconds:.0f} seconds ({estimated_minutes:.1f} minutes)")
    
    if estimated_minutes > 10:
        print(f"   ⚠️  This may take a while. Consider running in smaller batches.")


def main():
    """Main validation function"""
    is_valid = validate_config()
    
    if is_valid:
        show_estimated_runtime()
        print(f"\n🚀 Ready to run: python test_case_downloader.py")
    else:
        print(f"\n🔧 Please fix the issues above before running the downloader")
        sys.exit(1)


if __name__ == "__main__":
    main()
