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
    print(f"Decomposed Queries: {sub_queries}")
    
    # Test table selection
    print("\n2. Testing Table Selection:")
    table = decomposer._select_relevant_table(test_query)
    print(f"Selected Table: {table}")
    
    # Test entity extraction
    print("\n3. Testing Entity Extraction:")
    table_info = decomposer.metadata.get_table_info(table)
    decomposer._initialize_matcher(table_info)
    entities = decomposer._extract_entities(test_query, table_info)
    print("Extracted Entities:")
    for entity in entities:
        print(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
        print(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
    
    # Test full decomposition
    print("\n4. Testing Full Decomposition:")
    results = decomposer.decompose_query(test_query)
    print("Decomposition Results:")
    for result in results:
        print(f"\nType: {result['type']}")
        print(f"Original Query: {result['original_query']}")
        print(f"Sub-query: {result['sub_query']}")
        print(f"Table: {result['table']}")
        print(f"Entities: {len(result['entities'])} found")
        print(f"Explanation: {result['explanation']}")

if __name__ == "__main__":
    test_decomposer() 