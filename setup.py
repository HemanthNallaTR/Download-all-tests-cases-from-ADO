"""
Setup script for Azure DevOps Test Case Downloader
Helps users configure the environment and test connectivity
"""

import os
import sys
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        import subprocess
        
        # First, try to upgrade pip to ensure we have the latest version
        print("  Upgrading pip...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True, check=False)
        
        # Install dependencies one by one with better error handling
        packages = [
            "requests>=2.30.0",
            "python-dotenv>=1.0.0", 
            "openpyxl>=3.1.0",
            "pandas>=2.0.0"
        ]
        
        failed_packages = []
        
        for package in packages:
            print(f"  Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--prefer-binary"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"    ❌ Failed to install {package}")
                failed_packages.append(package)
            else:
                print(f"    ✅ Successfully installed {package}")
        
        if failed_packages:
            print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
            print("💡 Try installing manually:")
            for pkg in failed_packages:
                print(f"   pip install {pkg}")
            return False
        else:
            print("✅ All dependencies installed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {str(e)}")
        print("💡 Try installing manually: pip install -r requirements.txt")
        return False


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example_file = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example_file.exists():
        try:
            # Copy example file to .env
            with open(env_example_file, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual Azure DevOps credentials")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {str(e)}")
            return False
    else:
        print("❌ .env.example file not found")
        return False


def test_ado_connectivity():
    """Test connectivity to Azure DevOps"""
    print("\n🔐 Testing Azure DevOps connectivity...")
    
    load_dotenv()
    
    org_url = os.getenv('AZURE_DEVOPS_ORG_URL')
    pat = os.getenv('AZURE_DEVOPS_PAT')
    project = os.getenv('AZURE_DEVOPS_DEFAULT_PROJECT')
    
    if not all([org_url, pat, project]):
        print("❌ Missing environment variables. Please check your .env file:")
        if not org_url:
            print("  - AZURE_DEVOPS_ORG_URL is missing")
        if not pat:
            print("  - AZURE_DEVOPS_PAT is missing")
        if not project:
            print("  - AZURE_DEVOPS_DEFAULT_PROJECT is missing")
        return False
    
    # Test basic connectivity
    try:
        # Clean up org URL
        if org_url.endswith('/'):
            org_url = org_url[:-1]
        
        # Create auth header
        credentials = f":{pat}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        # Test projects API
        test_url = f"{org_url}/_apis/projects/{project}?api-version=7.0"
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            project_data = response.json()
            print(f"✅ Successfully connected to Azure DevOps")
            print(f"   Project: {project_data.get('name', project)}")
            print(f"   Organization: {org_url}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed. Please check your PAT token")
            return False
        elif response.status_code == 404:
            print(f"❌ Project '{project}' not found or you don't have access")
            return False
        else:
            print(f"❌ Connection failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False


def test_test_plan_access():
    """Test access to the specific test plan"""
    print("\n📋 Testing test plan access...")
    
    load_dotenv()
    
    org_url = os.getenv('AZURE_DEVOPS_ORG_URL')
    pat = os.getenv('AZURE_DEVOPS_PAT')
    project = os.getenv('AZURE_DEVOPS_DEFAULT_PROJECT')
    
    from config import PLAN_ID, SUITE_ID_START
    
    try:
        # Clean up org URL
        if org_url.endswith('/'):
            org_url = org_url[:-1]
        
        # Create auth header
        credentials = f":{pat}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        # Test test plan API
        test_url = f"{org_url}/{project}/_apis/testplan/Plans/{PLAN_ID}?api-version=7.0"
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            plan_data = response.json()
            print(f"✅ Successfully accessed test plan")
            print(f"   Plan ID: {PLAN_ID}")
            print(f"   Plan Name: {plan_data.get('name', 'Unknown')}")
            
            # Test first suite access
            suite_url = f"{org_url}/{project}/_apis/testplan/Plans/{PLAN_ID}/Suites/{SUITE_ID_START}/TestCase?api-version=7.0"
            suite_response = requests.get(suite_url, headers=headers, timeout=10)
            
            if suite_response.status_code == 200:
                print(f"✅ Successfully accessed test suite {SUITE_ID_START}")
                return True
            else:
                print(f"⚠️  Test plan accessible, but suite {SUITE_ID_START} returned status: {suite_response.status_code}")
                return True  # Plan is accessible, suite might just be empty
                
        elif response.status_code == 404:
            print(f"❌ Test plan {PLAN_ID} not found or you don't have access")
            return False
        else:
            print(f"❌ Test plan access failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing test plan access: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("🚀 Azure DevOps Test Case Downloader Setup")
    print("=" * 50)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Create .env file
    if success and not create_env_file():
        success = False
    
    # Test connectivity
    if success and not test_ado_connectivity():
        success = False
        print("\n💡 To fix connectivity issues:")
        print("   1. Make sure your PAT token has the required permissions:")
        print("      - Test Plans (Read)")
        print("      - Work Items (Read)")
        print("   2. Check that your organization URL is correct")
        print("   3. Verify the project name exists and you have access")
    
    # Test test plan access
    if success and not test_test_plan_access():
        success = False
        print("\n💡 To fix test plan access issues:")
        print("   1. Verify the PLAN_ID in config.py is correct")
        print("   2. Make sure you have permissions to access test plans")
        print("   3. Check that the test plan exists in the specified project")
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n🏃 You can now run the downloader:")
        print("   python test_case_downloader.py")
    else:
        print("❌ Setup encountered issues. Please fix the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
