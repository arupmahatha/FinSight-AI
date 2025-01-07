import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.decomposer import QueryDecomposer
from engine.generator import SQLGenerator
from engine.executor import SQLExecutor
from engine.analyzer import SQLAnalyzer
from testing import get_test_llm, get_test_db_connection

def test_full_workflow():
    """Test the complete workflow from query to analysis"""
    # Initialize all components
    llm = get_test_llm()
    connection = get_test_db_connection()
    
    decomposer = QueryDecomposer(llm)
    generator = SQLGenerator(llm)
    executor = SQLExecutor(connection)
    analyzer = SQLAnalyzer(llm)
    
    # Test query
    test_query = "what is the room revenue for ac wailea for the month of dec 2024?"
    
    print("\n=== Testing Complete Workflow ===")
    print(f"Input Query: {test_query}")
    
    try:
        # Step 1: Decomposition
        print("\n1. Query Decomposition:")
        decomposed_results = decomposer.decompose_query(test_query)
        print(f"Decomposed into {len(decomposed_results)} sub-queries")
        
        all_results = []
        for decomposed in decomposed_results:
            print(f"\nProcessing sub-query: {decomposed['sub_query']}")
            
            # Step 2: SQL Generation
            print("\n2. SQL Generation:")
            sql_query = generator.generate_sql(decomposed)
            print(f"Generated SQL: {sql_query}")
            
            # Step 3: Query Execution
            print("\n3. Query Execution:")
            success, results, error = executor.execute_query(sql_query)
            if success:
                print(f"Execution successful: {len(results)} rows returned")
                all_results.append({
                    'sub_query': decomposed['sub_query'],
                    'sql_query': sql_query,
                    'results': results
                })
            else:
                print(f"Execution failed: {error}")
        
        # Step 4: Analysis
        if all_results:
            print("\n4. Results Analysis:")
            analysis = analyzer.analyze_results({'original_query': test_query}, all_results)
            if analysis['success']:
                print("\nAnalysis Results:")
                print(f"Summary: {analysis['analysis'].get('summary')}")
                print(f"Insights: {analysis['analysis'].get('insights')}")
            else:
                print(f"Analysis failed: {analysis.get('error')}")
    
    except Exception as e:
        print(f"\nWorkflow failed: {str(e)}")

if __name__ == "__main__":
    test_full_workflow() 