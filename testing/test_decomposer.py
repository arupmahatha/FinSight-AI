import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.decomposer import QueryDecomposer
from testing import get_test_llm

def test_decomposer(api_key=None):
    """Test QueryDecomposer functionality"""
    if not api_key:
        # For local testing, try to get from environment
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
    if not api_key:
        raise ValueError("API key is required")
    
    # Initialize with Haiku model
    llm = get_test_llm("sonnet", api_key=api_key)
    decomposer = QueryDecomposer(llm)
    
    # Test query
    test_query = "what is the room sold of hilton garden for the month of november 2023?"
    
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
        
        # Print extracted entities
        print(f"Extracted Entities for sub-query {i}:")
        for entity in entities:
            print(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
            print(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
        
        # Filter entities
        filtered_entities = decomposer._filter_entities(query, entities)
        print(f"Filtered Entities for sub-query {i}:")
        for entity in filtered_entities:
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
        
        # Print extracted entities
        print(f"- Extracted Entities for sub-query {i}:")
        for entity in result['extracted_entities']:
            print(f"  * Found '{entity['search_term']}' in column '{entity['column']}'")
            print(f"    Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
        
        # Print filtered entities
        print(f"- Filtered Entities for sub-query {i}:")
        for entity in result['filtered_entities']:
            print(f"  * Found '{entity['search_term']}' in column '{entity['column']}'")
            print(f"    Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")
        
        print(f"- Explanation: {result['explanation']}")

if __name__ == "__main__":
    test_decomposer()