"""
Lightweight Azure DevOps Test Case Downloader
Alternative version that uses CSV export instead of Excel to avoid pandas dependency
"""

import os
import logging
import csv
import requests
import base64
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import sys
from pathlib import Path
import html

from config import (
    PLAN_ID, SUITE_ID_START, SUITE_ID_END,
    LOG_LEVEL, LOG_FORMAT
)


class LightweightTestCaseDownloader:
    """Lightweight version that exports to CSV instead of Excel"""
    
    def __init__(self):
        """Initialize the downloader with configuration"""
        self.setup_logging()
        self.load_environment()
        self.setup_auth()
        self.test_cases_data = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
        self.logger = logging.getLogger(__name__)
        
    def load_environment(self):
        """Load environment variables"""
        load_dotenv()
        
        self.org_url = os.getenv('AZURE_DEVOPS_ORG_URL')
        self.pat = os.getenv('AZURE_DEVOPS_PAT')
        self.project = os.getenv('AZURE_DEVOPS_DEFAULT_PROJECT')
        
        if not all([self.org_url, self.pat, self.project]):
            raise ValueError("Missing required environment variables. Please check your .env file.")
            
        if self.org_url.endswith('/'):
            self.org_url = self.org_url[:-1]
            
        self.logger.info(f"Loaded configuration for project: {self.project}")
    
    def setup_auth(self):
        """Setup authentication headers for Azure DevOps API"""
        credentials = f":{self.pat}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def make_api_request(self, url: str) -> Dict[str, Any]:
        """Make a request to Azure DevOps REST API"""
        try:
            self.logger.debug(f"Making API request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return {}
    
    def get_test_cases_from_suite(self, plan_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """Get test cases from a specific test suite using Azure DevOps REST API"""
        self.logger.info(f"Fetching test cases from Plan ID: {plan_id}, Suite ID: {suite_id}")
        
        url = f"{self.org_url}/{self.project}/_apis/testplan/Plans/{plan_id}/Suites/{suite_id}/TestCase"
        url += "?api-version=7.0"
        
        try:
            response_data = self.make_api_request(url)
            
            if not response_data:
                self.logger.warning(f"No response data for suite {suite_id}")
                return []
            
            test_cases_raw = response_data if isinstance(response_data, list) else [response_data]
            processed_test_cases = []
            
            for test_case_data in test_cases_raw:
                try:
                    processed_case = self.process_test_case(test_case_data, plan_id, suite_id)
                    if processed_case:
                        processed_test_cases.append(processed_case)
                except Exception as e:
                    self.logger.error(f"Error processing test case in suite {suite_id}: {str(e)}")
                    continue
            
            self.logger.info(f"Retrieved {len(processed_test_cases)} test cases from suite {suite_id}")
            return processed_test_cases
                
        except Exception as e:
            self.logger.error(f"Error fetching test cases from suite {suite_id}: {str(e)}")
            return []
    
    def process_test_case(self, test_case_data: Dict[str, Any], plan_id: int, suite_id: int) -> Dict[str, Any]:
        """Process raw test case data into a standardized format"""
        try:
            work_item = test_case_data.get('workItem', {})
            work_item_fields = work_item.get('workItemFields', [])
            
            fields_dict = {}
            for field in work_item_fields:
                for key, value in field.items():
                    fields_dict[key] = value
            
            steps_html = fields_dict.get('Microsoft.VSTS.TCM.Steps', '')
            steps_text = self.extract_steps_from_html(steps_html)
            
            processed_case = {
                'id': work_item.get('id', ''),
                'title': work_item.get('name', ''),
                'plan_id': plan_id,
                'suite_id': suite_id,
                'suite_name': test_case_data.get('testSuite', {}).get('name', ''),
                'plan_name': test_case_data.get('testPlan', {}).get('name', ''),
                'state': fields_dict.get('System.State', ''),
                'assigned_to': fields_dict.get('System.AssignedTo', ''),
                'priority': fields_dict.get('Microsoft.VSTS.Common.Priority', ''),
                'automation_status': fields_dict.get('Microsoft.VSTS.TCM.AutomationStatus', ''),
                'activated_by': fields_dict.get('Microsoft.VSTS.Common.ActivatedBy', ''),
                'activated_date': fields_dict.get('Microsoft.VSTS.Common.ActivatedDate', ''),
                'state_change_date': fields_dict.get('Microsoft.VSTS.Common.StateChangeDate', ''),
                'work_item_type': fields_dict.get('System.WorkItemType', ''),
                'revision': fields_dict.get('System.Rev', ''),
                'steps': steps_text,
                'order': test_case_data.get('order', ''),
                'project_name': test_case_data.get('project', {}).get('name', ''),
                'project_id': test_case_data.get('project', {}).get('id', '')
            }
            
            return processed_case
            
        except Exception as e:
            self.logger.error(f"Error processing test case data: {str(e)}")
            return {}
    
    def extract_steps_from_html(self, steps_html: str) -> str:
        """Extract readable test steps from HTML format"""
        if not steps_html:
            return ""
        
        try:
            import re
            steps_html = html.unescape(steps_html)
            step_pattern = r'<step[^>]*>.*?</step>'
            steps = re.findall(step_pattern, steps_html, re.DOTALL)
            
            processed_steps = []
            for i, step in enumerate(steps, 1):
                step_text = re.sub(r'<[^>]+>', ' ', step)
                step_text = ' '.join(step_text.split())
                if step_text.strip():
                    processed_steps.append(f"Step {i}: {step_text}")
            
            return '\n'.join(processed_steps) if processed_steps else "No steps available"
            
        except Exception as e:
            self.logger.warning(f"Error extracting steps from HTML: {str(e)}")
            return "Error parsing steps"
    
    def download_all_test_cases(self):
        """Download test cases from all specified suites"""
        self.logger.info(f"Starting download of test cases from suites {SUITE_ID_START} to {SUITE_ID_END}")
        
        total_test_cases = 0
        successful_suites = 0
        failed_suites = 0
        
        for suite_id in range(SUITE_ID_START, SUITE_ID_END + 1):
            try:
                test_cases = self.get_test_cases_from_suite(PLAN_ID, suite_id)
                
                if test_cases:
                    self.test_cases_data.extend(test_cases)
                    total_test_cases += len(test_cases)
                    successful_suites += 1
                else:
                    self.logger.info(f"No test cases found in suite {suite_id}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process suite {suite_id}: {str(e)}")
                failed_suites += 1
                continue
        
        self.logger.info(f"Download completed:")
        self.logger.info(f"  - Total test cases: {total_test_cases}")
        self.logger.info(f"  - Successful suites: {successful_suites}")
        self.logger.info(f"  - Failed suites: {failed_suites}")
    
    def export_to_csv(self):
        """Export test cases data to CSV"""
        if not self.test_cases_data:
            self.logger.warning("No test cases data to export")
            return
        
        try:
            csv_filename = "test_cases_export.csv"
            
            if self.test_cases_data:
                fieldnames = list(self.test_cases_data[0].keys())
                
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.test_cases_data)
                
                self.logger.info(f"Successfully exported {len(self.test_cases_data)} test cases to {csv_filename}")
                
                # Also create a simplified Excel-compatible CSV
                excel_filename = "test_cases_export_excel.csv"
                with open(excel_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.test_cases_data)
                
                self.logger.info(f"Also created Excel-compatible version: {excel_filename}")
                self.print_summary_statistics()
                
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def print_summary_statistics(self):
        """Print summary statistics about the exported data"""
        total_cases = len(self.test_cases_data)
        
        self.logger.info("="*50)
        self.logger.info("EXPORT SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Total Test Cases: {total_cases}")
        
        if self.test_cases_data:
            # Count by state
            states = {}
            automation_status = {}
            
            for case in self.test_cases_data:
                state = case.get('state', 'Unknown')
                states[state] = states.get(state, 0) + 1
                
                auto_status = case.get('automation_status', 'Unknown')
                automation_status[auto_status] = automation_status.get(auto_status, 0) + 1
            
            self.logger.info(f"\nTest Cases by State:")
            for state, count in states.items():
                self.logger.info(f"  {state}: {count}")
            
            self.logger.info(f"\nTest Cases by Automation Status:")
            for status, count in automation_status.items():
                self.logger.info(f"  {status}: {count}")
        
        self.logger.info("="*50)
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("Starting Lightweight Azure DevOps Test Case Downloader")
            self.logger.info(f"Target Organization: {self.org_url}")
            self.logger.info(f"Target Project: {self.project}")
            self.logger.info(f"Plan ID: {PLAN_ID}")
            self.logger.info(f"Suite ID Range: {SUITE_ID_START} - {SUITE_ID_END}")
            
            self.download_all_test_cases()
            self.export_to_csv()
            
            self.logger.info("Test case download completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during execution: {str(e)}")
            raise


def main():
    """Main entry point"""
    try:
        downloader = LightweightTestCaseDownloader()
        downloader.run()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
