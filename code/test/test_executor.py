import pandas as pd
import sqlite3
import os
import datetime
import json
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
import re
from dotenv import load_dotenv

@dataclass
class TestResult:
    test_id: str
    query: str
    generated_sql: str
    execution_status: str
    execution_time: float
    result_count: int
    error_message: str = None
    clarification_requested: bool = False

class TestExecutor:
    def __init__(self):
        # Use your API key directly for reliability
        self.groq_api_key = "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"
        
        try:
            self.llm = ChatGroq(model="llama-3.1-8b-instant", api_key=self.groq_api_key)
            print("✅ ChatGroq initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize ChatGroq: {str(e)}")
            
        self.db_schema = self.get_schema()
        self.system_prompt = self._create_system_prompt()
    
    def get_schema(self):
        """Load database schema - CORRECTED PATH"""
        # From code/src/test/ to code/src/data/banking_schema_sqlite.sql
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'banking_schema_sqlite.sql')
        
        print(f"🔍 Looking for schema at: {os.path.abspath(schema_path)}")
        
        if os.path.exists(schema_path):
            print(f"✅ Loading schema from: {schema_path}")
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✅ Schema loaded successfully ({len(content)} characters)")
                    return content
            except Exception as e:
                print(f"❌ Error reading schema: {e}")
        else:
            print(f"❌ Schema file not found at: {os.path.abspath(schema_path)}")
        
        return "-- Schema file not found"
    
    def _create_system_prompt(self):
        return f"""
        You are a highly intelligent SQLite expert. Your task is to convert a user's natural language question into a valid SQLite query.

        **INSTRUCTIONS:**
        1. If the request is ambiguous and you truly cannot generate SQL, ask ONE clarification question (prefixed with `CLARIFICATION:`).
        2. Otherwise, make reasonable assumptions and generate the best possible SQL query directly.
        3. NEVER invent columns or tables — only use what is explicitly in the schema.
        4. Use JOINs correctly (e.g., to get a customer's city, JOIN `customers` with `branches`).
        5. Return ONLY the raw SQL query (or a clarification if absolutely needed). No explanations, no markdown.

        **Schema:**
        ```sql
        {self.db_schema}
        ```
        """

    def run_query(self, query: str):
        """Execute SQL query against database - CORRECTED PATH"""
        # CORRECT PATH: From code/src/test/ to code/src/banking_system.db (outside app folder)
        db_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'banking_system.db')
        
        print(f"🔍 Looking for database at: {os.path.abspath(db_path)}")
        
        if not os.path.exists(db_path):
            # Try absolute path construction as backup
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_db_path = os.path.join(current_script_dir, '..', 'src', 'banking_system.db')
            alt_db_path = os.path.abspath(alt_db_path)
            
            print(f"🔍 Trying alternative absolute path: {alt_db_path}")
            
            if os.path.exists(alt_db_path):
                db_path = alt_db_path
                print(f"✅ Found database at alternative path")
            else:
                return None, f"Database not found at: {os.path.abspath(db_path)} or {alt_db_path}"
        else:
            print(f"✅ Found database at: {os.path.abspath(db_path)}")
                
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df, None
        except Exception as e:
            return None, str(e)
    
    def generate_sql(self, natural_query: str):
        """Convert natural language to SQL using AI"""
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=natural_query)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def execute_test_case(self, test_id: str, query: str) -> TestResult:
        """Execute a single test case"""
        start_time = datetime.datetime.now()
        
        # Generate SQL
        ai_response = self.generate_sql(query)
        
        # Check if clarification is requested
        if ai_response.startswith("CLARIFICATION:"):
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return TestResult(
                test_id=test_id,
                query=query,
                generated_sql=ai_response,
                execution_status="CLARIFICATION_REQUESTED",
                execution_time=execution_time,
                result_count=0,
                clarification_requested=True
            )
        
        # Extract SQL from response
        match = re.search(r'SELECT .*', ai_response, re.IGNORECASE | re.DOTALL)
        sql = match.group(0).strip() if match else ai_response.strip()
        if sql.endswith(';'):
            sql = sql[:-1]
        
        # Execute SQL
        result_df, error = self.run_query(sql)
        end_time = datetime.datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if error:
            return TestResult(
                test_id=test_id,
                query=query,
                generated_sql=sql,
                execution_status="FAILED",
                execution_time=execution_time,
                result_count=0,
                error_message=error
            )
        else:
            return TestResult(
                test_id=test_id,
                query=query,
                generated_sql=sql,
                execution_status="PASSED",
                execution_time=execution_time,
                result_count=len(result_df) if result_df is not None else 0
            )

