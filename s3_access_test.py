#!/usr/bin/env python3
"""
Simple S3 Access Test

This script tests S3 bucket access with detailed diagnostics.
It checks credentials, bucket access, and permissions.

Usage:
    python s3_access_test.py

Environment Variables (.env file):
    AWS_ACCESS_KEY_ID=your_access_key_here
    AWS_SECRET_ACCESS_KEY=your_secret_key_here
    AWS_SESSION_TOKEN=your_session_token_here (optional)
    AWS_REGION=us-east-1 (optional)
"""

import os
import sys
import json
from datetime import datetime
import logging

# Try to import required packages
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
except ImportError:
    print("❌ boto3 not installed. Installing now...")
    os.system("pip install boto3")
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables directly.")

class S3AccessTester:
    """Test S3 bucket access with comprehensive diagnostics"""
    
    def __init__(self):
        # Configuration from your existing S3 uploader
        self.bucket_name = "a200190-oct-nonprod-us-east-1-service-builds"
        self.aws_account_id = "600627334605" 
        self.region = "us-east-1"
        self.prefix = "testcases/"
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.s3_client = None
        self.sts_client = None
        
    def check_credentials(self):
        """Check AWS credentials configuration"""
        print("\n🔑 Checking AWS Credentials...")
        print("=" * 50)
        
        # Check environment variables
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        aws_region = os.getenv('AWS_REGION', self.region)
        
        if aws_access_key:
            print(f"✅ AWS_ACCESS_KEY_ID: {aws_access_key[:8]}***{aws_access_key[-4:] if len(aws_access_key) > 12 else '***'}")
        else:
            print("❌ AWS_ACCESS_KEY_ID: Not set")
            
        if aws_secret_key:
            print(f"✅ AWS_SECRET_ACCESS_KEY: {aws_secret_key[:4]}***{aws_secret_key[-4:] if len(aws_secret_key) > 8 else '***'}")
        else:
            print("❌ AWS_SECRET_ACCESS_KEY: Not set")
            
        if aws_session_token:
            print(f"✅ AWS_SESSION_TOKEN: {aws_session_token[:10]}...")
        else:
            print("ℹ️  AWS_SESSION_TOKEN: Not set (OK for permanent credentials)")
            
        print(f"✅ AWS_REGION: {aws_region}")
        
        return aws_access_key and aws_secret_key
    
    def initialize_clients(self):
        """Initialize AWS clients"""
        try:
            print("\n🚀 Initializing AWS Clients...")
            print("=" * 50)
            
            # Create session
            session = boto3.Session(region_name=self.region)
            self.s3_client = session.client('s3')
            self.sts_client = session.client('sts')
            
            print("✅ AWS clients initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            return False
    
    def check_identity(self):
        """Check AWS identity using STS"""
        try:
            print("\n👤 Checking AWS Identity...")
            print("=" * 50)
            
            response = self.sts_client.get_caller_identity()
            
            user_id = response.get('UserId', 'Unknown')
            account = response.get('Account', 'Unknown')
            arn = response.get('Arn', 'Unknown')
            
            print(f"✅ User ID: {user_id}")
            print(f"✅ Account: {account}")
            print(f"✅ ARN: {arn}")
            
            if account == self.aws_account_id:
                print(f"✅ Account matches expected: {self.aws_account_id}")
            else:
                print(f"⚠️  Account mismatch! Expected: {self.aws_account_id}, Got: {account}")
            
            return True
            
        except ClientError as e:
            print(f"❌ Failed to get identity: {e}")
            return False
        except NoCredentialsError:
            print("❌ No AWS credentials found")
            return False
        except Exception as e:
            print(f"❌ Unexpected error checking identity: {e}")
            return False
    
    def test_bucket_access(self):
        """Test S3 bucket access"""
        try:
            print(f"\n🪣 Testing S3 Bucket Access: {self.bucket_name}")
            print("=" * 50)
            
            # Test bucket existence and permissions
            print("📡 Testing bucket existence...")
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket exists and is accessible")
            
            # Get bucket region
            try:
                location_response = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
                bucket_region = location_response['LocationConstraint'] or 'us-east-1'
                print(f"✅ Bucket region: {bucket_region}")
                
                if bucket_region != self.region:
                    print(f"⚠️  Region mismatch! Client: {self.region}, Bucket: {bucket_region}")
            except ClientError as e:
                print(f"⚠️  Could not get bucket location: {e}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print("❌ Access denied to S3 bucket")
                print("   Check your IAM permissions for s3:GetBucketLocation and s3:ListBucket")
            elif error_code == '404':
                print(f"❌ Bucket '{self.bucket_name}' not found")
            else:
                print(f"❌ S3 bucket access test failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error testing bucket access: {e}")
            return False
    
    def test_list_objects(self):
        """Test listing objects in the bucket"""
        try:
            print(f"\n📋 Testing List Objects (prefix: {self.prefix})")
            print("=" * 50)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix,
                MaxKeys=10
            )
            
            object_count = response.get('KeyCount', 0)
            print(f"✅ Found {object_count} objects with prefix '{self.prefix}'")
            
            if object_count > 0:
                print("\n📄 Sample objects:")
                for obj in response.get('Contents', [])[:5]:
                    key = obj['Key']
                    size = obj['Size']
                    modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   • {key} ({size:,} bytes, {modified})")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print("❌ Access denied for listing objects")
                print("   Check your IAM permissions for s3:ListBucket")
            else:
                print(f"❌ List objects test failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error listing objects: {e}")
            return False
    
    def test_upload_permissions(self):
        """Test upload permissions with a small test file"""
        try:
            print(f"\n📤 Testing Upload Permissions")
            print("=" * 50)
            
            test_key = f"{self.prefix}test_access_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            test_content = f"S3 access test - {datetime.now().isoformat()}"
            
            # Try to upload
            print(f"📡 Uploading test object: {test_key}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_content.encode('utf-8'),
                ContentType='text/plain'
            )
            print("✅ Upload successful")
            
            # Try to read it back
            print("📡 Reading back test object...")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            content = response['Body'].read().decode('utf-8')
            print("✅ Download successful")
            
            # Clean up - delete test object
            print("🗑️  Cleaning up test object...")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            print("✅ Cleanup successful")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print("❌ Access denied for upload/download operations")
                print("   Check your IAM permissions for s3:PutObject, s3:GetObject, s3:DeleteObject")
            else:
                print(f"❌ Upload permissions test failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error testing upload permissions: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all S3 access tests"""
        print("🔍 S3 Access Comprehensive Test")
        print("=" * 50)
        print(f"Bucket: {self.bucket_name}")
        print(f"Account: {self.aws_account_id}")
        print(f"Region: {self.region}")
        print(f"Prefix: {self.prefix}")
        
        results = {}
        
        # Step 1: Check credentials
        results['credentials'] = self.check_credentials()
        
        if not results['credentials']:
            print("\n❌ Cannot proceed without valid credentials!")
            return results
        
        # Step 2: Initialize clients
        results['clients'] = self.initialize_clients()
        
        if not results['clients']:
            print("\n❌ Cannot proceed without AWS clients!")
            return results
        
        # Step 3: Check identity
        results['identity'] = self.check_identity()
        
        # Step 4: Test bucket access
        results['bucket_access'] = self.test_bucket_access()
        
        # Step 5: Test list objects
        if results['bucket_access']:
            results['list_objects'] = self.test_list_objects()
        else:
            results['list_objects'] = False
        
        # Step 6: Test upload permissions
        if results['bucket_access']:
            results['upload_permissions'] = self.test_upload_permissions()
        else:
            results['upload_permissions'] = False
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 50)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        all_passed = all(results.values())
        print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        if not all_passed:
            print("\n💡 Troubleshooting Tips:")
            if not results.get('credentials'):
                print("   • Set AWS credentials in environment variables or .env file")
            if not results.get('identity'):
                print("   • Check if your credentials are valid and not expired")
            if not results.get('bucket_access'):
                print("   • Verify bucket name and check IAM permissions")
            if not results.get('list_objects'):
                print("   • Add s3:ListBucket permission to your IAM policy")
            if not results.get('upload_permissions'):
                print("   • Add s3:PutObject, s3:GetObject, s3:DeleteObject permissions")
        
        return results

def main():
    """Main execution"""
    tester = S3AccessTester()
    results = tester.run_comprehensive_test()
    
    # Exit code based on results
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()
