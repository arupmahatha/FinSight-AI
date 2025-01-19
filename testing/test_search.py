import sys
import os
import unittest
from anthropic import Anthropic
from dotenv import load_dotenv

# Add the project root directory to the sys.path BEFORE other imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Now import the modules after adding to path
from utils.search import search_financial_terms_without_threshold, extract_entities_from_llm
from engine.metadata import FinancialTableMetadata
from testing import get_test_llm  # Import the utility function

class TestSearchFinancialTerms(unittest.TestCase):

    def setUp(self):
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        # Initialize components
        self.metadata = FinancialTableMetadata()
        self.table_name = "final_income_sheet_new_seq"
        self.table_info = self.metadata.get_table_info(self.table_name)
        self.llm = get_test_llm("sonnet", api_key=api_key)

    def test_search_financial_terms_without_threshold(self):
        # Define test query
        sub_query = "Show the EBITD comparison for 2023 between Courtyard Pasadena Old Town and Residence Westshore Tampa."
        
        # Extract entities using the LLM
        entities = extract_entities_from_llm(sub_query, self.llm)
        print(f"\n=== Entities Extracted from LLM ===")
        print(f"Entities: {entities}")

        # Call the search function with the extracted entities
        print("\n=== Matching Results ===")
        matches = search_financial_terms_without_threshold(sub_query, self.table_info, self.llm)
        
        for match in matches:
            print(f"\nFound match in column '{match['column']}':")
            print(f"  Search term used: '{match['search_term']}'")
            print(f"  Matched value: '{match['matched_value']}'")
            print(f"  Match score: {match['score']}")

if __name__ == "__main__":
    unittest.main() 