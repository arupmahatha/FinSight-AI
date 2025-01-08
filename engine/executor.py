from typing import Dict, List, Tuple
import sqlite3
import re

class SQLExecutor:
    # List of dangerous SQL operations to block
    BLOCKED_OPERATIONS = {
        'delete', 'drop', 'truncate', 'update', 'insert', 'replace', 
        'alter', 'create', 'rename', 'modify', 'grant', 'revoke'
    }

    def __init__(self, db_connection: sqlite3.Connection):
        self.connection = db_connection

    def _is_safe_query(self, sql_query: str) -> Tuple[bool, str]:
        """
        Check if the query is safe to execute
        Returns:
            Tuple of (is_safe: bool, error_message: str)
        """
        # Convert to lowercase for checking
        query_lower = sql_query.lower().strip()

        # Must start with SELECT
        if not query_lower.startswith('select'):
            return False, "Only SELECT queries are allowed"

        # Check for blocked operations
        for operation in self.BLOCKED_OPERATIONS:
            # Use regex to find whole words only
            pattern = r'\b' + operation + r'\b'
            if re.search(pattern, query_lower):
                return False, f"Operation '{operation}' is not allowed"

        return True, ""

    def execute_query(self, sql_query: str) -> Tuple[bool, List[Dict], str]:
        """
        Execute SQL query and return results
        
        Returns:
            Tuple containing:
            - success: bool
            - results: List of dictionaries (row results)
            - error: Error message if any
        """
        # First check if query is safe
        is_safe, error_msg = self._is_safe_query(sql_query)
        if not is_safe:
            return False, [], f"Security check failed: {error_msg}"

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch results and convert to list of dicts
            rows = cursor.fetchall()
            results = [
                {columns[i]: value for i, value in enumerate(row)}
                for row in rows
            ]
            
            return True, results, ""
            
        except Exception as e:
            return False, [], str(e)
            
    def validate_query(self, sql_query: str) -> Tuple[bool, str]:
        """
        Validate SQL query before execution
        
        Returns:
            Tuple containing:
            - is_valid: bool
            - error_message: str
        """
        # First check if query is safe
        is_safe, error_msg = self._is_safe_query(sql_query)
        if not is_safe:
            return False, error_msg

        try:
            # Try to compile the query without executing
            cursor = self.connection.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {sql_query}")
            return True, ""
            
        except Exception as e:
            return False, str(e) 