class TestReportGenerator:
    def __init__(self, test_results: List[TestResult]):
        self.test_results = test_results
        self.timestamp = datetime.datetime.now()
    
    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r.execution_status == "PASSED"])
        failed = len([r for r in self.test_results if r.execution_status == "FAILED"])
        clarification = len([r for r in self.test_results if r.execution_status == "CLARIFICATION_REQUESTED"])
        
        avg_execution_time = sum(r.execution_time for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "clarification_requested": clarification,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "average_execution_time": avg_execution_time
        }
    
    def generate_detailed_report(self) -> pd.DataFrame:
        """Generate detailed test results DataFrame"""
        data = []
        for result in self.test_results:
            data.append({
                "Test_ID": result.test_id,
                "Natural_Language_Query": result.query,
                "Generated_SQL": result.generated_sql,
                "Execution_Status": result.execution_status,
                "Execution_Time_Seconds": result.execution_time,
                "Result_Count": result.result_count,
                "Error_Message": result.error_message,
                "Clarification_Requested": result.clarification_requested
            })
        return pd.DataFrame(data)
    
    def save_html_report(self, filename: str):
        """Generate and save HTML report"""
        summary = self.generate_summary_stats()
        detailed_df = self.generate_detailed_report()
        
        # Truncate long SQL queries for HTML display
        detailed_df_display = detailed_df.copy()
        detailed_df_display['Generated_SQL'] = detailed_df_display['Generated_SQL'].apply(
            lambda x: x[:150] + "..." if len(str(x)) > 150 else x
        )
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Banking AI Assistant Test Execution Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
                .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
                .content {{ padding: 30px; }}
                .summary {{ margin: 30px 0; background: #f8f9fa; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                .summary-table {{ border-collapse: collapse; width: 100%; max-width: 800px; margin: 0 auto; }}
                .summary-table th, .summary-table td {{ border: 1px solid #dee2e6; padding: 20px; text-align: left; }}
                .summary-table th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 600; }}
                .status-passed {{ color: #28a745; font-weight: bold; }}
                .status-failed {{ color: #dc3545; font-weight: bold; }}
                .status-clarification {{ color: #ffc107; font-weight: bold; }}
                .detailed {{ background: #f8f9fa; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                .detailed-table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                .detailed-table th, .detailed-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; font-size: 13px; }}
                .detailed-table th {{ background: linear-gradient(135deg, #495057 0%, #343a40 100%); color: white; font-weight: 600; }}
                .detailed-table td {{ max-width: 250px; overflow: hidden; text-overflow: ellipsis; vertical-align: top; }}
                .metric-value {{ font-size: 32px; font-weight: 800; }}
                h1 {{ margin: 0; font-size: 36px; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                h2 {{ color: #495057; border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 25px; }}
                .highlight {{ background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #2196f3; }}
                .performance-indicator {{ text-align: center; font-size: 18px; font-weight: 600; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏦 Banking AI Assistant Test Report</h1>
                    <p style="margin: 15px 0 0 0; font-size: 20px;"><strong>Generated:</strong> {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0 0 0; font-size: 18px;"><strong>Test Suite:</strong> Natural Language to SQL Conversion</p>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <h2>📊 Executive Summary</h2>
                        <table class="summary-table">
                            <tr><th>Metric</th><th>Value</th></tr>
                            <tr><td>Total Test Cases</td><td class="metric-value">{summary['total_tests']}</td></tr>
                            <tr><td>Successful Executions</td><td class="status-passed metric-value">{summary['passed']}</td></tr>
                            <tr><td>Failed Executions</td><td class="status-failed metric-value">{summary['failed']}</td></tr>
                            <tr><td>Clarifications Needed</td><td class="status-clarification metric-value">{summary['clarification_requested']}</td></tr>
                            <tr><td>Success Rate</td><td class="metric-value" style="color: {'#28a745' if summary['pass_rate'] >= 80 else '#ffc107' if summary['pass_rate'] >= 60 else '#dc3545'};">{summary['pass_rate']:.1f}%</td></tr>
                            <tr><td>Average Response Time</td><td class="metric-value">{summary['average_execution_time']:.3f}s</td></tr>
                        </table>
                        
                        <div class="highlight">
                            <div class="performance-indicator">
                                {'🌟 OUTSTANDING PERFORMANCE!' if summary['pass_rate'] >= 90 else '🎉 EXCELLENT PERFORMANCE!' if summary['pass_rate'] >= 80 else '👍 GOOD PERFORMANCE!' if summary['pass_rate'] >= 70 else '⚠️ NEEDS IMPROVEMENT' if summary['pass_rate'] >= 60 else '🔧 REQUIRES OPTIMIZATION'}
                            </div>
                        </div>
                    </div>
                    
                    <div class="detailed">
                        <h2>📋 Detailed Test Results</h2>
                        {detailed_df_display.to_html(classes='detailed-table', escape=False, index=False)}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def save_excel_report(self, filename: str):
        """Save detailed results to Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = pd.DataFrame([self.generate_summary_stats()])
            summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
            
            # All results sheet
            detailed_df = self.generate_detailed_report()
            detailed_df.to_excel(writer, sheet_name='All_Test_Results', index=False)
            
            # Passed tests sheet
            passed_tests = detailed_df[detailed_df['Execution_Status'] == 'PASSED']
            if not passed_tests.empty:
                passed_tests.to_excel(writer, sheet_name='Successful_Tests', index=False)
            
            # Failed tests sheet
            failed_tests = detailed_df[detailed_df['Execution_Status'] == 'FAILED']
            if not failed_tests.empty:
                failed_tests.to_excel(writer, sheet_name='Failed_Tests', index=False)
        
        return filename

def main():
    """Main test execution function"""
    try:
        print("=" * 100)
        print("🏦 BANKING AI ASSISTANT COMPREHENSIVE TEST SUITE")
        print("=" * 100)
        
        # Debug: Show current working directory and paths
        current_dir = os.path.dirname(__file__)
        print(f"📁 Test executor location: {current_dir}")
        print(f"📁 Working from directory: {os.path.abspath(current_dir)}")
        
        # Read test cases
        test_cases_path = os.path.join(current_dir, 'TestCases.xlsx')
        if not os.path.exists(test_cases_path):
            print(f"❌ Error: TestCases.xlsx not found at {test_cases_path}")
            return
            
        test_cases_df = pd.read_excel(test_cases_path)
        print(f"✅ Loaded {len(test_cases_df)} comprehensive test cases")
        
        # Initialize test executor
        print(f"\n🚀 Initializing Banking AI Test Framework...")
        executor = TestExecutor()
        
        # Create reports directory
        reports_dir = os.path.join(current_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        print(f"📂 Reports will be saved to: {reports_dir}")
        
        # Test database connection first
        print(f"\n🔍 Verifying database connectivity...")
        test_df, error = executor.run_query("SELECT name FROM sqlite_master WHERE type='table' LIMIT 10")
        if error:
            print(f"❌ Database connection failed: {error}")
            return
        else:
            print(f"✅ Database connection established successfully!")
            if test_df is not None and not test_df.empty:
                print(f"📋 Found {len(test_df)} tables: {', '.join(list(test_df['name']))}")
            else:
                print(f"⚠️  Database is empty - no tables found")
        
        # Execute all test cases
        print(f"\n🧪 Executing comprehensive test suite ({len(test_cases_df)} test cases)...")
        print("=" * 100)
        test_results = []
        
        for i, row in test_cases_df.iterrows():
            test_id = str(row['Test Case ID'])
            query = row['Natural Language Query']
            
            print(f"Test {test_id:>2}/35: {query[:70]}{'...' if len(query) > 70 else ''}")
            result = executor.execute_test_case(test_id, query)
            test_results.append(result)
            
            # Detailed status reporting
            if result.execution_status == "PASSED":
                print(f"         ✅ SUCCESS ({result.execution_time:.2f}s) → {result.result_count} rows returned")
            elif result.execution_status == "FAILED":
                print(f"         ❌ FAILED ({result.execution_time:.2f}s)")
                if result.error_message and len(result.error_message) < 80:
                    print(f"         💬 Error: {result.error_message}")
            else:
                print(f"         ❓ CLARIFICATION ({result.execution_time:.2f}s)")
        
        print("=" * 100)
        print("🏁 Test suite execution completed!")
        
        # Generate comprehensive reports
        print(f"\n📊 Generating comprehensive performance reports...")
        report_generator = TestReportGenerator(test_results)
        
        # Save reports with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Professional HTML report
        html_file = os.path.join(reports_dir, f"banking_ai_performance_report_{timestamp}.html")
        report_generator.save_html_report(html_file)
        print(f"🌐 Interactive HTML report: {html_file}")
        
        # Comprehensive Excel report
        excel_file = os.path.join(reports_dir, f"banking_ai_test_results_{timestamp}.xlsx")
        report_generator.save_excel_report(excel_file)
        print(f"📊 Detailed Excel analysis: {excel_file}")
        
        # Final performance assessment
        summary = report_generator.generate_summary_stats()
        print(f"\n" + "=" * 100)
        print("🎯 FINAL PERFORMANCE ASSESSMENT")
        print("=" * 100)
        print(f"📈 Total Test Cases Executed:    {summary['total_tests']}")
        print(f"✅ Successful SQL Generation:    {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)")
        print(f"❌ Failed Executions:            {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)")
        print(f"❓ Clarifications Required:      {summary['clarification_requested']} ({summary['clarification_requested']/summary['total_tests']*100:.1f}%)")
        print(f"🎯 Overall Success Rate:         {summary['pass_rate']:.1f}%")
        print(f"⚡ Average Response Time:        {summary['average_execution_time']:.3f} seconds")
        print("=" * 100)
        
        # Performance categorization
        if summary['pass_rate'] >= 90:
            print("🌟 WORLD-CLASS: Your AI assistant demonstrates exceptional capabilities!")
        elif summary['pass_rate'] >= 80:
            print("🎉 EXCELLENT: Outstanding performance with minor optimization opportunities!")
        elif summary['pass_rate'] >= 70:
            print("👍 GOOD: Solid performance demonstrating strong core capabilities!")
        elif summary['pass_rate'] >= 60:
            print("⚠️  FAIR: Adequate baseline with improvement potential!")
        else:
            print("🔧 NEEDS DEVELOPMENT: Focus on prompt engineering and schema optimization!")
        
        print("=" * 100)
        
    except Exception as e:
        print(f"💥 Critical system error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
