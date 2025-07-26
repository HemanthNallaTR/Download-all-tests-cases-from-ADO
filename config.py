"""
Configuration settings for the Azure DevOps Test Case Downloader
"""

# Azure DevOps Configuration
PLAN_ID = 1410043  # Constant plan ID
SUITE_ID_START = 1410044  # Starting suite ID
SUITE_ID_END = 1410100  # Ending suite ID

# Export Configuration
EXPORT_FILENAME = "test_cases_export.xlsx"
SHEET_NAME = "Test Cases"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Test Case Fields to Export
TEST_CASE_FIELDS = [
    "id",
    "title",
    "state",
    "priority",
    "areaPath",
    "iterationPath",
    "assignedTo",
    "description",
    "steps",
    "expectedResult",
    "tags"
]
