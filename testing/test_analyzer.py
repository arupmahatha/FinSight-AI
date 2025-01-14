import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.analyzer import SQLAnalyzer
from testing import get_test_llm

def test_analyzer(api_key=None):
    """Test SQLAnalyzer functionality"""
    if not api_key:
        # For local testing, try to get from environment
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
    if not api_key:
        raise ValueError("API key is required")
    
    # Initialize with Haiku model
    llm = get_test_llm("haiku", api_key=api_key)
    analyzer = SQLAnalyzer(llm)
    
    # Test data
    test_query_info = {
        'original_query': "what is the room revenue for ac wailea for the month of dec 2024?"
    }
    
    test_results = [{
        'sub_query': "what is the room revenue for ac wailea for the month of dec 2024?",
        'sql_query': "SELECT SQL_Property, Revenue FROM final_income_sheet_new_seq WHERE SQL_Property = 'AC Wailea' AND Date = '2024-12'",
        'results': [
            {'SQL_Property': 'AC Wailea', 'Revenue': 150000, 'Date': '2024-12-01'},
            {'SQL_Property': 'AC Wailea', 'Revenue': 160000, 'Date': '2024-12-02'}
        ]
    }]
    
    print("\n=== Testing SQLAnalyzer ===")
    print(f"Original Query: {test_query_info['original_query']}")
    
    # Test results formatting
    print("\n1. Testing Results Formatting:")
    formatted_results = analyzer._format_results_for_prompt(test_results[0]['results'])
    print("Formatted Results:")
    print(formatted_results)
    
    # Test sub-queries formatting
    print("\n2. Testing Sub-queries Formatting:")
    formatted_sub_queries = analyzer._format_sub_queries_for_prompt([{
        'sub_query': test_results[0]['sub_query'],
        'sql_query': test_results[0]['sql_query'],
        'results': formatted_results
    }])
    print("Formatted Sub-queries:")
    print(formatted_sub_queries)
    
    # Test full analysis
    print("\n3. Testing Full Analysis:")
    analysis_results = analyzer.analyze_results(test_query_info, test_results)
    print("\nAnalysis Results:")
    if analysis_results['success']:
        analysis = analysis_results['analysis']
        print(f"\nSuccess: {analysis_results['success']}")
        print(f"Sub-query count: {analysis_results['sub_query_count']}")
        print(f"Total result count: {analysis_results['total_result_count']}")
        print("\nAnalysis:")
        print(f"Summary: {analysis.get('summary', 'N/A')}")
        print(f"Insights: {analysis.get('insights', 'N/A')}")
        print(f"Trends: {analysis.get('trends', 'N/A')}")
        print(f"Implications: {analysis.get('implications', 'N/A')}")
        print(f"Relationships: {analysis.get('relationships', 'N/A')}")
    else:
        print(f"Analysis failed: {analysis_results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_analyzer() 