from typing import Dict, List
from anthropic import Anthropic
from .metadata import FinancialTableMetadata

class SQLGenerator:
    def __init__(self, llm: Anthropic):
        self.llm = llm
        self.metadata = FinancialTableMetadata()

    def generate_sql(self, query_info: Dict) -> str:
        """
        Generate SQL query from decomposed query info
        
        Args:
            query_info: Dict containing:
                - sub_query: The natural language question
                - table: The target table name 
                - entities: List of matched entities
        """
        # Get table metadata
        table_info = self.metadata.get_table_info(query_info['table'])
        if not table_info:
            raise ValueError(f"Table '{query_info['table']}' not found in metadata")
            
        # Format available columns
        available_columns = self._format_table_schema(table_info)
        
        # Format entity matches for the prompt
        entity_matches = self._format_entity_matches(query_info.get('entities', []), table_info)
        
        prompt = f"""Given the following information, generate a SQL query:

Natural Language Query: {query_info['sub_query']}
Table: {query_info['table']}

Available Columns (ONLY use these columns in your query):
{available_columns}

Matched Values:
{entity_matches}

Requirements:
1. ONLY use columns from the "Available Columns" list above
2. Return a valid SQLite query
3. In WHERE clauses, use ONLY the exact matched values shown above (not the user's input terms)
4. Use proper SQL syntax and formatting
5. Return ONLY the SQL query without any explanation
6. The query must start with SELECT

For example, if there is a match "Found 'apple' in column 'company' matching value 'Apple Inc.'",
use "WHERE company = 'Apple Inc.'" NOT "WHERE company = 'apple'"

SQL Query:"""

        response = self.llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Basic validation
        if not sql_query.lower().startswith('select'):
            raise ValueError("Generated query must start with SELECT")
        
        return sql_query

    def _format_table_schema(self, table_info) -> str:
        """Format available columns for the prompt"""
        schema = []
        for col_name, col_info in table_info.columns.items():
            schema.append(f"- {col_name}: {col_info.description}")
        return "\n".join(schema)

    def _format_entity_matches(self, entity_matches: List[Dict], table_info) -> str:
        """Format entity matches using the pre-matched entities from decomposer"""
        if not entity_matches:
            return "No specific entity matches found"
        
        matches = []
        for match in entity_matches:
            matches.append(
                f"- Found '{match['search_term']}' in column '{match['column']}' "
                f"matching value '{match['matched_value']}'"
            )
        
        return "\n".join(matches) 