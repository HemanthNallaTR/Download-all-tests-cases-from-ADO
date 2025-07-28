"""
Azure DevOps Test Case Downloader
Downloads test cases from Azure DevOps test suites and exports to Excel
Features:
- Creates separate Excel files for each suite
- Essential columns mode (ID, Title, Steps, Expected Results)
- Full details mode (all available fields)
- Proper API response handling and data extraction
Uses Azure DevOps REST APIs directly
"""

import os
import logging
import pandas as pd
import requests
import base64
import json
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import sys
from pathlib import Path
import html
from datetime import datetime

from config import (
    PLAN_ID, SUITE_ID_START, SUITE_ID_END, EXPORT_FILENAME,
    SHEET_NAME, LOG_LEVEL, LOG_FORMAT, TEST_CASE_FIELDS
)


class TestCaseDownloader:
    """Main class for downloading test cases from Azure DevOps with enhanced features"""
    
    def __init__(self, essential_columns_only=False, separate_files_per_suite=True):
        """Initialize the downloader with configuration
        
        Args:
            essential_columns_only: If True, exports only ID, Title, Steps, Expected Results
            separate_files_per_suite: If True, creates separate Excel files for each suite
        """
        self.essential_columns_only = essential_columns_only
        self.separate_files_per_suite = separate_files_per_suite
        self.setup_logging()
        self.load_environment()
        self.setup_auth()
        self.test_cases_data = []
        self.suite_data = {}  # Dictionary to store data by suite
        self.total_test_cases = 0
        self.last_export_filename = None  # Track the last exported filename
        
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
            
        # Clean up org URL to get the base URL
        if self.org_url.endswith('/'):
            self.org_url = self.org_url[:-1]
            
        self.logger.info(f"Loaded configuration for project: {self.project}")
    
    def setup_auth(self):
        """Setup authentication headers for Azure DevOps API"""
        # Create basic auth header with PAT
        credentials = f":{self.pat}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def make_api_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make a request to Azure DevOps REST API with proper error handling"""
        try:
            self.logger.debug(f"Making API request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    return None
            elif response.status_code == 404:
                self.logger.warning(f"Resource not found (404): {url}")
                return None
            elif response.status_code == 401:
                self.logger.error(f"Authentication failed (401). Check your PAT token.")
                return None
            elif response.status_code == 403:
                self.logger.error(f"Access forbidden (403). Check your permissions.")
                return None
            else:
                self.logger.error(f"API request failed with status {response.status_code}")
                self.logger.debug(f"Response: {response.text[:500]}...")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during API request: {str(e)}")
            return None
    
    def get_work_item_details(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """Get full work item details including all fields and test steps"""
        url = f"{self.org_url}/{self.project}/_apis/wit/workitems/{work_item_id}?$expand=all&api-version=7.0"
        response_data = self.make_api_request(url)
        
        if response_data:
            self.logger.debug(f"Retrieved full work item details for {work_item_id}")
            return response_data
        else:
            self.logger.warning(f"Failed to get work item details for {work_item_id}")
            return None
    
    def get_test_cases_from_suite(self, plan_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """Get test cases from a specific test suite using Azure DevOps REST API"""
        self.logger.info(f"Fetching test cases from Plan ID: {plan_id}, Suite ID: {suite_id}")
        
        # Azure DevOps Test Plans REST API endpoint
        url = f"{self.org_url}/{self.project}/_apis/testplan/Plans/{plan_id}/Suites/{suite_id}/TestCase?api-version=7.0"
        
        response_data = self.make_api_request(url)
        
        if response_data is None:
            self.logger.warning(f"No response data for suite {suite_id}")
            return []
        
        try:
            # Handle the Azure DevOps API response format
            if isinstance(response_data, dict) and 'value' in response_data:
                # Standard Azure DevOps response with 'value' array
                test_cases_raw = response_data['value']
                count = response_data.get('count', len(test_cases_raw))
                self.logger.info(f"Suite {suite_id} - API returned {count} test cases")
            elif isinstance(response_data, list):
                # Direct array response
                test_cases_raw = response_data
                self.logger.info(f"Suite {suite_id} - Direct array with {len(test_cases_raw)} test cases")
            elif isinstance(response_data, dict) and 'workItem' in response_data:
                # Single test case response
                test_cases_raw = [response_data]
                self.logger.info(f"Suite {suite_id} - Single test case response")
            else:
                self.logger.warning(f"Unexpected response structure for suite {suite_id}: {list(response_data.keys()) if isinstance(response_data, dict) else type(response_data)}")
                return []
            
            if not test_cases_raw:
                self.logger.info(f"Suite {suite_id} contains no test cases")
                return []
            
            processed_test_cases = []
            
            for test_case_data in test_cases_raw:
                try:
                    processed_case = self.process_test_case(test_case_data, plan_id, suite_id)
                    if processed_case:
                        processed_test_cases.append(processed_case)
                except Exception as e:
                    self.logger.error(f"Error processing test case in suite {suite_id}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Retrieved {len(processed_test_cases)} test cases from suite {suite_id}")
            return processed_test_cases
                
        except Exception as e:
            self.logger.error(f"Error processing response for suite {suite_id}: {str(e)}")
            return []
    
    def process_test_case(self, test_case_data: Dict[str, Any], plan_id: int, suite_id: int) -> Optional[Dict[str, Any]]:
        """Process raw test case data into a standardized format"""
        try:
            work_item = test_case_data.get('workItem', {})
            if not work_item:
                self.logger.warning(f"No workItem found in test case data for suite {suite_id}")
                return None
            
            work_item_id = work_item.get('id')
            work_item_name = work_item.get('name', 'Untitled Test Case')
            
            if not work_item_id:
                self.logger.warning(f"No work item ID found for suite {suite_id}")
                return None
            
            # Get full work item details to access all fields including test steps
            full_work_item = self.get_work_item_details(work_item_id)
            
            if full_work_item:
                fields_dict = full_work_item.get('fields', {})
                self.logger.debug(f"Work item {work_item_id} has {len(fields_dict)} fields")
            else:
                # Fallback to basic fields from test case data
                work_item_fields = work_item.get('workItemFields', [])
                fields_dict = {}
                if isinstance(work_item_fields, list):
                    for field in work_item_fields:
                        if isinstance(field, dict):
                            for key, value in field.items():
                                fields_dict[key] = value
                elif isinstance(work_item_fields, dict):
                    fields_dict = work_item_fields
            
            # Extract test steps
            steps_html = fields_dict.get('Microsoft.VSTS.TCM.Steps', '')
            
            if self.essential_columns_only:
                # Essential mode: only ID, Title, Steps, Expected Results
                test_steps, expected_results = self.extract_test_steps_and_expected(steps_html)
                
                processed_case = {
                    'test_case_id': work_item_id,
                    'title': work_item_name,
                    'test_steps': test_steps,
                    'expected_results': expected_results
                }
            else:
                # Full mode: all available fields
                steps_text = self.extract_steps_from_html(steps_html)
                
                processed_case = {
                    'test_case_id': work_item_id,
                    'title': work_item_name,
                    'plan_id': plan_id,
                    'suite_id': suite_id,
                    'suite_name': test_case_data.get('testSuite', {}).get('name', f'Suite {suite_id}'),
                    'plan_name': test_case_data.get('testPlan', {}).get('name', f'Plan {plan_id}'),
                    'state': fields_dict.get('System.State', fields_dict.get('state', 'Unknown')),
                    'assigned_to': fields_dict.get('System.AssignedTo', fields_dict.get('assignedTo', 'Unassigned')),
                    'priority': fields_dict.get('Microsoft.VSTS.Common.Priority', fields_dict.get('priority', 'Not Set')),
                    'automation_status': fields_dict.get('Microsoft.VSTS.TCM.AutomationStatus', fields_dict.get('automationStatus', 'Not Automated')),
                    'activated_by': fields_dict.get('Microsoft.VSTS.Common.ActivatedBy', fields_dict.get('activatedBy', '')),
                    'activated_date': fields_dict.get('Microsoft.VSTS.Common.ActivatedDate', fields_dict.get('activatedDate', '')),
                    'state_change_date': fields_dict.get('Microsoft.VSTS.Common.StateChangeDate', fields_dict.get('stateChangeDate', '')),
                    'work_item_type': fields_dict.get('System.WorkItemType', fields_dict.get('workItemType', 'Test Case')),
                    'revision': fields_dict.get('System.Rev', fields_dict.get('revision', '')),
                    'area_path': fields_dict.get('System.AreaPath', fields_dict.get('areaPath', '')),
                    'iteration_path': fields_dict.get('System.IterationPath', fields_dict.get('iterationPath', '')),
                    'test_steps': steps_text,
                    'order': test_case_data.get('order', ''),
                    'project_name': test_case_data.get('project', {}).get('name', ''),
                    'project_id': test_case_data.get('project', {}).get('id', ''),
                    'created_date': fields_dict.get('System.CreatedDate', fields_dict.get('createdDate', '')),
                    'created_by': fields_dict.get('System.CreatedBy', fields_dict.get('createdBy', '')),
                    'tags': fields_dict.get('System.Tags', fields_dict.get('tags', ''))
                }
            
            return processed_case
            
        except Exception as e:
            self.logger.error(f"Error processing test case data: {str(e)}")
            return None
    
    def extract_test_steps_and_expected(self, steps_html: str) -> tuple:
        """Extract test steps and expected results separately from HTML format"""
        if not steps_html:
            return "No steps defined", "No expected result defined"
        
        try:
            # Decode HTML entities
            steps_html = html.unescape(steps_html)
            
            # Extract step content between step tags
            step_pattern = r'<step[^>]*>(.*?)</step>'
            steps = re.findall(step_pattern, steps_html, re.DOTALL)
            
            all_steps = []
            all_expected = []
            
            for i, step in enumerate(steps, 1):
                # Extract parameterized strings (action and expected result)
                param_pattern = r'<parameterizedString[^>]*>(.*?)</parameterizedString>'
                params = re.findall(param_pattern, step, re.DOTALL)
                
                if params:
                    # Usually first param is action, second is expected result
                    action = re.sub(r'<[^>]+>', ' ', params[0]) if len(params) > 0 else ""
                    expected = re.sub(r'<[^>]+>', ' ', params[1]) if len(params) > 1 else ""
                    
                    # Clean up whitespace
                    action = ' '.join(action.split()).strip()
                    expected = ' '.join(expected.split()).strip()
                    
                    if action:
                        all_steps.append(f"Step {i}: {action}")
                    if expected:
                        all_expected.append(f"Step {i}: {expected}")
            
            steps_text = '\n'.join(all_steps) if all_steps else "No readable steps found"
            expected_text = '\n'.join(all_expected) if all_expected else "No expected results found"
            
            return steps_text, expected_text
            
        except Exception as e:
            self.logger.warning(f"Error extracting steps from HTML: {str(e)}")
            return "Error parsing test steps", "Error parsing expected results"
    
    def extract_steps_from_html(self, steps_html: str) -> str:
        """Extract readable test steps from HTML format"""
        if not steps_html:
            return ""
        
        try:
            # Simple HTML tag removal and formatting
            # Remove HTML tags but keep content
            import re
            
            # Replace common HTML entities
            steps_html = html.unescape(steps_html)
            
            # Extract step content between step tags
            step_pattern = r'<step[^>]*>.*?</step>'
            steps = re.findall(step_pattern, steps_html, re.DOTALL)
            
            processed_steps = []
            for i, step in enumerate(steps, 1):
                # Remove HTML tags but keep text content
                step_text = re.sub(r'<[^>]+>', ' ', step)
                # Clean up whitespace
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
        self.logger.info(f"Mode: {'Essential columns only' if self.essential_columns_only else 'Full details'}")
        self.logger.info(f"Output: {'Separate files per suite' if self.separate_files_per_suite else 'Single combined file'}")
        
        successful_suites = 0
        failed_suites = 0
        empty_suites = 0
        
        for suite_id in range(SUITE_ID_START, SUITE_ID_END + 1):
            try:
                test_cases = self.get_test_cases_from_suite(PLAN_ID, suite_id)
                
                if test_cases:
                    if self.separate_files_per_suite:
                        self.suite_data[suite_id] = test_cases
                    else:
                        self.test_cases_data.extend(test_cases)
                    
                    self.total_test_cases += len(test_cases)
                    successful_suites += 1
                    self.logger.info(f"Suite {suite_id}: {len(test_cases)} test cases")
                else:
                    empty_suites += 1
                    self.logger.info(f"Suite {suite_id}: No test cases found")
                    
            except Exception as e:
                self.logger.error(f"Failed to process suite {suite_id}: {str(e)}")
                failed_suites += 1
                continue
        
        self.logger.info(f"Download Summary:")
        self.logger.info(f"  - Total test cases: {self.total_test_cases}")
        self.logger.info(f"  - Suites with data: {successful_suites}")
        self.logger.info(f"  - Empty suites: {empty_suites}")
        self.logger.info(f"  - Failed suites: {failed_suites}")
        self.logger.info(f"  - Total suites processed: {SUITE_ID_END - SUITE_ID_START + 1}")
    
    def cleanup_old_files(self, output_dir: Path):
        """Clean up old test case files before creating new ones"""
        try:
            # Find all existing Excel files in the output directory
            existing_files = []
            for pattern in ['*.xlsx', '*.xls']:
                existing_files.extend(output_dir.glob(pattern))
            
            if existing_files:
                self.logger.info(f"🗑️ Cleaning up {len(existing_files)} old test case files...")
                deleted_count = 0
                failed_count = 0
                
                for file_path in existing_files:
                    try:
                        file_path.unlink()  # Delete the file
                        deleted_count += 1
                        self.logger.debug(f"   - Deleted: {file_path.name}")
                    except Exception as e:
                        failed_count += 1
                        self.logger.warning(f"   - Failed to delete {file_path.name}: {e}")
                
                self.logger.info(f"✅ Cleanup completed: {deleted_count} deleted, {failed_count} failed")
            else:
                self.logger.info("📁 No old files found - directory is clean")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error during cleanup: {e}")
            # Continue with export even if cleanup fails
    
    def cleanup_old_single_files(self):
        """Clean up old single export files"""
        try:
            # Find files that match the single export pattern
            current_dir = Path(".")
            base_filename = Path(EXPORT_FILENAME).stem  # e.g., "test_cases_export"
            
            # Look for files like "test_cases_export_*.xlsx"
            pattern = f"{base_filename}_*.xlsx"
            existing_files = list(current_dir.glob(pattern))
            
            # Also look for the original filename without timestamp
            original_file = current_dir / EXPORT_FILENAME
            if original_file.exists():
                existing_files.append(original_file)
            
            if existing_files:
                self.logger.info(f"🗑️ Cleaning up {len(existing_files)} old single export files...")
                deleted_count = 0
                failed_count = 0
                
                for file_path in existing_files:
                    try:
                        file_path.unlink()  # Delete the file
                        deleted_count += 1
                        self.logger.debug(f"   - Deleted: {file_path.name}")
                    except Exception as e:
                        failed_count += 1
                        self.logger.warning(f"   - Failed to delete {file_path.name}: {e}")
                
                self.logger.info(f"✅ Cleanup completed: {deleted_count} deleted, {failed_count} failed")
            else:
                self.logger.info("📁 No old single export files found")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error during single file cleanup: {e}")
            # Continue with export even if cleanup fails
    
    def export_to_excel(self):
        """Export test cases data to Excel based on configuration"""
        if self.separate_files_per_suite:
            self.export_separate_suite_files()
        else:
            self.export_single_file()
    
    def export_separate_suite_files(self):
        """Export each suite to its own Excel file"""
        if not self.suite_data:
            self.logger.warning("No test cases data to export")
            return
        
        try:
            # Create output directory
            output_dir = Path("test_cases_by_suite")
            output_dir.mkdir(exist_ok=True)
            
            # Clean up old files before creating new ones
            self.cleanup_old_files(output_dir)
            
            exported_files = []
            
            for suite_id, test_cases in self.suite_data.items():
                try:
                    # Create DataFrame for this suite
                    df = pd.DataFrame(test_cases)
                    
                    if self.essential_columns_only:
                        # Ensure essential column order
                        column_order = ['test_case_id', 'title', 'test_steps', 'expected_results']
                        df = df.reindex(columns=column_order)
                        filename_suffix = "Essential"
                    else:
                        # Reorder columns for full mode
                        preferred_columns = [
                            'test_case_id', 'title', 'plan_id', 'suite_id', 'plan_name', 'suite_name',
                            'state', 'assigned_to', 'priority', 'automation_status',
                            'activated_by', 'activated_date', 'state_change_date',
                            'work_item_type', 'revision', 'area_path', 'iteration_path',
                            'order', 'project_name', 'project_id', 'test_steps',
                            'created_date', 'created_by', 'tags'
                        ]
                        available_columns = [col for col in preferred_columns if col in df.columns]
                        additional_columns = [col for col in df.columns if col not in preferred_columns]
                        column_order = available_columns + additional_columns
                        df = df[column_order]
                        filename_suffix = "Full"
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"TestCases_Plan{PLAN_ID}_Suite{suite_id}_{filename_suffix}_{timestamp}.xlsx"
                    filepath = output_dir / filename
                    
                    # Export to Excel
                    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name=f"Suite {suite_id}", index=False)
                        
                        # Auto-adjust column widths and formatting
                        worksheet = writer.sheets[f"Suite {suite_id}"]
                        
                        if self.essential_columns_only:
                            # Set specific column widths for essential mode
                            worksheet.column_dimensions['A'].width = 15  # test_case_id
                            worksheet.column_dimensions['B'].width = 50  # title
                            worksheet.column_dimensions['C'].width = 80  # test_steps
                            worksheet.column_dimensions['D'].width = 80  # expected_results
                        else:
                            # Auto-adjust for full mode
                            for column in worksheet.columns:
                                max_length = 0
                                column_letter = column[0].column_letter
                                
                                for cell in column:
                                    try:
                                        cell_value = str(cell.value) if cell.value is not None else ""
                                        if len(cell_value) > max_length:
                                            max_length = len(cell_value)
                                    except:
                                        pass
                                
                                # Set reasonable width limits
                                adjusted_width = min(max(max_length + 2, 10), 80)
                                worksheet.column_dimensions[column_letter].width = adjusted_width
                        
                        # Enable text wrapping for all cells
                        from openpyxl.styles import Alignment
                        for row in worksheet.iter_rows():
                            for cell in row:
                                cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
                    exported_files.append(filepath)
                    self.logger.info(f"✅ Exported Suite {suite_id}: {len(test_cases)} test cases → {filename}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to export suite {suite_id}: {str(e)}")
                    continue
            
            # Create summary file
            self.create_summary_file(output_dir)
            
            self.logger.info(f"✅ Export completed! {len(exported_files)} files created in '{output_dir}' directory")
            
        except Exception as e:
            self.logger.error(f"Error during export: {str(e)}")
            raise
    
    def create_summary_file(self, output_dir: Path):
        """Create a summary Excel file with all test cases"""
        try:
            all_test_cases = []
            for suite_id, test_cases in self.suite_data.items():
                # Add suite ID to each test case for summary
                for test_case in test_cases:
                    test_case_with_suite = test_case.copy()
                    if 'suite_id' not in test_case_with_suite:
                        test_case_with_suite['suite_id'] = suite_id
                    all_test_cases.append(test_case_with_suite)
            
            if all_test_cases:
                df = pd.DataFrame(all_test_cases)
                
                if self.essential_columns_only:
                    # Include suite_id in essential summary
                    column_order = ['suite_id', 'test_case_id', 'title', 'test_steps', 'expected_results']
                    filename_suffix = "Essential"
                else:
                    # Full summary with all columns
                    preferred_columns = [
                        'suite_id', 'test_case_id', 'title', 'plan_id', 'plan_name', 'suite_name',
                        'state', 'assigned_to', 'priority', 'automation_status',
                        'activated_by', 'activated_date', 'state_change_date',
                        'work_item_type', 'revision', 'area_path', 'iteration_path',
                        'order', 'project_name', 'project_id', 'test_steps',
                        'created_date', 'created_by', 'tags'
                    ]
                    available_columns = [col for col in preferred_columns if col in df.columns]
                    additional_columns = [col for col in df.columns if col not in preferred_columns]
                    column_order = available_columns + additional_columns
                    filename_suffix = "Full"
                
                df = df.reindex(columns=column_order)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_file = output_dir / f"TestCases_Plan{PLAN_ID}_Summary_{filename_suffix}_{timestamp}.xlsx"
                
                with pd.ExcelWriter(summary_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name="All Test Cases", index=False)
                    
                    # Auto-adjust column widths and enable wrapping
                    worksheet = writer.sheets["All Test Cases"]
                    
                    if self.essential_columns_only:
                        worksheet.column_dimensions['A'].width = 12  # suite_id
                        worksheet.column_dimensions['B'].width = 15  # test_case_id
                        worksheet.column_dimensions['C'].width = 50  # title
                        worksheet.column_dimensions['D'].width = 80  # test_steps
                        worksheet.column_dimensions['E'].width = 80  # expected_results
                    else:
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            
                            for cell in column:
                                try:
                                    cell_value = str(cell.value) if cell.value is not None else ""
                                    if len(cell_value) > max_length:
                                        max_length = len(cell_value)
                                except:
                                    pass
                            
                            adjusted_width = min(max(max_length + 2, 10), 80)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    # Enable text wrapping
                    from openpyxl.styles import Alignment
                    for row in worksheet.iter_rows():
                        for cell in row:
                            cell.alignment = Alignment(wrap_text=True, vertical='top')
                
                self.logger.info(f"✅ Created summary file: {summary_file.name}")
                
        except Exception as e:
            self.logger.error(f"Failed to create summary file: {str(e)}")
    
    def export_single_file(self):
        """Export all test cases to a single Excel file (legacy mode)"""
        if not self.test_cases_data:
            self.logger.warning("No test cases data to export")
            return
        
        try:
            # Clean up old single export files
            self.cleanup_old_single_files()
            
            # Create DataFrame
            df = pd.DataFrame(self.test_cases_data)
            
            if self.essential_columns_only:
                column_order = ['test_case_id', 'title', 'test_steps', 'expected_results']
                df = df.reindex(columns=column_order)
            else:
                # Reorder columns for better readability
                preferred_columns = [
                    'test_case_id', 'title', 'plan_id', 'suite_id', 'plan_name', 'suite_name',
                    'state', 'assigned_to', 'priority', 'automation_status',
                    'activated_by', 'activated_date', 'state_change_date',
                    'work_item_type', 'revision', 'order', 'project_name', 'project_id', 'test_steps'
                ]
                
                # Use preferred order for existing columns, then add any additional columns
                available_columns = [col for col in preferred_columns if col in df.columns]
                additional_columns = [col for col in df.columns if col not in preferred_columns]
                column_order = available_columns + additional_columns
                
                df = df[column_order]
            
            # Export to Excel with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = Path(EXPORT_FILENAME).stem  # Get filename without extension
            export_path = Path(f"{base_filename}_{timestamp}.xlsx")
            self.last_export_filename = str(export_path)  # Store for reference
            
            with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[SHEET_NAME]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            cell_value = str(cell.value) if cell.value is not None else ""
                            if len(cell_value) > max_length:
                                max_length = len(cell_value)
                        except:
                            pass
                    
                    # Set reasonable width limits
                    adjusted_width = min(max(max_length + 2, 10), 100)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.logger.info(f"Successfully exported {len(df)} test cases to {export_path}")
            
            # Print summary statistics
            self.print_summary_statistics(df)
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            raise
    
    def print_summary_statistics(self, df: pd.DataFrame):
        """Print summary statistics about the exported data"""
        self.logger.info("="*50)
        self.logger.info("EXPORT SUMMARY")
        self.logger.info("="*50)
        
        total_cases = len(df)
        unique_suites = df['suite_id'].nunique()
        unique_plans = df['plan_id'].nunique()
        
        self.logger.info(f"Total Test Cases: {total_cases}")
        self.logger.info(f"Unique Test Suites: {unique_suites}")
        self.logger.info(f"Unique Test Plans: {unique_plans}")
        
        # Statistics by state
        if 'state' in df.columns:
            state_counts = df['state'].value_counts()
            self.logger.info(f"\nTest Cases by State:")
            for state, count in state_counts.items():
                self.logger.info(f"  {state}: {count}")
        
        # Statistics by automation status
        if 'automation_status' in df.columns:
            automation_counts = df['automation_status'].value_counts()
            self.logger.info(f"\nTest Cases by Automation Status:")
            for status, count in automation_counts.items():
                self.logger.info(f"  {status}: {count}")
        
        # Suite range
        if 'suite_id' in df.columns and not df.empty:
            min_suite = df['suite_id'].min()
            max_suite = df['suite_id'].max()
            self.logger.info(f"\nSuite ID Range: {min_suite} - {max_suite}")
        
        self.logger.info("="*50)
    
    def run(self):
        """Main execution method"""
        try:
            mode_desc = "Essential" if self.essential_columns_only else "Full"
            output_desc = "Separate suite files" if self.separate_files_per_suite else "Single combined file"
            
            self.logger.info("Starting Azure DevOps Test Case Downloader")
            self.logger.info(f"Target Organization: {self.org_url}")
            self.logger.info(f"Target Project: {self.project}")
            self.logger.info(f"Plan ID: {PLAN_ID}")
            self.logger.info(f"Suite ID Range: {SUITE_ID_START} - {SUITE_ID_END}")
            self.logger.info(f"Mode: {mode_desc} columns")
            self.logger.info(f"Output: {output_desc}")
            
            # Download test cases
            self.download_all_test_cases()
            
            # Export to Excel
            self.export_to_excel()
            
            self.logger.info("✅ Test case download completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during execution: {str(e)}")
            raise


def main():
    """Main entry point with mode selection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Azure DevOps Test Case Downloader')
    parser.add_argument('--essential', action='store_true', 
                       help='Export only essential columns (ID, Title, Steps, Expected Results)')
    parser.add_argument('--single-file', action='store_true',
                       help='Export to single file instead of separate files per suite')
    parser.add_argument('--mode', choices=['essential', 'full'], default='full',
                       help='Choose export mode: essential (4 columns) or full (all columns)')
    parser.add_argument('--output', choices=['separate', 'single'], default='separate',
                       help='Choose output format: separate files per suite or single combined file')
    
    args = parser.parse_args()
    
    # Determine modes
    essential_mode = args.essential or args.mode == 'essential'
    separate_files = not args.single_file and args.output == 'separate'
    
    try:
        print("🚀 Azure DevOps Test Case Downloader")
        print("=" * 50)
        print(f"Mode: {'Essential (4 columns)' if essential_mode else 'Full (all columns)'}")
        print(f"Output: {'Separate files per suite' if separate_files else 'Single combined file'}")
        print(f"Plan ID: {PLAN_ID}")
        print(f"Suite Range: {SUITE_ID_START} - {SUITE_ID_END}")
        print("=" * 50)
        
        downloader = TestCaseDownloader(
            essential_columns_only=essential_mode,
            separate_files_per_suite=separate_files
        )
        downloader.run()
        
        print("\n✅ Download completed successfully!")
        
        if separate_files:
            print("📁 Check the 'test_cases_by_suite' directory for your files")
            if essential_mode:
                print("📋 Files contain: Test Case ID, Title, Test Steps, Expected Results")
            else:
                print("📋 Files contain: All available test case fields")
        else:
            filename_to_show = downloader.last_export_filename if downloader.last_export_filename else EXPORT_FILENAME
            print(f"📄 Check '{filename_to_show}' for your test cases")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
