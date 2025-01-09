import sys
import os
import unittest

# Add the project root directory to the sys.path BEFORE other imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Now import the modules after adding to path
from utils.search import search_financial_terms, get_ngrams
from engine.metadata import FinancialTableMetadata

class TestSearchFinancialTerms(unittest.TestCase):

    def setUp(self):
        # Initialize the metadata and table info for testing
        self.metadata = FinancialTableMetadata()
        self.table_name = "final_income_sheet_new_seq"
        self.table_info = self.metadata.get_table_info(self.table_name)

    def test_search_financial_terms(self):
        # Define test query
        search_term = "what is the room revenue for ac wailea for the month of dec 2024?"
        
        # Step 1: Show n-grams generation
        print("\n=== N-grams Generated ===")
        ngrams_list = get_ngrams(search_term)
        for i, gram in enumerate(ngrams_list, 1):
            print(f"{i}. '{gram}'")
        
        # Step 2: Show matching results
        print("\n=== Matching Results ===")
        matches = search_financial_terms(search_term, self.table_info)
        
        for match in matches:
            print(f"\nFound match in column '{match['column']}':")
            print(f"  Search term used: '{match['search_term']}'")
            print(f"  Matched value: '{match['matched_value']}'")
            print(f"  Match score: {match['score']}")

if __name__ == "__main__":
    unittest.main() 