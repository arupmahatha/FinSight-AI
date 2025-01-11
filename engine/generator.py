from typing import Dict, List
from anthropic import Anthropic
from config import Config
from .metadata import FinancialTableMetadata

class SQLGenerator:
    def __init__(self, llm):
        # Store the wrapped client directly
        self.llm = llm
        self.metadata = FinancialTableMetadata()

    def _call_llm(self, prompt: str) -> str:
        """Helper method to call Claude with consistent parameters"""
        # Use the wrapped client's direct call method
        if hasattr(self.llm, 'invoke'):
            response = self.llm.invoke(prompt)
            return response.content
        elif hasattr(self.llm, 'messages'):
            # Direct Anthropic client call with Sonnet model
            response = self.llm.messages.create(
                model=Config.sonnet_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000
            )
            return response.content[0].text
        else:
            # Direct call to the wrapped function
            return self.llm(prompt)

    def generate_sql(self, query_info: Dict) -> str:
        """
        Generate SQL query from decomposed query info
        
        Args:
            query_info: Dict containing:
                - sub_query: The natural language question
                - table: The target table name 
                - filtered_entities: List of filtered matched entities
        """
        # Get table metadata
        table_info = self.metadata.get_table_info(query_info['table'])
        if not table_info:
            raise ValueError(f"Table '{query_info['table']}' not found in metadata")
            
        # Format available columns
        available_columns = self._format_table_schema(table_info)
        
        # Use the filtered entities from decomposer instead of raw entities
        entity_matches = self._format_entity_matches(query_info.get('filtered_entities', []), table_info)
        
        prompt = f"""Given the following information, generate a SQL query:

Natural Language Query: {query_info['sub_query']}
Table: {query_info['table']}

Available Columns (ONLY use these columns in your query):
{available_columns}

Matched Values:
{entity_matches}

Requirements:
1. ONLY use columns from the "Available Columns" list above
2. For ANY filtering conditions (WHERE, HAVING, etc.):
   - You can ONLY use the exact values listed in "Matched Values" above
   - NO partial matches, LIKE patterns, or any values not explicitly shown in the matches
   - For example, if 'Room Revenue' isn't in the matched values, you cannot use "WHERE column LIKE '%Room Revenue%'"
3. Return a valid SQLite query
4. In WHERE clauses, use the exact matched value (e.g., if match is "Found 'apple' in column 'company' matching value 'Apple Inc.'", use "WHERE company = 'Apple Inc.'" NOT "WHERE company = 'apple'")
5. Use proper SQL syntax and formatting
6. Return ONLY the SQL query without any explanation
7. The query must start with SELECT

SQL Query:"""

        sql_query = self._call_llm(prompt).strip()
        
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
        """Format entity matches using the filtered entities from decomposer"""
        if not entity_matches:
            return "No specific entity matches found"
        
        matches = []
        for match in entity_matches:
            matches.append(
                f"- Found '{match['search_term']}' in column '{match['column']}' "
                f"matching value '{match['matched_value']}'"
            )
        
        return "\n".join(matches) 