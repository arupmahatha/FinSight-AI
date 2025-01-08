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
    test_query = "what is the gross operating profit of Residence Inn Pasadena for November 2023"
    
    print("\n=== Testing Complete Workflow ===")
    print(f"Input Query: {test_query}")
    
    try:
        # Step 1: Query Understanding and Decomposition
        print("\n1. Query Understanding and Decomposition:")
        
        # Decompose the query first
        decomposed_results = decomposer.decompose_query(test_query)
        print(f"\nDecomposed into {len(decomposed_results)} sub-queries:")
        
        for idx, decomposed in enumerate(decomposed_results, 1):
            print(f"\nSub-query {idx}:")
            print(f"- Type: {decomposed['type']}")
            print(f"- Query: {decomposed['sub_query']}")
            print(f"- Table: {decomposed['table']}")
            
            # Find entities for this specific sub-query
            entities = decomposer.find_entities(decomposed['sub_query'])
            print("\nIdentified Entities:")
            for entity in entities:
                print(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
                print(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
            
            print(f"- Total Entities: {len(decomposed['entities'])}")
            print(f"- Explanation: {decomposed['explanation']}")
        
        all_results = []
        for decomposed in decomposed_results:
            print(f"\nProcessing sub-query: {decomposed['sub_query']}")
            
            # Step 2: SQL Generation
            print("\n2. SQL Generation:")
            # Get table metadata for the generator
            table_info = generator.metadata.get_table_info(decomposed['table'])
            print(f"Using table: {decomposed['table']}")
            print("Available columns:")
            for col, info in table_info.columns.items():
                print(f"- {col}: {info.description}")
            
            sql_query = generator.generate_sql(decomposed)
            print(f"\nGenerated SQL: {sql_query}")
            
            # Step 3: Query Execution
            print("\n3. Query Execution:")
            # First validate the query
            is_valid, error = executor.validate_query(sql_query)
            if is_valid:
                print("SQL validation passed")
                success, results, error = executor.execute_query(sql_query)
                if success:
                    print(f"Execution successful: {len(results)} rows returned")
                    if results:
                        print("\nResults Preview:")
                        headers = results[0].keys()
                        print(" | ".join(str(h) for h in headers))
                        print("-" * 50)
                        for row in results[:3]:  # Show first 3 rows
                            print(" | ".join(str(row[h]) for h in headers))
                    
                    all_results.append({
                        'sub_query': decomposed['sub_query'],
                        'sql_query': sql_query,
                        'results': results
                    })
                else:
                    print(f"Execution failed: {error}")
            else:
                print(f"SQL validation failed: {error}")
        
        # Step 4: Analysis
        if all_results:
            print("\n4. Results Analysis:")
            analysis = analyzer.analyze_results(
                {'original_query': test_query}, 
                all_results
            )
            
            if analysis['success']:
                print("\nAnalysis Results:")
                print(f"\nSuccess: {analysis['success']}")
                print(f"Sub-query count: {analysis['sub_query_count']}")
                print(f"Total result count: {analysis['total_result_count']}")
                print("\nAnalysis:")
                print(f"Summary: {analysis['analysis'].get('summary', 'N/A')}")
                print(f"Insights: {analysis['analysis'].get('insights', 'N/A')}")
                print(f"Trends: {analysis['analysis'].get('trends', 'N/A')}")
                print(f"Implications: {analysis['analysis'].get('implications', 'N/A')}")
                print(f"Relationships: {analysis['analysis'].get('relationships', 'N/A')}")
            else:
                print(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
        else:
            print("\nNo results to analyze")
    
    except Exception as e:
        print(f"\nWorkflow failed: {str(e)}")

if __name__ == "__main__":
    test_full_workflow() 