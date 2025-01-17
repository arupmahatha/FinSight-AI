from typing import List, Dict
from anthropic import Anthropic
from config import Config
from engine.metadata import FinancialTableMetadata
from fuzzywuzzy import fuzz
from utils.search import search_financial_terms_without_threshold

class QueryDecomposer:
    def __init__(self, llm: Anthropic):
        self.llm = Anthropic(api_key=llm.api_key)  # Create new instance for Haiku
        self.matcher = None
        self.financial_terms = {}
        self.metadata = FinancialTableMetadata()

    def _call_llm(self, prompt: str) -> str:
        """Helper method to call Claude Haiku with consistent parameters"""
        response = self.llm.messages.create(
            model=Config.sonnet_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1000
        )
        return response.content[0].text

    def _decompose_complex_query(self, query: str, chat_history: List[Dict] = None) -> List[str]:
        """Break down complex queries into simpler sub-queries"""
        prompt = f"""Break down this query ONLY if it compares multiple entities or asks for multiple pieces of information.
        If the query is about a single entity or metric, return it unchanged.
        
        Examples:
        1. Input: "What is the Room Revenue for AC Wailea for Dec 2024?"
           Output: ["what is the Room Revenue for AC Wailea for Dec 2024?"]
           
        2. Input: "Compare the Room Revenue for AC Wailea and Residence Inn Tampa for Dec 2024"
           Output: [
               "What is the Room Revenue for AC Wailea for Dec 2024?",
               "What is the Room Revenue for Residence Inn Tampa for Dec 2024?"
           ]
        
        Current Query: {query}
        
        Return the sub-queries as a simple list, one per line. For single queries, return just the original query."""

        try:
            response = self._call_llm(prompt)
            # Clean up the response and split into lines
            sub_queries = [q.strip() for q in response.split('\n') if q.strip() and not q.startswith('[') and not q.startswith(']')]
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
            response = self._call_llm(prompt)
            selected_table = response.strip()
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
        """Extract entities using LLM-based entity extraction and fuzzy matching"""
        # Use the new search function that uses LLM for entity extraction
        matches = search_financial_terms_without_threshold(query, table_info, self._call_llm)
        
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
                extracted_entities = self._extract_entities(sub_query, table_info)
                results.append({
                    "type": "direct" if len(sub_queries) == 1 else "decomposed",
                    "original_query": query,
                    "sub_query": sub_query,
                    "table": table_name,
                    "extracted_entities": extracted_entities,
                    "explanation": f"Query processed using {table_name} table",
                })
            return results
        except Exception as e:
            print(f"Warning: Query decomposition failed: {e}")
            return [{
                "type": "direct",
                "original_query": query,
                "sub_query": query,
                "extracted_entities": [],
                "explanation": "Direct query (fallback)",
            }]

    def find_entities(self, query: str) -> Dict[str, List[Dict]]:
        """Public method to find entities in a query"""
        table_name = self._select_relevant_table(query)
        table_info = self.metadata.get_table_info(table_name)
        self._initialize_matcher(table_info)
        extracted_entities = self._extract_entities(query, table_info)
        for entity in extracted_entities:
            entity["table"] = table_name
        return {
            "extracted_entities": extracted_entities,
        }
