import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.executor import SQLExecutor
from testing import get_test_db_connection

def test_executor():
    """Test SQLExecutor functionality"""
    # Initialize
    connection = get_test_db_connection()
    executor = SQLExecutor(connection)
    
    # Test queries
    test_queries = [
        "SELECT SUM(Current_Actual_Month) AS room_sold FROM final_income_sheet_new_seq WHERE SQL_Property = 'Steward Santa Barbara' AND SQL_Account_Category_Order = 'Rooms Sold' AND Month = '2023-11-01'",
        "SELECT * FROM final_income_sheet_new_seq LIMIT 5",
        "DELETE FROM final_income_sheet_new_seq",  # Should be blocked
        "SELECT * FROM final_income_sheet_new_seq; DROP TABLE users",  # Should be blocked
    ]
    
    print("\n=== Testing SQLExecutor ===")
    
    for query in test_queries:
        print(f"\nTesting Query: {query}")
        
        # Test query safety check
        print("\n1. Testing Safety Check:")
        is_safe, error_msg = executor._is_safe_query(query)
        print(f"Is Safe: {is_safe}")
        if error_msg:
            print(f"Error Message: {error_msg}")
        
        # Test query validation
        print("\n2. Testing Query Validation:")
        is_valid, validation_error = executor.validate_query(query)
        print(f"Is Valid: {is_valid}")
        if validation_error:
            print(f"Validation Error: {validation_error}")
        
        # Test query execution
        print("\n3. Testing Query Execution:")
        success, results, error = executor.execute_query(query)
        print(f"Success: {success}")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Results: {len(results)} rows returned")
            if results:
                print("First row sample:")
                print(results[0])

if __name__ == "__main__":
    test_executor() 