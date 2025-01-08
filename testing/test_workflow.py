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
    test_query = "Compare the Room Revenue for AC Wailea and Residence Inn Tampa for Dec 2024"
    
    print("\n=== Testing Complete Workflow ===")
    print(f"Input Query: {test_query}")
    
    try:
        # Step 1: Query Understanding and Decomposition
        print("\n1. Query Understanding and Decomposition:")
        
        # First decompose into sub-queries
        sub_queries = decomposer._decompose_complex_query(test_query)
        print("\nDecomposed Queries:")
        for i, query in enumerate(sub_queries, 1):
            print(f"\nSub-query {i}: {query}")
            
            # Get table for this sub-query
            table = decomposer._select_relevant_table(query)
            print(f"Table: {table}")
            
            # Get entities for this sub-query
            table_info = decomposer.metadata.get_table_info(table)
            decomposer._initialize_matcher(table_info)
            entities = decomposer._extract_entities(query, table_info)
            print("\nIdentified Entities:")
            for entity in entities:
                print(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
                print(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
            
            # Step 2: SQL Generation for this sub-query
            print("\n2. SQL Generation:")
            query_info = {
                'sub_query': query,
                'table': table,
                'entities': entities
            }
            
            print(f"\nGenerating SQL for: {query}")
            print(f"Using table: {table}")
            print("Available columns:")
            for col, info in table_info.columns.items():
                print(f"- {col}: {info.description}")
            
            sql_query = generator.generate_sql(query_info)
            print(f"\nGenerated SQL: {sql_query}")
            
            # Step 3: Query Execution for this sub-query
            print("\n3. Query Execution:")
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
                else:
                    print(f"Execution failed: {error}")
            else:
                print(f"SQL validation failed: {error}")
        
        # Step 4: Final Analysis of all results
        print("\n4. Results Analysis:")
        analysis = analyzer.analyze_results(
            {'original_query': test_query},
            [{'sub_query': q, 'sql_query': sql_query, 'results': results} 
             for q in sub_queries]
        )
        
        if analysis['success']:
            print("\nAnalysis Results:")
            print(f"Success: {analysis['success']}")
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
    
    except Exception as e:
        print(f"\nWorkflow failed: {str(e)}")

if __name__ == "__main__":
    test_full_workflow() 