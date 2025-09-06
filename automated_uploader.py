"""
Automated Open Arena Chain Uploader
Uploads test case files with minimal prompts - only asks for TR Bearer Token if not in .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def get_bearer_token():
    """Get bearer token from env or prompt user"""
    load_dotenv()
    
    bearer_token = os.getenv('TR_BEARER_TOKEN')
    if bearer_token and bearer_token.strip():
        print("✅ Using TR Bearer Token from .env file")
        return bearer_token.strip()
    
    print("⚠️ TR_BEARER_TOKEN not found or empty in .env file")
    print("Please enter your TR Bearer Token:")
    
    # Import msvcrt for Windows password input
    try:
        import msvcrt
        
        def get_password():
            """Get password input showing asterisks"""
            password = ""
            while True:
                char = msvcrt.getch()
                if char == b'\r':  # Enter key
                    print()  # New line
                    break
                elif char == b'\x08':  # Backspace
                    if len(password) > 0:
                        password = password[:-1]
                        print('\b \b', end='', flush=True)  # Remove last asterisk
                else:
                    password += char.decode('utf-8')
                    print('*', end='', flush=True)
            return password
        
        bearer_token = get_password().strip()
    except ImportError:
        # Fallback for non-Windows systems
        import getpass
        bearer_token = getpass.getpass("Enter your Bearer Token: ").strip()
    
    if not bearer_token:
        print("❌ No bearer token provided. Cannot continue.")
        sys.exit(1)
    
    # Update environment variable for this session
    os.environ['TR_BEARER_TOKEN'] = bearer_token
    print("✅ Bearer token entered successfully")
    return bearer_token


def run_auto_upload():
    """Run automated upload with default options"""
    try:
        # Get bearer token
        bearer_token = get_bearer_token()
        
        # Import the uploader modules
        from open_arena_chain_uploader import OpenArenaChainUploader, get_excel_files
        
        # Get workspace ID from env or use default
        workspace_id = os.getenv('TR_WORKSPACE_ID')
        
        # Initialize uploader
        uploader = OpenArenaChainUploader(bearer_token, workspace_id)
        
        # Test authentication
        print("\n📡 Testing authentication...")
        if not uploader.test_authentication():
            print("❌ Authentication failed. Please check your bearer token.")
            return False
        
        print("✅ Authentication successful")
        
        # Find Excel files
        test_cases_dir = Path("test_cases_by_suite")
        excel_files = get_excel_files(test_cases_dir)
        
        if not excel_files:
            print(f"❌ No Excel files found in {test_cases_dir}")
            print("Please run the test case downloader first.")
            return False
        
        print(f"📁 Found {len(excel_files)} Excel files")
        
        # Auto-delete existing files
        print("\n🗑️ Checking existing workspace files...")
        existing_files = uploader.list_workspace_files()
        
        if existing_files:
            print(f"Found {len(existing_files)} existing files - deleting them...")
            filenames_to_delete = []
            for file_info in existing_files:
                filename = file_info.get('name', file_info.get('filename', 'Unknown'))
                if filename != 'Unknown':
                    filenames_to_delete.append(filename)
            
            if filenames_to_delete:
                success, deleted_files = uploader.delete_workspace_files(filenames_to_delete)
                if success:
                    print(f"✅ Deleted {len(deleted_files)} existing files")
                else:
                    print("⚠️ Some files could not be deleted, continuing anyway...")
        else:
            print("✅ No existing files found")
        
        # Upload all files
        print(f"\n🚀 Uploading {len(excel_files)} files...")
        print("🎯 Using optimized upload strategy...")
        
        success = uploader.upload_all_files_optimized(excel_files)
        
        if success:
            print(f"\n✅ All {len(excel_files)} files uploaded successfully!")
            print("🌐 Files are now available in your Open Arena Chain workspace")
            return True
        else:
            print("\n❌ Some files failed to upload")
            return False
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🚀 Open Arena Chain - Automated Uploader")
    print("=" * 50)
    print("Auto Mode: Uses defaults for all options")
    print("- Delete existing files: YES")
    print("- Upload all files: YES")
    print("- Only prompt: TR Bearer Token (if not in .env)")
    print("=" * 50)
    
    success = run_auto_upload()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
