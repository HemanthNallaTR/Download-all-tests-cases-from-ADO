# Thomson Reuters Test Case Uploader - Updated with HAR Analysis

## 🔍 **API Discovery Results**

Through HAR file analysis, we've identified the correct Thomson Reuters API structure:

### API Details
- **Base URL**: `https://aiopenarena.gcs.int.thomsonreuters.com`
- **API Version**: `/v1`
- **Authentication**: Bearer Token
- **Workflow ID**: `bbccc927-a30c-4f37-8907-968482778d32`

### File Structure
Files are stored within workflow components:
```json
{
  "components": [
    {},
    {
      "model_params": {
        "modelParam": {
          "file_upload": {
            "files_uploaded": [
              {
                "file_name": "TestCases_Plan1410043_Suite1410045_Essential.xlsx",
                "size": "23.24 KB",
                "uploaded_timestamp": "2025-07-25 13:09:47",
                "id": "unique_file_id"
              }
            ]
          }
        }
      }
    }
  ]
}
```

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configuration
Create `.env.thomson_reuters`:
```env
TR_BEARER_TOKEN=your_bearer_token_here
TR_WORKSPACE_ID=bbccc927-a30c-4f37-8907-968482778d32
```

## 🚀 Usage

### Quick Start
```bash
python open_arena_chain_uploader.py
```

### Manual Run
```python
from open_arena_chain_uploader import OpenArenaChainUploader
from pathlib import Path

# Initialize uploader
uploader = OpenArenaChainUploader("your_bearer_token")

# Upload files
files = Path("test_cases_by_suite").glob("*.xlsx")
for file_path in files:
    uploader.upload_file(file_path)
```

## 🔧 API Endpoints Discovered

Based on HAR analysis, the script tries these endpoints:

### File Listing
- `GET /v1/workflow/{workflow_id}` - Get workflow with files

### File Upload (Multiple attempts)
- `POST /v1/workflow/{workflow_id}/upload`
- `POST /v1/workflow/{workflow_id}/files`
- `POST /v1/upload/workflow/{workflow_id}`
- `POST /upload` (fallback)

### File Deletion
- `DELETE /v1/workflow/{workflow_id}/files/{file_id}`
- `DELETE /v1/files/{file_id}` (alternative)

## 📊 Current File Status

From the HAR analysis, we found 52 existing test case files in the workspace:
```
TestCases_Plan1410043_Suite1410045_Essential.xlsx (23.24 KB)
TestCases_Plan1410043_Suite1410046_Essential.xlsx (15.98 KB)
TestCases_Plan1410043_Suite1410047_Essential.xlsx (23.24 KB)
... (and 49 more files)
```

## ⚠️ Notes

1. **Authentication**: Use a valid Bearer Token from Thomson Reuters platform
2. **Workflow ID**: The default workflow ID is hardcoded but can be overridden
3. **File Management**: Files are managed within workflow components, not direct file operations
4. **Error Handling**: Script includes fallback endpoints and graceful error handling

## 🐛 Troubleshooting

### Common Issues
1. **Invalid Bearer Token**: Check token validity and permissions
2. **Workflow Not Found**: Verify workflow ID is correct
3. **Upload Failures**: API endpoints may require specific formats or additional parameters

### Debug Mode
The script includes extensive logging to help identify API issues:
- Authentication test results
- Endpoint attempt details
- Response status codes and error messages
