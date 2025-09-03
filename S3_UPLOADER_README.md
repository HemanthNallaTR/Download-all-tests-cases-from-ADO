# S3 Test Case Uploader

This script uploads Excel test case files to Amazon S3 bucket with detailed logging and follows the same flow as the Open Arena Chain uploader.

## Features

- 🔍 **Smart File Discovery**: Automatically scans current directory and `test_cases_by_suite` folder
- 📊 **Detailed Logging**: Clear, step-by-step logging for each operation
- 🗑️ **File Management**: Option to delete existing files before upload
- 📤 **Batch Upload**: Efficient upload of multiple files with progress tracking
- 🛡️ **Error Handling**: Comprehensive error handling and retry logic
- 📈 **Progress Tracking**: Real-time upload progress and speed monitoring
- 🎯 **Flexible Selection**: Upload all files or select specific ones

## Prerequisites

1. **Python 3.7+** installed
2. **AWS credentials** configured
3. **Required Python packages** (installed automatically)

## AWS Configuration

### S3 Bucket Details
- **Bucket**: `a200190-oct-nonprod-us-east-1-service-builds`
- **Account ID**: `600627334605`
- **Region**: `us-east-1`
- **Prefix**: `testcases/`

### Required AWS Permissions

Your AWS credentials need the following S3 permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::a200190-oct-nonprod-us-east-1-service-builds"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::a200190-oct-nonprod-us-east-1-service-builds/testcases/*"
        }
    ]
}
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

#### Option A: Environment Variables (.env file)
1. Copy the template: `cp .env.template .env`
2. Edit `.env` file with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # Optional for temporary credentials
AWS_REGION=us-east-1
```

#### Option B: AWS CLI Configuration
```bash
aws configure
```

#### Option C: IAM Role (if running on EC2)
The script will automatically use the instance's IAM role.

## Usage

### Quick Start (Windows)
```bash
run_s3_uploader.bat
```

### Manual Run
```bash
python s3_test_case_uploader.py
```

## File Discovery

The script automatically scans for Excel files (*.xlsx, *.xls) in:

1. **Current directory**: Where the script is run
2. **test_cases_by_suite/**: Subdirectory with test case files

### Supported File Types
- Excel files (.xlsx, .xls)
- Any files matching the patterns in `test_cases_by_suite/`

## Upload Process Flow

1. **🔍 Discovery Phase**
   - Scan current directory for Excel files
   - Scan `test_cases_by_suite/` directory
   - Display found files with sizes

2. **📡 Access Verification**
   - Test AWS credentials
   - Verify S3 bucket access
   - Check permissions

3. **📋 Existing Files Check**
   - List existing files in S3 bucket
   - Option to delete existing files
   - Confirmation prompts

4. **📤 File Selection**
   - Choose to upload all files or select specific ones
   - Display selected files and total size

5. **🚀 Upload Execution**
   - Sequential upload with progress tracking
   - Real-time speed monitoring
   - Detailed success/failure logging

6. **📊 Summary Report**
   - Upload statistics
   - Success/failure breakdown
   - S3 location details

## Example Upload Log

```
======================================================================
S3 Test Case Uploader
======================================================================
Upload test case Excel files to Amazon S3 with detailed logging

📍 Configuration:
   🪣 S3 Bucket: a200190-oct-nonprod-us-east-1-service-builds
   🏢 AWS Account: 600627334605
   🌍 Region: us-east-1
   📁 Prefix: testcases/

2025-01-13 10:30:15,123 - INFO - 📡 Using provided AWS credentials from environment
2025-01-13 10:30:15,124 - INFO - ✅ S3 client initialized for region: us-east-1
📡 Testing S3 access...
2025-01-13 10:30:15,456 - INFO - 📡 Testing S3 bucket access...
2025-01-13 10:30:15,789 - INFO - ✅ Successfully accessed bucket: a200190-oct-nonprod-us-east-1-service-builds
2025-01-13 10:30:15,890 - INFO - ✅ Found 0 objects with prefix 'testcases/'

🔍 Scanning directory: C:\Download all tests cases from ADO
📋 Looking for patterns: *.xlsx, *.xls
   📁 Pattern '*.xlsx': 0 files
   📁 Pattern '*.xls': 0 files
✅ Total files found: 0

📁 Found 53 files in test_cases_by_suite directory
📊 Total files discovered: 53

🔍 Checking existing files in S3...
✅ No existing files found in S3

What files would you like to upload?
1. Upload all discovered files
2. Select specific files
3. Cancel upload

Enter your choice (number): 1

📤 Selected 53 files for upload
💾 Total upload size: 156.78 MB

Proceed with upload to S3? (y/n): y

🚀 Starting upload of 53 files to S3...
[1/53] Processing: TestCases_Plan1410043_Suite1410044_Essential_20250728_170324.xlsx
📤 Uploading: TestCases_Plan1410043_Suite1410044_Essential_20250728_170324.xlsx (2.95 MB)
🎯 S3 Key: testcases/TestCases_Plan1410043_Suite1410044_Essential_20250728_170324.xlsx
✅ Upload successful: TestCases_Plan1410043_Suite1410044_Essential_20250728_170324.xlsx
⏱️ Upload time: 3.2s (0.9 MB/s)
✅ [1/53] Success: TestCases_Plan1410043_Suite1410044_Essential_20250728_170324.xlsx
📈 Progress: 1.9% (1/53)

📊 BATCH UPLOAD SUMMARY:
✅ Successful uploads: 53
❌ Failed uploads: 0
📁 Total files: 53
💾 Total size: 156.78 MB
⏱️ Total time: 127.3s
🚀 Average speed: 1.2 MB/s
```

## Error Handling

The script handles various error scenarios:

- **AWS Credential Issues**: Clear messages about missing/invalid credentials
- **S3 Access Problems**: Permission and bucket access errors
- **File Upload Failures**: Individual file upload errors with retry logic
- **Network Issues**: Timeout and connection error handling
- **Large File Support**: Automatic multipart upload for files > 100MB

## Troubleshooting

### Common Issues

1. **"AWS credentials not found"**
   - Ensure `.env` file exists with correct credentials
   - Or configure AWS CLI: `aws configure`

2. **"Access denied to S3 bucket"**
   - Verify AWS permissions (see Required AWS Permissions section)
   - Check if bucket name is correct

3. **"Bucket not found"**
   - Verify bucket name: `a200190-oct-nonprod-us-east-1-service-builds`
   - Ensure you have access to the correct AWS account

4. **Upload failures**
   - Check internet connection
   - Verify file permissions
   - Check available disk space

### Debug Mode

For detailed debugging, you can modify the logging level in the script:

```python
self.logger.setLevel(logging.DEBUG)
```

## File Metadata

Each uploaded file includes metadata:
- `original-filename`: Original file name
- `upload-timestamp`: ISO timestamp of upload
- `uploader`: Tool identifier
- `aws-account`: AWS account ID

## Security Notes

- Never commit `.env` file with real credentials to version control
- Use IAM roles when possible instead of access keys
- Regularly rotate access keys
- Follow AWS security best practices

## Support

For issues or questions:
1. Check the error logs in the console output
2. Verify AWS credentials and permissions
3. Ensure network connectivity to AWS S3
4. Check file permissions and disk space

---

**Note**: This uploader is designed to work specifically with the test case files from Azure DevOps and follows the same user experience flow as the Open Arena Chain uploader.
