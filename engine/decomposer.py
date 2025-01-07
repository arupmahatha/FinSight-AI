from typing import List, Dict
from anthropic import Anthropic
from engine.metadata import FinancialTableMetadata
from fuzzywuzzy import fuzz
from utils.search import search_financial_terms

class QueryDecomposer:
    def __init__(self, llm: Anthropic):
        self.llm = llm
        self.matcher = None
        self.financial_terms = {}
        self.metadata = FinancialTableMetadata()

    def _decompose_complex_query(self, query: str, chat_history: List[Dict] = None) -> List[str]:
        """Break down complex queries into simpler sub-queries"""
        prompt = f"""Break down this complex query into simple, individual questions. 
        If the query is already simple, return it as is.
        Query: {query}
        
        Format: Return a list of sub-questions."""

        try:
            response = self.llm.invoke(prompt)
            # Split response into individual questions
            sub_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
            return sub_queries if sub_queries else [query]
        except Exception as e:
            print(f"Query decomposition failed: {e}")
            return [query]

    def _select_relevant_table(self, query: str) -> str:
        """Select the most relevant table based on query content using LLM"""
        # Prepare metadata information for the prompt
        tables_info = []
        for table_name, table_def in self.metadata.tables.items():
            table_info = f"""
Table: {table_name}
Description: {table_def.description}
Common Queries: {', '.join(table_def.common_queries)}
Columns: {', '.join(f"{col} ({info.description})" for col, info in table_def.columns.items())}
"""
            tables_info.append(table_info)

        prompt = f"""Given the following query and available tables, select the most appropriate table name.
Only return the table name, nothing else.

Query: {query}

Available Tables:
{'\n'.join(tables_info)}

Table name:"""

        try:
            response = self.llm.invoke(prompt)
            selected_table = response.content.strip()
            
            # Validate the response is an actual table
            if selected_table in self.metadata.tables:
                return selected_table
            
            # Fallback to first table if LLM returns invalid table name
            return list(self.metadata.tables.keys())[0]
        except Exception as e:
            print(f"Table selection failed: {e}")
            return list(self.metadata.tables.keys())[0]

    def _initialize_matcher(self, table_metadata):
        """Initialize the matcher with table metadata"""
        self.financial_terms = {}
        for column_name, column_info in table_metadata.columns.items():
            if column_info.distinct_values:
                self.financial_terms[column_name] = column_info.distinct_values

    def _extract_entities(self, query: str, table_info) -> List[Dict]:
        """
        Extract entities using n-gram based fuzzy matching
        Returns list of matches with column and value information
        """
        matches = search_financial_terms(query, table_info)
        
        # Format matches for generator
        formatted_matches = []
        for match in matches:
            formatted_matches.append({
                'search_term': match['search_term'],
                'column': match['column'],
                'matched_value': match['matched_value'],
                'score': match['score']
            })
        
        return formatted_matches

    def decompose_query(self, query: str, chat_history: List[Dict] = None) -> List[Dict]:
        """Main method to process and decompose queries"""
        try:
            # Step 1: Decompose complex query into simpler sub-queries
            sub_queries = self._decompose_complex_query(query, chat_history)
            
            results = []
            for sub_query in sub_queries:
                # Step 2: Select relevant table for each sub-query
                table_name = self._select_relevant_table(sub_query)
                table_info = self.metadata.get_table_info(table_name)
                
                # Step 3: Initialize matcher with selected table's metadata
                self._initialize_matcher(table_info)
                
                # Step 4: Extract entities based on the selected table
                entities = self._extract_entities(sub_query, table_info)
                
                results.append({
                    'type': 'direct' if len(sub_queries) == 1 else 'decomposed',
                    'original_query': query,
                    'sub_query': sub_query,
                    'table': table_name,
                    'entities': entities,
                    'explanation': f'Query processed using {table_name} table'
                })

            return results

        except Exception as e:
            print(f"Warning: Query decomposition failed: {e}")
            return [{
                'type': 'direct',
                'original_query': query,
                'sub_query': query,
                'entities': [],
                'explanation': 'Direct query (fallback)'
            }] 

    def find_entities(self, query: str) -> List[Dict]:
        """Public method to find entities in a query"""
        # First select the relevant table
        table_name = self._select_relevant_table(query)
        table_info = self.metadata.get_table_info(table_name)
        
        # Initialize matcher with selected table's metadata
        self._initialize_matcher(table_info)
        
        # Extract entities
        entities = self._extract_entities(query, table_info)
        
        # Add table information to each entity
        for entity in entities:
            entity['table'] = table_name
        
        return entities 