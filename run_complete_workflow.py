"""
Complete Workflow Runner
Runs both test case downloader and Open Arena Chain uploader in sequence
"""

import subprocess
import sys
import os

def run_script(script_name, args=None):
    """Run a Python script and return success status"""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, cwd=os.getcwd())
        print(f"✅ {script_name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}")
        return False

def main():
    """Run the complete workflow"""
    print("🚀 Starting Complete Test Case Workflow")
    print("=" * 60)
    print("Step 1: Download test cases from Azure DevOps")
    print("Step 2: Upload test cases to Open Arena Chain")
    print("=" * 60)
    
    # Step 1: Run test case downloader
    print("\n📥 STEP 1: Downloading Test Cases from Azure DevOps")
    downloader_success = run_script(
        "test_case_downloader.py", 
        ["--essential", "--output", "separate"]
    )
    
    if not downloader_success:
        print("\n❌ Download failed. Stopping workflow.")
        sys.exit(1)
    
    # Step 2: Run Open Arena Chain uploader
    print("\n📤 STEP 2: Uploading Test Cases to Open Arena Chain")
    uploader_success = run_script("open_arena_chain_uploader.py")
    
    if not uploader_success:
        print("\n❌ Upload failed.")
        sys.exit(1)
    
    print("\n🎉 Complete workflow finished successfully!")
    print("✅ Test cases downloaded and uploaded successfully!")

if __name__ == "__main__":
    main()
