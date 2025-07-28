#!/usr/bin/env python3
"""
Open Arena Chain Data Analytics Platform File Uploader

This script uploads Excel test case files to Open Arena Chain Data Analytics workspace
using Bearer Token authentication. It provides options for file management and filtering.

Usage:
    python open_arena_chain_uploader.py

Dependencies:
    pip install requests python-dotenv

Environment Variables (.env file):
    TR_BEARER_TOKEN=your_bearer_token_here
    TR_WORKSPACE_ID=your_workspace_id_here (optional)
"""

import os
import sys
import requests
import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import getpass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Please set environment variables manually.")

class OpenArenaChainUploader:
    """Upload files to Open Arena Chain Data Analytics platform"""
    
    def __init__(self, bearer_token: str, workspace_id: Optional[str] = None):
        """
        Initialize the uploader
        
        Args:
            bearer_token: Bearer token for authentication
            workspace_id: Optional workspace ID (workflow ID for Thomson Reuters)
        """
        self.bearer_token = bearer_token
        self.workspace_id = workspace_id
        self.base_url = "https://aiopenarena.gcs.int.thomsonreuters.com"
        self.api_base = f"{self.base_url}/v1"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {bearer_token}',
            'User-Agent': 'Open Arena Chain Test Case Uploader/1.0',
            'Accept': 'application/json'
        })
        
    def test_authentication(self) -> bool:
        """
        Test if the bearer token is valid by accessing the workflow
        
        Returns:
            bool: True if authentication is successful
        """
        try:
            # Test authentication by accessing the workflow
            workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
            test_url = f"{self.api_base}/workflow/{workflow_id}"
            
            response = self.session.get(test_url)
            
            if response.status_code == 200:
                print("✅ Authentication successful")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed: Invalid bearer token")
                return False
            elif response.status_code == 403:
                print("❌ Authentication failed: Access denied")
                return False
            else:
                print(f"⚠️ Authentication test returned status {response.status_code}")
                print(f"Response: {response.text[:200] if response.text else 'No response body'}")
                # Proceed with caution for other status codes
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    def list_workspace_files(self) -> List[Dict]:
        """
        List existing files in the workspace using workflow endpoint
        
        Returns:
            List of file information dictionaries
        """
        try:
            # Use the correct workflow endpoint from HAR analysis
            workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
            url = f"{self.api_base}/workflow/{workflow_id}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Check if response has content
                if not response.text.strip():
                    print("📋 Workflow is empty (no files found)")
                    return []
                
                try:
                    workflow_data = response.json()
                    
                    # Extract files from the workflow structure based on HAR analysis
                    files = []
                    try:
                        components = workflow_data.get('components', [])
                        if len(components) > 1:
                            model_params = components[1].get('model_params', {})
                            file_upload = model_params.get('modelParam', {}).get('file_upload', {})
                            files_uploaded = file_upload.get('files_uploaded', [])
                            
                            for file_info in files_uploaded:
                                files.append({
                                    'name': file_info.get('file_name', 'Unknown'),
                                    'size': file_info.get('size', 'Unknown'),
                                    'uploaded_timestamp': file_info.get('uploaded_timestamp', 'Unknown'),
                                    'id': file_info.get('id', file_info.get('file_name'))
                                })
                                
                    except (IndexError, KeyError, AttributeError) as e:
                        print(f"⚠️ Warning: Could not parse workflow structure: {e}")
                        print("Raw workflow data keys:")
                        print(list(workflow_data.keys()))
                    
                    return files
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ API returned non-JSON response: {response.text[:100]}...")
                    print("📋 Assuming workflow is empty")
                    return []
            elif response.status_code == 404:
                print("📋 Workflow not found")
                return []
            else:
                print(f"⚠️ Could not access workflow: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error accessing workflow: {e}")
            return []
    
    def delete_workspace_files(self, filenames: list) -> tuple:
        """
        Delete specific files from the Open Arena Chain workflow
        
        Args:
            filenames: List of filenames to delete
            
        Returns:
            tuple: (success: bool, deleted_files: list)
        """
        try:
            # Based on HAR analysis: DELETE /v1/document/{workflow_id}
            workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
            
            # The HAR shows deletion requires files_to_delete in request body
            delete_url = f"{self.api_base}/document/{workflow_id}"
            
            # Prepare payload as shown in HAR file
            payload = {
                "files_to_delete": filenames
            }
            
            print(f"🗑️ Attempting to delete {len(filenames)} files...")
            response = self.session.delete(
                delete_url, 
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    deleted_files = result.get('deleted_files', [])
                    print(f"✅ Successfully deleted {len(deleted_files)} files")
                    for file in deleted_files:
                        print(f"   - {file}")
                    return True, deleted_files
                except json.JSONDecodeError:
                    print(f"✅ Delete request successful (HTTP 200)")
                    return True, filenames
            elif response.status_code == 404:
                print(f"⚠️ Files not found (may already be deleted)")
                return True, filenames  # Consider as successful
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"HTTP {response.status_code}\nResponse: {json.dumps(error_data, indent=2)}"
                except:
                    error_msg = f"HTTP {response.status_code}\nResponse: {response.text[:200] if response.text else 'No response body'}"
                print(f"⚠️ Delete failed: {error_msg}")
                return False, []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting files: {e}")
            return False, []
    
    def upload_files_batch(self, file_paths: list) -> bool:
        """
        Upload multiple files in a single batch request (complete 3-step workflow)
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            bool: True if all uploads were successful
        """
        try:
            # Step 1: Get current workflow configuration
            workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
            workflow_url = f"{self.api_base}/workflow/{workflow_id}"
            
            print(f"📋 Getting current workflow configuration...")
            workflow_response = self.session.get(workflow_url)
            
            if workflow_response.status_code != 200:
                print(f"❌ Failed to get workflow configuration: HTTP {workflow_response.status_code}")
                return False
                
            workflow_data = workflow_response.json()
            print(f"✅ Retrieved workflow configuration")
            
            # Step 2: Prepare batch payload with all files
            files_data = []
            
            for file_path in file_paths:
                file_id = str(uuid.uuid4())
                files_data.append({
                    "file_name": file_path.name,
                    "file_id": file_id
                })
            
            # Based on HAR analysis: exact payload structure
            payload = {
                "asset_id": "204311",
                "files_names": files_data,
                "is_rag_storage_request": True,
                "workflow_id": workflow_id
            }
            
            print(f"📤 Batch upload request for {len(file_paths)} files...")
            
            # Step 3: Single API call - use exact URL from HAR
            upload_url = f"{self.base_url}/v3/document/file_upload"
            
            # Use exact headers from HAR
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": "https://dataandanalytics.int.thomsonreuters.com",
                "Referer": "https://dataandanalytics.int.thomsonreuters.com/"
            }
            
            response = self.session.post(
                upload_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ Batch upload API failed: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
                
            # Step 4: Parse S3 upload URLs from response
            try:
                upload_response = response.json()
                s3_uploads = upload_response.get('url', [])
                
                if not s3_uploads:
                    print("❌ No S3 upload URLs received from API")
                    return False
                    
                print(f"✅ Batch API request successful, proceeding with {len(s3_uploads)} S3 uploads...")
                
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response from batch upload API")
                return False
            
            # Step 5: Upload files to S3 (sequential for now to avoid overwhelming S3)
            successful_uploads = 0
            failed_uploads = 0
            uploaded_files_info = []
            
            for i, s3_data in enumerate(s3_uploads):
                file_info = s3_data
                file_name = file_info.get('file_name', f'file_{i}')
                s3_url_data = file_info.get('url', {})
                
                # Find the corresponding file path
                file_path = None
                for fp in file_paths:
                    if fp.name == file_name:
                        file_path = fp
                        break
                
                if not file_path:
                    print(f"⚠️ Could not find local file for: {file_name}")
                    failed_uploads += 1
                    continue
                
                print(f"[{i+1}/{len(s3_uploads)}] Uploading to S3: {file_name}")
                
                # Upload to S3
                if self.upload_to_s3(file_path, s3_url_data):
                    successful_uploads += 1
                    print(f"✅ S3 upload successful: {file_name}")
                    
                    # Collect uploaded file info for workflow update
                    uploaded_files_info.append({
                        "file_name": file_name,
                        "uploaded_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        "size": f"{file_path.stat().st_size / 1024:.1f} KB"
                    })
                else:
                    failed_uploads += 1
                    print(f"❌ S3 upload failed: {file_name}")
            
            print(f"\n📊 S3 Upload Summary:")
            print(f"✅ Successful: {successful_uploads}")
            print(f"❌ Failed: {failed_uploads}")
            print(f"📁 Total: {len(s3_uploads)}")
            
            # Step 6: CRITICAL - Update workflow with uploaded files (PATCH request)
            if successful_uploads > 0:
                print(f"\n💾 Saving workflow with {successful_uploads} uploaded files...")
                if self.save_workflow_with_files(workflow_data, uploaded_files_info):
                    print(f"✅ Workflow saved successfully!")
                    print(f"🔄 RAG chain will be automatically re-indexed")
                else:
                    print(f"⚠️ Files uploaded but workflow save failed - files may not be visible in Open Arena Chain")
                    return False
            
            return failed_uploads == 0
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Batch upload error: {e}")
            return False
    
    def save_workflow_with_files(self, workflow_data: dict, uploaded_files_info: list) -> bool:
        """
        Save workflow configuration with uploaded files (PATCH request)
        
        Args:
            workflow_data: Current workflow configuration
            uploaded_files_info: List of uploaded file information
            
        Returns:
            bool: True if workflow save was successful
        """
        try:
            workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
            
            # Update the workflow data with uploaded files
            # Find the OpenSearch component and update its file_upload parameter
            for component in workflow_data.get('components', []):
                if component.get('component_id') == 'ai_platform_hosted_opensearch_local_data':
                    model_params = component.get('model_params', {})
                    if 'modelParam' in model_params:
                        if 'file_upload' not in model_params['modelParam']:
                            model_params['modelParam']['file_upload'] = {}
                        
                        # Merge with existing files
                        existing_files = model_params['modelParam']['file_upload'].get('files_uploaded', [])
                        all_files = existing_files + uploaded_files_info
                        
                        # Update file upload configuration
                        model_params['modelParam']['file_upload'].update({
                            "files_uploaded": all_files,
                            "isValid": True
                        })
                    break
            
            # Prepare PATCH request to save workflow
            workflow_url = f"{self.api_base}/workflow/{workflow_id}"
            
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Origin": "https://dataandanalytics.int.thomsonreuters.com",
                "Referer": "https://dataandanalytics.int.thomsonreuters.com/"
            }
            
            response = self.session.patch(
                workflow_url,
                json=workflow_data,
                headers=headers,
                timeout=120  # Longer timeout as this can take time
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    message = result.get('message', 'Workflow updated successfully')
                    print(f"✅ {message}")
                    return True
                except json.JSONDecodeError:
                    print(f"✅ Workflow update successful (HTTP 200)")
                    return True
            else:
                print(f"❌ Workflow save failed: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error saving workflow: {e}")
            return False
    
    def upload_to_s3(self, file_path: Path, s3_url_data: dict) -> bool:
        """
        Upload file directly to S3 using provided credentials
        
        Args:
            file_path: Local file to upload
            s3_url_data: S3 upload data from API response
            
        Returns:
            bool: True if S3 upload was successful
        """
        try:
            s3_url = s3_url_data.get('url')
            s3_fields = s3_url_data.get('fields', {})
            
            if not s3_url or not s3_fields:
                print(f"❌ Invalid S3 upload data for {file_path.name}")
                return False
            
            # Prepare multipart form data
            files = {'file': (file_path.name, open(file_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = s3_fields
            
            # Upload to S3
            response = requests.post(s3_url, data=data, files=files, timeout=60)
            files['file'][1].close()  # Close file handle
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"❌ S3 upload failed for {file_path.name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ S3 upload error for {file_path.name}: {e}")
            return False
    
    def upload_all_files_optimized(self, file_paths: List[Path]) -> bool:
        """
        Upload all files individually with fresh S3 URLs, save workflow only once at end
        This avoids both S3 URL expiration AND multiple deployments
        """
        if not file_paths:
            return False
        
        print(f"🚀 OPTIMIZED UPLOAD STRATEGY:")
        print(f"   📤 Upload {len(file_paths)} files individually (fresh S3 URLs each time)")
        print(f"   💾 Save workflow only ONCE at the end")
        print(f"   🎯 Result: 1 deployment instead of {len(file_paths)} deployments!")
        print()
        
        # Step 1: Get current workflow configuration
        workflow_id = self.workspace_id or "bbccc927-a30c-4f37-8907-968482778d32"
        workflow_url = f"{self.api_base}/workflow/{workflow_id}"
        
        print(f"📋 Getting current workflow configuration...")
        workflow_response = self.session.get(workflow_url)
        
        if workflow_response.status_code != 200:
            print(f"❌ Failed to get workflow configuration: HTTP {workflow_response.status_code}")
            return False
            
        workflow_data = workflow_response.json()
        print(f"✅ Retrieved workflow configuration")
        
        successful_uploads = 0
        failed_uploads = 0
        all_uploaded_files = []  # Accumulate ALL files for single save
        
        # Step 2: Upload each file individually with fresh S3 URL
        for i, file_path in enumerate(file_paths):
            print(f"[{i+1}/{len(file_paths)}] Uploading {file_path.name}...")
            
            try:
                # Get fresh S3 URL for this single file
                headers = {
                    "Content-Type": "application/json; charset=UTF-8",
                    "Origin": "https://dataandanalytics.int.thomsonreuters.com",
                    "Referer": "https://dataandanalytics.int.thomsonreuters.com/"
                }
                
                files_data = [{
                    "file_name": file_path.name,
                    "file_id": str(uuid.uuid4())
                }]
                
                payload = {
                    "asset_id": "204311",
                    "files_names": files_data,
                    "is_rag_storage_request": True,
                    "workflow_id": workflow_id
                }
                
                upload_url = f"{self.base_url}/v3/document/file_upload"
                response = self.session.post(upload_url, json=payload, headers=headers, timeout=60)
                
                if response.status_code != 200:
                    print(f"❌ Failed to get S3 URL: HTTP {response.status_code}")
                    failed_uploads += 1
                    continue
                
                upload_response = response.json()
                s3_uploads = upload_response.get('url', [])
                
                if not s3_uploads:
                    print(f"❌ No S3 upload URL received")
                    failed_uploads += 1
                    continue
                
                s3_url_data = s3_uploads[0].get('url', {})
                
                # Upload to S3 using fresh URL
                if self.upload_to_s3(file_path, s3_url_data):
                    successful_uploads += 1
                    print(f"✅ S3 upload successful: {file_path.name}")
                    
                    # Accumulate file info (DON'T save workflow yet!)
                    all_uploaded_files.append({
                        "file_name": file_path.name,
                        "uploaded_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        "size": f"{file_path.stat().st_size / 1024:.1f} KB"
                    })
                else:
                    failed_uploads += 1
                    print(f"❌ S3 upload failed: {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Error uploading {file_path.name}: {e}")
                failed_uploads += 1
        
        # Step 3: NOW save workflow with ALL uploaded files at once
        if all_uploaded_files:
            print(f"\n💾 Saving workflow with ALL {len(all_uploaded_files)} uploaded files...")
            print(f"🎯 This triggers only 1 deployment instead of {len(all_uploaded_files)} separate deployments!")
            
            if self.save_workflow_with_files(workflow_data, all_uploaded_files):
                print(f"✅ Workflow saved successfully with all {len(all_uploaded_files)} files!")
                print(f"🔄 RAG chain will be re-indexed ONCE")
            else:
                print(f"⚠️ Files uploaded but workflow save failed")
                return False
        
        print(f"\n📊 OPTIMIZED UPLOAD SUMMARY:")
        print(f"✅ Successful uploads: {successful_uploads}")
        print(f"❌ Failed uploads: {failed_uploads}")
        print(f"📁 Total files: {len(file_paths)}")
        print(f"🎯 Deployments triggered: 1 (saved {len(file_paths) - 1} deployments!)")
        
        return failed_uploads == 0
    def upload_file(self, file_path: Path) -> bool:
        """
        Upload a single file using the optimized workflow
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            bool: True if upload was successful
        """
        return self.upload_files_batch([file_path])

def get_excel_files(directory: Path) -> List[Path]:
    """
    Get all Excel files from the specified directory
    
    Args:
        directory: Directory to scan for Excel files
        
    Returns:
        List of Excel file paths
    """
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return []
    
    excel_files = []
    for pattern in ['*.xlsx', '*.xls']:
        excel_files.extend(directory.glob(pattern))
    
    return sorted(excel_files)

def prompt_user_choice(question: str, options: List[str]) -> str:
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
    print("=" * 60)
    print("Open Arena Chain Data Analytics Platform File Uploader")
    print("=" * 60)
    
    # Check for bearer token
    bearer_token = os.getenv('TR_BEARER_TOKEN')
    if not bearer_token:
        print("⚠️ TR_BEARER_TOKEN environment variable not found")
        print("\nYou can either:")
        print("1. Set up a .env file with TR_BEARER_TOKEN=your_token_here")
        print("2. Enter your bearer token now (input will be hidden)")
        print()
        
        try:
            import getpass
            bearer_token = getpass.getpass("Enter your Bearer Token: ").strip()
        except ImportError:
            # Fallback if getpass is not available
            bearer_token = input("Enter your Bearer Token: ").strip()
        
        if not bearer_token:
            print("❌ No bearer token provided. Cannot continue.")
            sys.exit(1)
        
        print("✅ Bearer token entered successfully")
    
    # Get workspace ID
    workspace_id = os.getenv('TR_WORKSPACE_ID')
    if not workspace_id:
        workspace_id = input("\nEnter your workspace ID (optional): ").strip()
        if not workspace_id:
            print("⚠️ No workspace ID provided. Using default workspace for operations.")
    
    # Initialize uploader
    uploader = OpenArenaChainUploader(bearer_token, workspace_id)
    
    # Test authentication
    print("\n📡 Testing authentication...")
    if not uploader.test_authentication():
        print("\n❌ Authentication failed. Please check your bearer token.")
        sys.exit(1)
    
    # Find Excel files
    test_cases_dir = Path("test_cases_by_suite")
    excel_files = get_excel_files(test_cases_dir)
    
    if not excel_files:
        print(f"\n❌ No Excel files found in {test_cases_dir}")
        sys.exit(1)
    
    print(f"\n📁 Found {len(excel_files)} Excel files in {test_cases_dir}")
    
    # Ask about deleting existing files FIRST
    # Check workspace files regardless of user-provided workspace_id (uses default if not provided)
    print("\n🗑️ Checking existing workspace files...")
    existing_files = uploader.list_workspace_files()
    
    if existing_files:
        print(f"Found {len(existing_files)} existing files in workspace")
        
        delete_options = [
            "Delete all existing files before upload",
            "Skip deletion (keep existing files)",
            "Cancel upload"
        ]
        
        delete_choice = prompt_user_choice("How should we handle existing files?", delete_options)
        
        if delete_choice == "Cancel upload":
            print("\nUpload cancelled by user.")
            sys.exit(0)
        elif delete_choice == "Delete all existing files before upload":
            print("\n🗑️ Deleting existing files...")
            
            # Extract filenames from existing files
            filenames_to_delete = []
            for file_info in existing_files:
                filename = file_info.get('name', file_info.get('filename', 'Unknown'))
                if filename != 'Unknown':
                    filenames_to_delete.append(filename)
            
            if filenames_to_delete:
                # Use batch delete with all filenames
                success, deleted_files = uploader.delete_workspace_files(filenames_to_delete)
                
                if success:
                    print(f"\n📊 Deletion summary: {len(deleted_files)} deleted, 0 failed")
                else:
                    failed_count = len(filenames_to_delete)
                    print(f"\n📊 Deletion summary: 0 deleted, {failed_count} failed")
                    
                    continue_options = ["Continue with upload", "Stop and report"]
                    continue_choice = prompt_user_choice("Some deletions failed. What would you like to do?", continue_options)
                    
                    if continue_choice == "Stop and report":
                        print(f"\n❌ Upload stopped due to deletion failures.")
                        print(f"Successfully deleted: 0 files")
                        print(f"Failed to delete: {failed_count} files")
                        sys.exit(1)
            else:
                print("⚠️ No valid filenames found for deletion")
    else:
        print("✅ No existing files found in workspace")
    
    # Now ask about file filtering for upload
    file_options = [
        "Upload all Excel files",
        "Select specific files",
        "Cancel upload"
    ]
    
    file_choice = prompt_user_choice("What files would you like to upload?", file_options)
    
    if file_choice == "Cancel upload":
        print("\nUpload cancelled by user.")
        sys.exit(0)
    
    # Filter files if needed
    files_to_upload = excel_files
    if file_choice == "Select specific files":
        print(f"\n📋 Available files:")
        for i, file_path in enumerate(excel_files, 1):
            print(f"{i:2d}. {file_path.name}")
        
        while True:
            try:
                selection = input("\nEnter file numbers to upload (comma-separated, e.g., 1,3,5): ").strip()
                if not selection:
                    print("No files selected.")
                    continue
                    
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                files_to_upload = [excel_files[i] for i in indices if 0 <= i < len(excel_files)]
                
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
    
    # Upload files using optimized strategy
    print(f"\n� Starting optimized upload of {len(files_to_upload)} files...")
    
    # Confirm upload
    choice = input(f"\nProceed with optimized upload (fresh S3 URLs + single save)? (y/n): ").strip().lower()
    if choice != 'y':
        print("Upload cancelled")
        sys.exit(0)
    
    print("\n🚀 Using OPTIMIZED individual upload strategy...")
    print(f"💡 This prevents S3 URL expiration AND minimizes deployments!")
    
    success = uploader.upload_all_files_optimized(files_to_upload)
    
    if success:
        uploaded_count = len(files_to_upload)
        failed_count = 0
        print(f"✅ All files uploaded successfully with optimized strategy!")
    else:
        # Count actual successes from the method
        uploaded_count = 0
        failed_count = len(files_to_upload)
        print(f"❌ Optimized upload had failures")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully uploaded: {uploaded_count} files")
    print(f"❌ Failed uploads: {failed_count} files")
    print(f"📁 Total files processed: {len(files_to_upload)}")
    
    if failed_count == 0:
        print("\n🎉 All files uploaded successfully!")
    else:
        print(f"\n⚠️ {failed_count} files failed to upload. Please check the error messages above.")
    
    print("\n✨ Upload process completed.")

if __name__ == "__main__":
    main()
