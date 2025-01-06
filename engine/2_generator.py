from typing import Dict, List
from langchain_anthropic import ChatAnthropic
from ..database.metadata import FinancialTableMetadata

class SQLGenerator:
    def __init__(self, llm: ChatAnthropic):
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
        entity_matches = self._format_entity_matches(query_info['entities'], table_info)
        
        prompt = f"""Given the following information, generate a SQL query:

Natural Language Query: {query_info['sub_query']}
Table: {query_info['table']}

Available Columns:
{available_columns}

Matched Values to Use:
{entity_matches}

Requirements:
1. Use ONLY the columns listed above
2. Return a valid SQLite query
3. In WHERE clauses, use ONLY the exact matched values shown above (not the user's input terms)
4. Use proper SQL syntax and formatting
5. Return ONLY the SQL query without any explanation
6. The query must start with SELECT

For example, if there is a match "Found 'apple' in column 'company' matching value 'Apple Inc.'",
use "WHERE company = 'Apple Inc.'" NOT "WHERE company = 'apple'"

SQL Query:"""

        try:
            response = self.llm.invoke(prompt)
            sql_query = response.content.strip()
            
            # Validate the generated query
            self._validate_query(sql_query, table_info)
                
            return sql_query
            
        except Exception as e:
            raise Exception(f"SQL generation failed: {str(e)}")

    def _format_table_schema(self, table_info) -> str:
        """Format available columns for the prompt"""
        schema = []
        for col_name, col_info in table_info.columns.items():
            schema.append(f"- {col_name}: {col_info.description}")
        return "\n".join(schema)

    def _format_entity_matches(self, entities: List[str], table_info) -> str:
        """
        Format entity matches for the prompt, including both the entity and its matched value
        Returns formatted string of matches like:
        - Found 'apple' in column 'company' matching value 'Apple Inc.'
        - Found '2023' in column 'year' matching value '2023'
        """
        matches = []
        for entity in entities:
            # Find which column this entity matched with
            for col_name, col_info in table_info.columns.items():
                if col_info.distinct_values:
                    # Convert all values to strings for comparison
                    distinct_values = [str(v).lower() for v in col_info.distinct_values]
                    for idx, lower_value in enumerate(distinct_values):
                        if entity in lower_value:
                            # Get the original (non-lowercased) value
                            original_value = str(col_info.distinct_values[idx])
                            matches.append(
                                f"- Found '{entity}' in column '{col_name}' matching value '{original_value}'"
                            )
        
        return "\n".join(matches) if matches else "No specific entity matches found"

    def _validate_query(self, sql_query: str, table_info) -> None:
        """Validate the generated query"""
        # Check if query starts with SELECT
        if not sql_query.lower().startswith('select'):
            raise ValueError("Generated query must start with SELECT")
        
        # Validate columns
        self._validate_columns(sql_query, table_info)

    def _validate_columns(self, sql_query: str, table_info) -> None:
        """Validate that only available columns are used"""
        # Simple validation - check if any column name in query isn't in table_info
        available_columns = {col.lower() for col in table_info.columns.keys()}
        
        # Extract column names from SQL (this is a simplified approach)
        words = sql_query.lower().replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
        for i, word in enumerate(words):
            if word in ['select', 'from', 'where', 'group', 'order', 'by', 'and', 'or']:
                continue
            if word not in available_columns and i > 0 and words[i-1] not in ['as', 'from', 'table']:
                raise ValueError(f"Column '{word}' not found in table metadata") 