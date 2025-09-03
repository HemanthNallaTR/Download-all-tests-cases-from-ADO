#!/usr/bin/env python3
"""
S3 Test Case Uploader

This script uploads Excel test case files to Amazon S3 bucket with detailed logging.
It follows the same flow as the open arena chain uploader but targets S3 storage.

Usage:
    python s3_test_case_uploader.py

Dependencies:
    pip install boto3 python-dotenv

Environment Variables (.env file):
    AWS_ACCESS_KEY_ID=your_access_key_here
    AWS_SECRET_ACCESS_KEY=your_secret_key_here
    AWS_SESSION_TOKEN=your_session_token_here (optional, for temporary credentials)
    AWS_REGION=us-east-1 (optional, defaults to us-east-1)
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
except ImportError:
    print("❌ boto3 not installed. Please run: pip install boto3")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Please set environment variables manually.")

class S3TestCaseUploader:
    """Upload test case files to Amazon S3 bucket"""
    
    def __init__(self, bucket_name: str, aws_account_id: str, region: str = "us-east-1", prefix: str = "testcases/"):
        """
        Initialize the S3 uploader
        
        Args:
            bucket_name: S3 bucket name
            aws_account_id: AWS Account ID
            region: AWS region (default: us-east-1)
            prefix: S3 key prefix for uploaded files (default: testcases/)
        """
        self.bucket_name = bucket_name
        self.aws_account_id = aws_account_id
        self.region = region
        self.prefix = prefix.rstrip('/') + '/' if prefix and not prefix.endswith('/') else prefix
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with formatting
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Initialize S3 client
        self.s3_client = None
        self.s3_resource = None
        self._initialize_s3_client()
        
    def _initialize_s3_client(self):
        """Initialize AWS S3 client and resource"""
        try:
            # Check for AWS credentials
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_session_token = os.getenv('AWS_SESSION_TOKEN')
            
            session_kwargs = {}
            
            if aws_access_key and aws_secret_key:
                session_kwargs.update({
                    'aws_access_key_id': aws_access_key,
                    'aws_secret_access_key': aws_secret_key,
                })
                if aws_session_token:
                    session_kwargs['aws_session_token'] = aws_session_token
                    
                self.logger.info("📡 Using provided AWS credentials from environment")
            else:
                self.logger.info("📡 Using default AWS credential chain (IAM role, profile, etc.)")
            
            # Create session and clients
            session = boto3.Session(
                region_name=self.region,
                **session_kwargs
            )
            
            self.s3_client = session.client('s3')
            self.s3_resource = session.resource('s3')
            
            self.logger.info(f"✅ S3 client initialized for region: {self.region}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize S3 client: {e}")
            raise
    
    def test_s3_access(self) -> bool:
        """
        Test S3 access by trying to list bucket contents
        
        Returns:
            bool: True if S3 access is successful
        """
        try:
            self.logger.info("📡 Testing S3 bucket access...")
            
            # Test bucket access
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"✅ Successfully accessed bucket: {self.bucket_name}")
            
            # Test list objects (with prefix to limit results)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix,
                MaxKeys=1
            )
            
            object_count = response.get('KeyCount', 0)
            self.logger.info(f"✅ Found {object_count} objects with prefix '{self.prefix}'")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                self.logger.error("❌ Access denied to S3 bucket. Check your permissions.")
            elif error_code == '404':
                self.logger.error(f"❌ Bucket '{self.bucket_name}' not found.")
            else:
                self.logger.error(f"❌ S3 access test failed: {e}")
            return False
        except NoCredentialsError:
            self.logger.error("❌ AWS credentials not found. Please configure your credentials.")
            return False
        except PartialCredentialsError:
            self.logger.error("❌ Incomplete AWS credentials. Please check your configuration.")
            return False
        except Exception as e:
            self.logger.error(f"❌ S3 access test failed: {e}")
            return False
    
    def list_existing_files(self) -> List[Dict]:
        """
        List existing files in the S3 bucket with the specified prefix
        
        Returns:
            List of file information dictionaries
        """
        try:
            self.logger.info(f"📋 Listing existing files in bucket '{self.bucket_name}' with prefix '{self.prefix}'...")
            
            existing_files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    file_info = {
                        'key': obj['Key'],
                        'name': os.path.basename(obj['Key']),
                        'size': f"{obj['Size'] / 1024:.1f} KB",
                        'last_modified': obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S UTC"),
                        'etag': obj['ETag'].strip('"')
                    }
                    existing_files.append(file_info)
            
            self.logger.info(f"✅ Found {len(existing_files)} existing files")
            
            if existing_files:
                self.logger.info("📋 Existing files:")
                for file_info in existing_files[:10]:  # Show first 10 files
                    self.logger.info(f"   - {file_info['name']} ({file_info['size']}) - {file_info['last_modified']}")
                
                if len(existing_files) > 10:
                    self.logger.info(f"   ... and {len(existing_files) - 10} more files")
            
            return existing_files
            
        except ClientError as e:
            self.logger.error(f"❌ Failed to list existing files: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error listing existing files: {e}")
            return []
    
    def delete_files(self, file_keys: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Delete specified files from S3 bucket
        
        Args:
            file_keys: List of S3 object keys to delete
            
        Returns:
            tuple: (success: bool, deleted_files: list, failed_files: list)
        """
        if not file_keys:
            return True, [], []
        
        try:
            self.logger.info(f"🗑️ Deleting {len(file_keys)} files from S3...")
            
            # Prepare delete request (S3 supports batch delete up to 1000 objects)
            objects_to_delete = [{'Key': key} for key in file_keys]
            
            deleted_files = []
            failed_files = []
            
            # Process in batches of 1000 (S3 limit)
            batch_size = 1000
            for i in range(0, len(objects_to_delete), batch_size):
                batch = objects_to_delete[i:i + batch_size]
                
                try:
                    response = self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={
                            'Objects': batch,
                            'Quiet': False
                        }
                    )
                    
                    # Process successful deletions
                    for deleted in response.get('Deleted', []):
                        deleted_key = deleted['Key']
                        deleted_files.append(deleted_key)
                        self.logger.info(f"✅ Deleted: {os.path.basename(deleted_key)}")
                    
                    # Process failed deletions
                    for error in response.get('Errors', []):
                        failed_key = error['Key']
                        error_code = error['Code']
                        error_message = error['Message']
                        failed_files.append(failed_key)
                        self.logger.error(f"❌ Failed to delete {os.path.basename(failed_key)}: {error_code} - {error_message}")
                        
                except ClientError as e:
                    self.logger.error(f"❌ Batch delete failed: {e}")
                    # Add all keys in this batch to failed list
                    failed_files.extend([obj['Key'] for obj in batch])
            
            success = len(failed_files) == 0
            
            self.logger.info(f"📊 Deletion Summary:")
            self.logger.info(f"✅ Successfully deleted: {len(deleted_files)} files")
            self.logger.info(f"❌ Failed to delete: {len(failed_files)} files")
            
            return success, deleted_files, failed_files
            
        except Exception as e:
            self.logger.error(f"❌ Error during file deletion: {e}")
            return False, [], file_keys
    
    def upload_file(self, file_path: Path, s3_key: Optional[str] = None) -> bool:
        """
        Upload a single file to S3
        
        Args:
            file_path: Local file path to upload
            s3_key: Optional custom S3 key (if not provided, uses prefix + filename)
            
        Returns:
            bool: True if upload was successful
        """
        try:
            if not file_path.exists():
                self.logger.error(f"❌ File not found: {file_path}")
                return False
            
            # Generate S3 key
            if s3_key is None:
                s3_key = f"{self.prefix}{file_path.name}"
            
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            self.logger.info(f"📤 Uploading: {file_path.name} ({file_size_mb:.2f} MB)")
            self.logger.info(f"🎯 S3 Key: {s3_key}")
            
            # Upload file with metadata
            start_time = time.time()
            
            extra_args = {
                'Metadata': {
                    'original-filename': file_path.name,
                    'upload-timestamp': datetime.now(timezone.utc).isoformat(),
                    'uploader': 'S3TestCaseUploader',
                    'aws-account': self.aws_account_id
                }
            }
            
            # Use multipart upload for files larger than 100MB
            if file_size_mb > 100:
                self.logger.info("📦 Using multipart upload for large file...")
                extra_args['Config'] = boto3.s3.transfer.TransferConfig(
                    multipart_threshold=1024 * 25,  # 25MB
                    max_concurrency=10,
                    multipart_chunksize=1024 * 25,
                    use_threads=True
                )
            
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            upload_time = time.time() - start_time
            upload_speed = file_size_mb / upload_time if upload_time > 0 else 0
            
            self.logger.info(f"✅ Upload successful: {file_path.name}")
            self.logger.info(f"⏱️ Upload time: {upload_time:.1f}s ({upload_speed:.1f} MB/s)")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"❌ S3 upload failed for {file_path.name}: {error_code} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Upload error for {file_path.name}: {e}")
            return False
    
    def upload_files_batch(self, file_paths: List[Path]) -> Tuple[int, int, List[str], List[str]]:
        """
        Upload multiple files to S3 with detailed logging
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            tuple: (successful_count, failed_count, successful_files, failed_files)
        """
        if not file_paths:
            self.logger.warning("⚠️ No files provided for upload")
            return 0, 0, [], []
        
        self.logger.info(f"🚀 Starting batch upload of {len(file_paths)} files...")
        
        successful_files = []
        failed_files = []
        total_size = 0
        
        # Calculate total size
        for file_path in file_paths:
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        total_size_mb = total_size / (1024 * 1024)
        self.logger.info(f"📊 Total upload size: {total_size_mb:.2f} MB")
        
        start_time = time.time()
        
        # Upload files sequentially with progress tracking
        for i, file_path in enumerate(file_paths, 1):
            self.logger.info(f"[{i}/{len(file_paths)}] Processing: {file_path.name}")
            
            if self.upload_file(file_path):
                successful_files.append(file_path.name)
                self.logger.info(f"✅ [{i}/{len(file_paths)}] Success: {file_path.name}")
            else:
                failed_files.append(file_path.name)
                self.logger.error(f"❌ [{i}/{len(file_paths)}] Failed: {file_path.name}")
            
            # Progress update
            progress = (i / len(file_paths)) * 100
            self.logger.info(f"📈 Progress: {progress:.1f}% ({i}/{len(file_paths)})")
        
        total_time = time.time() - start_time
        avg_speed = total_size_mb / total_time if total_time > 0 else 0
        
        self.logger.info(f"\n📊 BATCH UPLOAD SUMMARY:")
        self.logger.info(f"✅ Successful uploads: {len(successful_files)}")
        self.logger.info(f"❌ Failed uploads: {len(failed_files)}")
        self.logger.info(f"📁 Total files: {len(file_paths)}")
        self.logger.info(f"💾 Total size: {total_size_mb:.2f} MB")
        self.logger.info(f"⏱️ Total time: {total_time:.1f}s")
        self.logger.info(f"🚀 Average speed: {avg_speed:.1f} MB/s")
        
        if successful_files:
            self.logger.info(f"\n✅ Successfully uploaded files:")
            for filename in successful_files:
                self.logger.info(f"   - {filename}")
        
        if failed_files:
            self.logger.info(f"\n❌ Failed uploads:")
            for filename in failed_files:
                self.logger.info(f"   - {filename}")
        
        return len(successful_files), len(failed_files), successful_files, failed_files
    
    def scan_directory_for_files(self, directory: Path, patterns: List[str] = None) -> List[Path]:
        """
        Scan directory for files matching specified patterns
        
        Args:
            directory: Directory to scan
            patterns: List of file patterns (default: ['*.xlsx', '*.xls'])
            
        Returns:
            List of matching file paths
        """
        if patterns is None:
            patterns = ['*.xlsx', '*.xls']
        
        self.logger.info(f"🔍 Scanning directory: {directory}")
        self.logger.info(f"📋 Looking for patterns: {', '.join(patterns)}")
        
        if not directory.exists():
            self.logger.error(f"❌ Directory not found: {directory}")
            return []
        
        found_files = []
        for pattern in patterns:
            matched_files = list(directory.glob(pattern))
            found_files.extend(matched_files)
            self.logger.info(f"   📁 Pattern '{pattern}': {len(matched_files)} files")
        
        # Remove duplicates and sort
        found_files = sorted(list(set(found_files)))
        
        self.logger.info(f"✅ Total files found: {len(found_files)}")
        
        if found_files:
            self.logger.info("📋 Found files:")
            for i, file_path in enumerate(found_files[:10], 1):  # Show first 10
                file_size = file_path.stat().st_size / 1024  # KB
                self.logger.info(f"   {i:2d}. {file_path.name} ({file_size:.1f} KB)")
            
            if len(found_files) > 10:
                self.logger.info(f"   ... and {len(found_files) - 10} more files")
        
        return found_files


