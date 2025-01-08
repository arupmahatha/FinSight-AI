import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.generator import SQLGenerator
from testing import get_test_llm

def test_generator():
    """Test SQLGenerator functionality"""
    # Initialize
    llm = get_test_llm()
    generator = SQLGenerator(llm)
    
    # Test query info
    test_query_info = {
        'sub_query': "what is the room revenue for ac wailea for the month of dec 2024?",
        'table': "final_income_sheet_new_seq",
        'entities': [
            {
                'search_term': 'ac wailea',
                'column': 'SQL_Property',
                'matched_value': 'AC Wailea',
                'score': 100
            },
            {
                'search_term': 'room revenue',
                'column': 'SQL_Account_Category_Order',
                'matched_value': 'Room Revenue',
                'score': 100
            }
        ]
    }
    
    print("\n=== Testing SQLGenerator ===")
    print(f"Input Query Info:")
    print(f"Sub-query: {test_query_info['sub_query']}")
    print(f"Table: {test_query_info['table']}")
    print(f"Entities: {test_query_info['entities']}")
    
    # Test table schema formatting
    print("\n1. Testing Table Schema Formatting:")
    table_info = generator.metadata.get_table_info(test_query_info['table'])
    schema = generator._format_table_schema(table_info)
    print("Available Columns:")
    print(schema)
    
    # Test entity matches formatting
    print("\n2. Testing Entity Matches Formatting:")
    entity_matches = generator._format_entity_matches(test_query_info['entities'], table_info)
    print("Formatted Entity Matches:")
    print(entity_matches)
    
    # Test SQL generation
    print("\n3. Testing SQL Generation:")
    try:
        sql_query = generator.generate_sql(test_query_info)
        print("Generated SQL Query:")
        print(sql_query)
    except Exception as e:
        print(f"Error generating SQL: {str(e)}")

if __name__ == "__main__":
    test_generator() 