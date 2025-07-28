# Azure DevOps Test Case Downloader

A Python framework to download test cases from Azure DevOps and export them to Excel format. This tool directly uses Azure DevOps REST APIs to fetch test case data without requiring additional dependencies like MCP.

# Azure DevOps Test Case Downloader

A comprehensive Python framework to download test cases from Azure DevOps and export them to Excel format. This tool uses Azure DevOps REST APIs directly to fetch test case data with enhanced features for different output modes.

## 🚀 Quick Start Options

### **Option 1: Essential Columns Mode (RECOMMENDED)**

```bash
# Downloads only: Test Case ID, Title, Test Steps, Expected Results
run_essential.bat
python test_case_downloader.py --essential
```

**Output**: Individual Excel files for each suite with 4 essential columns

- `TestCases_Plan1410043_Suite1410044_Essential_YYYYMMDD_HHMMSS.xlsx`
- `TestCases_Plan1410043_Suite1410045_Essential_YYYYMMDD_HHMMSS.xlsx`
- ... (one file per suite)
- `TestCases_Plan1410043_Summary_Essential_YYYYMMDD_HHMMSS.xlsx` (all combined)

**🗑️ Automatic Cleanup**: Old test case files are automatically deleted before downloading new ones to keep your workspace clean.

### **Option 2: Full Details Mode**

```bash
# Downloads all available fields (20+ columns)
run_full.bat
python test_case_downloader.py --mode full
```

**Output**: Individual Excel files for each suite with all available fields

- `TestCases_Plan1410043_Suite1410044_Full_YYYYMMDD_HHMMSS.xlsx`
- `TestCases_Plan1410043_Suite1410045_Full_YYYYMMDD_HHMMSS.xlsx`
- ... (one file per suite)
- `TestCases_Plan1410043_Summary_Full_YYYYMMDD_HHMMSS.xlsx` (all combined)

## 📦 Full Setup (Excel Export)

1. **Run the setup script**:

```bash
python setup.py
```

2. **Configure your credentials** by editing the `.env` file:

```
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/tr-corp-tax
AZURE_DEVOPS_PAT=your_personal_access_token_here
AZURE_DEVOPS_DEFAULT_PROJECT=OnesourceGCR
```

3. **Run the downloader**:

```bash
python test_case_downloader.py
```

## 🔧 Troubleshooting Installation Issues

If you encounter errors installing pandas/numpy (common on Windows), use the **lightweight version**:

```bash
# Install minimal dependencies only
pip install requests python-dotenv

# Run the lightweight version (CSV export)
python lightweight_downloader.py
```

The lightweight version:

- ✅ Avoids pandas/numpy compilation issues
- ✅ Exports to CSV (Excel-compatible)
- ✅ Same data extraction capabilities
- ✅ Works on any Python 3.7+ installation

## Features

- ✅ **Direct REST API calls** - No MCP dependencies required
- ✅ **Bulk download** - Iterates through multiple suite IDs (1410044 to 1410100)
- ✅ **Multiple export formats** - Excel (full version) or CSV (lightweight)
- ✅ **Detailed test steps** - Extracts and formats test steps from HTML
- ✅ **Comprehensive logging** - Track progress and troubleshoot issues
- ✅ **Authentication handling** - Secure PAT-based authentication
- ✅ **Error recovery** - Continues processing even if individual suites fail
- ✅ **Two versions available** - Full (Excel) and Lightweight (CSV)

## Configuration

The script is configured in `config.py`:

- **Plan ID**: 1410043 (constant)
- **Suite ID Range**: 1410044 to 1410100 (57 suites)
- **Export File**: `test_cases_export.xlsx` or `test_cases_export.csv`

### Customizing the Range

To download from different suites, edit `config.py`:

```python
SUITE_ID_START = 1410044  # Starting suite ID
SUITE_ID_END = 1410100    # Ending suite ID
```

## Output Format

### Excel Version (test_case_downloader.py)

Creates `test_cases_export.xlsx` with formatted columns and auto-sizing.

### CSV Version (lightweight_downloader.py)

Creates two files:

- `test_cases_export.csv` - Standard UTF-8 CSV
- `test_cases_export_excel.csv` - Excel-compatible CSV with BOM

Both contain the same columns:

- **Basic Info**: ID, Title, Plan ID, Suite ID, Plan Name, Suite Name
- **Status**: State, Assigned To, Priority, Automation Status
- **Metadata**: Activated By, Dates, Work Item Type, Revision
- **Content**: Test Steps (formatted and readable)

## Authentication Setup

1. **Create a Personal Access Token (PAT)** in Azure DevOps:

   - Go to User Settings → Personal Access Tokens
   - Create new token with permissions:
     - **Test Plans**: Read
     - **Work Items**: Read
2. **Add to .env file**:

```
AZURE_DEVOPS_PAT=your_token_here
```

## Available Scripts

| Script                        | Purpose             | Dependencies     | Output     |
| ----------------------------- | ------------------- | ---------------- | ---------- |
| `quick_start.bat`           | Windows quick start | Minimal          | CSV        |
| `setup.py`                  | Full installation   | All              | Setup only |
| `test_case_downloader.py`   | Full version        | pandas, openpyxl | Excel      |
| `lightweight_downloader.py` | Minimal version     | requests only    | CSV        |
| `validate_config.py`        | Configuration check | Minimal          | Validation |

## Troubleshooting

### Common Issues

**"Failed to install dependencies"**

- Use `quick_start.bat` or `lightweight_downloader.py`
- Install Visual Studio Build Tools if you need the Excel version

**"Missing environment variables"**

- Ensure `.env` file exists and contains all required variables
- Use `validate_config.py` to check your setup

**"Authentication failed"**

- Verify your PAT token has correct permissions
- Check that the token hasn't expired

**"Test plan not found"**

- Verify the PLAN_ID in `config.py` is correct
- Check you have access to the test plan in Azure DevOps

### Getting Help

1. Try the quick start: `quick_start.bat`
2. Validate configuration: `python validate_config.py`
3. Check the logs for detailed error messages
4. Use the lightweight version if installation fails

## Sample Output

```
2025-01-25 10:30:15,123 - INFO - Starting Azure DevOps Test Case Downloader
2025-01-25 10:30:15,124 - INFO - Target Organization: https://dev.azure.com/tr-corp-tax
2025-01-25 10:30:15,125 - INFO - Target Project: OnesourceGCR
2025-01-25 10:30:15,126 - INFO - Plan ID: 1410043
2025-01-25 10:30:15,127 - INFO - Suite ID Range: 1410044 - 1410100
2025-01-25 10:30:16,234 - INFO - Retrieved 5 test cases from suite 1410044
...
2025-01-25 10:32:45,678 - INFO - Successfully exported 142 test cases to test_cases_export.csv
```
