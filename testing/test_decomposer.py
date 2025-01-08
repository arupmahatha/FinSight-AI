import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.decomposer import QueryDecomposer
from testing import get_test_llm

def test_decomposer():
    """Test QueryDecomposer functionality"""
    # Initialize
    llm = get_test_llm()
    decomposer = QueryDecomposer(llm)
    
    # Test query
    test_query = "what is the room revenue for ac wailea for the month of dec 2024?"
    
    print("\n=== Testing QueryDecomposer ===")
    print(f"Input Query: {test_query}")
    
    # Test complex query decomposition
    print("\n1. Testing Query Decomposition:")
    sub_queries = decomposer._decompose_complex_query(test_query)
    print("Decomposed Queries:")
    for i, query in enumerate(sub_queries, 1):
        print(f"{i}. {query}")
        
        # Test table selection for each sub-query
        table = decomposer._select_relevant_table(query)
        print(f"\nTable for sub-query {i}: {table}")
        
        # Test entity extraction for each sub-query
        print(f"Entities for sub-query {i}:")
        table_info = decomposer.metadata.get_table_info(table)
        decomposer._initialize_matcher(table_info)
        entities = decomposer._extract_entities(query, table_info)
        for entity in entities:
            print(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
            print(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
    
    # Test full decomposition
    print("\n4. Testing Full Decomposition:")
    results = decomposer.decompose_query(test_query)
    print("Decomposition Results:")
    print(f"\nOriginal Query: {test_query}")
    
    for i, result in enumerate(results, 1):
        print(f"\nSub-query {i}:")
        print(f"- Query: {result['sub_query']}")
        print(f"- Type: {result['type']}")
        print(f"- Table: {result['table']}")
        print(f"- Entities:")
        for entity in result['entities']:
            print(f"  * Found '{entity['search_term']}' in column '{entity['column']}'")
            print(f"    Matched Value: '{entity['matched_value']}' (Score: {entity['score']}')")
        print(f"- Explanation: {result['explanation']}")

if __name__ == "__main__":
    test_decomposer()