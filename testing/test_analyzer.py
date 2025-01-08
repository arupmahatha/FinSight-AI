import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.analyzer import SQLAnalyzer
from testing import get_test_llm

def test_analyzer():
    """Test SQLAnalyzer functionality"""
    # Initialize
    llm = get_test_llm()
    analyzer = SQLAnalyzer(llm)
    
    # Test data
    # ... existing code ...

    # Test data
    test_query_info = {
        'original_query': "what is the room revenue for ac wailea for the month of dec 2024?",
        'query_type': 'revenue',  # Add query type
        'time_period': 'month',   # Add time period
        'date': '2024-12',        # Add date
        'property': 'AC Wailea'   # Add property
    }
    
    test_results = [{
        'sub_query': "what is the room revenue for ac wailea for the month of dec 2024?",
        'sql_query': "SELECT SQL_Property, Revenue FROM final_income_sheet_new_seq WHERE SQL_Property = 'AC Wailea' AND Date = '2024-12'",
        'results': [
            {'SQL_Property': 'AC Wailea', 'Revenue': 150000, 'Date': '2024-12-01'},
            {'SQL_Property': 'AC Wailea', 'Revenue': 160000, 'Date': '2024-12-02'}
        ]
    }]

# ... existing code ...
    
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
        print("\nSummary:", analysis_results['analysis'].get('summary'))
        print("\nInsights:", analysis_results['analysis'].get('insights'))
        print("\nTrends:", analysis_results['analysis'].get('trends'))
        print("\nImplications:", analysis_results['analysis'].get('implications'))
        print("\nRelationships:", analysis_results['analysis'].get('relationships'))
    else:
        print(f"Analysis failed: {analysis_results.get('error')}")

if __name__ == "__main__":
    test_analyzer() 