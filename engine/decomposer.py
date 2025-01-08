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
            sub_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
            return sub_queries if sub_queries else [query]
        except Exception as e:
            print(f"Query decomposition failed: {e}")
            return [query]

    def _select_relevant_table(self, query: str) -> str:
        """Select the most relevant table based on query content using LLM"""
        tables_info = []
        for table_name, table_def in self.metadata.tables.items():
            table_info = (
                f"Table: {table_name}\n"
                f"Description: {table_def.description}\n"
                f"Common Queries: {', '.join(table_def.common_queries)}\n"
                f"Columns: {', '.join(f'{col} ({info.description})' for col, info in table_def.columns.items())}\n"
            )
            tables_info.append(table_info)

        prompt = (
            f"Given the following query and available tables, select the most appropriate table name.\n"
            f"Only return the table name, nothing else.\n\n"
            f"Query: {query}\n\n"
            f"Available Tables:\n{''.join(tables_info)}\n\n"
            "Table name:"
        )

        try:
            response = self.llm.invoke(prompt)
            selected_table = response.content.strip()
            if selected_table in self.metadata.tables:
                return selected_table
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
        """Extract entities using n-gram based fuzzy matching"""
        matches = search_financial_terms(query, table_info)
        return [
            {
                "search_term": match["search_term"],
                "column": match["column"],
                "matched_value": match["matched_value"],
                "score": match["score"],
            }
            for match in matches
        ]

    def decompose_query(self, query: str, chat_history: List[Dict] = None) -> List[Dict]:
        """Main method to process and decompose queries"""
        try:
            sub_queries = self._decompose_complex_query(query, chat_history)
            results = []
            for sub_query in sub_queries:
                table_name = self._select_relevant_table(sub_query)
                table_info = self.metadata.get_table_info(table_name)
                self._initialize_matcher(table_info)
                entities = self._extract_entities(sub_query, table_info)
                results.append({
                    "type": "direct" if len(sub_queries) == 1 else "decomposed",
                    "original_query": query,
                    "sub_query": sub_query,
                    "table": table_name,
                    "entities": entities,
                    "explanation": f"Query processed using {table_name} table",
                })
            return results
        except Exception as e:
            print(f"Warning: Query decomposition failed: {e}")
            return [{
                "type": "direct",
                "original_query": query,
                "sub_query": query,
                "entities": [],
                "explanation": "Direct query (fallback)",
            }]

    def find_entities(self, query: str) -> List[Dict]:
        """Public method to find entities in a query"""
        table_name = self._select_relevant_table(query)
        table_info = self.metadata.get_table_info(table_name)
        self._initialize_matcher(table_info)
        entities = self._extract_entities(query, table_info)
        for entity in entities:
            entity["table"] = table_name
        return entities