def get_user_choice(question: str, options: List[str]) -> str:
    """
    Prompt user to choose from a list of options
    
    Args:
        question: Question to ask the user
        options: List of valid options
        
    Returns:
        Selected option
    """
    while True:
        print(f"\n{question}")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        try:
            choice = input("\nEnter your choice (number): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(options):
                return options[choice_idx]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(options)}")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)


def main():
    """Main execution function"""
    print("=" * 70)
    print("S3 Test Case Uploader")
    print("=" * 70)
    print("Upload test case Excel files to Amazon S3 with detailed logging")
    print()
    
    # Configuration from your requirements
    bucket_name = "a200190-oct-nonprod-us-east-1-service-builds"
    aws_account_id = "600627334605"
    region = "us-east-1"
    prefix = "testcases/"
    
    print(f"📍 Configuration:")
    print(f"   🪣 S3 Bucket: {bucket_name}")
    print(f"   🏢 AWS Account: {aws_account_id}")
    print(f"   🌍 Region: {region}")
    print(f"   📁 Prefix: {prefix}")
    print()
    
    # Initialize uploader
    try:
        uploader = S3TestCaseUploader(
            bucket_name=bucket_name,
            aws_account_id=aws_account_id,
            region=region,
            prefix=prefix
        )
    except Exception as e:
        print(f"❌ Failed to initialize S3 uploader: {e}")
        sys.exit(1)
    
    # Test S3 access
    print("📡 Testing S3 access...")
    if not uploader.test_s3_access():
        print("\n❌ S3 access test failed. Please check your AWS credentials and permissions.")
        print("\nRequired permissions:")
        print("- s3:ListBucket")
        print("- s3:GetObject")
        print("- s3:PutObject")
        print("- s3:DeleteObject")
        sys.exit(1)
    
    # Scan for files in current directory and test_cases_by_suite
    current_dir = Path.cwd()
    test_cases_dir = current_dir / "test_cases_by_suite"
    
    all_files = []
    
    # Scan current directory
    current_files = uploader.scan_directory_for_files(current_dir)
    if current_files:
        print(f"\n📁 Found {len(current_files)} files in current directory")
        all_files.extend(current_files)
    
    # Scan test_cases_by_suite directory
    if test_cases_dir.exists():
        suite_files = uploader.scan_directory_for_files(test_cases_dir)
        if suite_files:
            print(f"\n📁 Found {len(suite_files)} files in test_cases_by_suite directory")
            all_files.extend(suite_files)
    
    if not all_files:
        print("\n❌ No Excel files found in current directory or test_cases_by_suite")
        sys.exit(1)
    
    print(f"\n📊 Total files discovered: {len(all_files)}")
    
    # Check for existing files in S3
    print("\n🔍 Checking existing files in S3...")
    existing_files = uploader.list_existing_files()
    
    # Handle existing files
    if existing_files:
        print(f"\n🗑️ Found {len(existing_files)} existing files in S3")
        
        delete_options = [
            "Delete all existing files before upload",
            "Skip deletion (keep existing files)",
            "Cancel upload"
        ]
        
        delete_choice = get_user_choice("How should we handle existing files?", delete_options)
        
        if delete_choice == "Cancel upload":
            print("\nUpload cancelled by user.")
            sys.exit(0)
        elif delete_choice == "Delete all existing files before upload":
            file_keys = [file_info['key'] for file_info in existing_files]
            success, deleted, failed = uploader.delete_files(file_keys)
            
            if not success and failed:
                continue_options = ["Continue with upload", "Cancel upload"]
                continue_choice = get_user_choice("Some deletions failed. What would you like to do?", continue_options)
                
                if continue_choice == "Cancel upload":
                    print("\nUpload cancelled due to deletion failures.")
                    sys.exit(1)
    else:
        print("✅ No existing files found in S3")
    
    # File selection
    file_options = [
        "Upload all discovered files",
        "Select specific files",
        "Cancel upload"
    ]
    
    file_choice = get_user_choice("What files would you like to upload?", file_options)
    
    if file_choice == "Cancel upload":
        print("\nUpload cancelled by user.")
        sys.exit(0)
    
    # Filter files if needed
    files_to_upload = all_files
    if file_choice == "Select specific files":
        print(f"\n📋 Available files:")
        for i, file_path in enumerate(all_files, 1):
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"{i:2d}. {file_path.name} ({file_size:.1f} KB) - {file_path.parent.name}")
        
        while True:
            try:
                selection = input("\nEnter file numbers to upload (comma-separated, e.g., 1,3,5): ").strip()
                if not selection:
                    print("No files selected.")
                    continue
                    
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                files_to_upload = [all_files[i] for i in indices if 0 <= i < len(all_files)]
                
                if files_to_upload:
                    break
                else:
                    print("No valid files selected.")
                    
            except (ValueError, IndexError):
                print("Invalid selection. Please enter valid file numbers.")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                sys.exit(0)
    
    print(f"\n📤 Selected {len(files_to_upload)} files for upload")
    
    # Confirm upload
    total_size_mb = sum(f.stat().st_size for f in files_to_upload) / (1024 * 1024)
    print(f"💾 Total upload size: {total_size_mb:.2f} MB")
    
    choice = input(f"\nProceed with upload to S3? (y/n): ").strip().lower()
    if choice != 'y':
        print("Upload cancelled")
        sys.exit(0)
    
    # Perform upload
    print(f"\n🚀 Starting upload of {len(files_to_upload)} files to S3...")
    
    successful_count, failed_count, successful_files, failed_files = uploader.upload_files_batch(files_to_upload)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL UPLOAD SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully uploaded: {successful_count} files")
    print(f"❌ Failed uploads: {failed_count} files")
    print(f"📁 Total files processed: {len(files_to_upload)}")
    print(f"🪣 S3 Bucket: {bucket_name}")
    print(f"📁 S3 Prefix: {prefix}")
    
    if failed_count == 0:
        print("\n🎉 All files uploaded successfully!")
        print(f"🔗 Files are now available at: s3://{bucket_name}/{prefix}")
    else:
        print(f"\n⚠️ {failed_count} files failed to upload. Please check the error messages above.")
    
    print("\n✨ Upload process completed.")


if __name__ == "__main__":
    main()
