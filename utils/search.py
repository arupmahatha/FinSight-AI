from typing import List, Dict
from fuzzywuzzy import fuzz
from ..database.metadata import FinancialTableMetadata

def search_financial_terms(search_term: str, threshold: int = 40) -> List[Dict]:
    """Search for financial terms using fuzzy matching"""
    matches = []
    
    metadata = FinancialTableMetadata()
    table_info = metadata.get_table_info('final_income_sheet_new_seq')
    
    if not table_info or not table_info.columns:
        return matches
    
    for col_name, col_info in table_info.columns.items():
        # Check column name match
        col_score = fuzz.ratio(search_term.lower(), col_name.lower())
        if col_score >= threshold:
            matches.append({
                'term': col_name,
                'column': col_name,
                'score': col_score,
                'type': 'column_name'
            })
        
        # Check description match
        if col_info.description:
            desc_score = fuzz.ratio(search_term.lower(), col_info.description.lower())
            if desc_score >= threshold:
                matches.append({
                    'term': col_info.description,
                    'column': col_name,
                    'score': desc_score,
                    'type': 'description'
                })
        
        # Check distinct values
        if col_info.distinct_values:
            for value in col_info.distinct_values:
                if isinstance(value, str):
                    value_score = fuzz.ratio(search_term.lower(), value.lower())
                    if value_score >= threshold:
                        matches.append({
                            'term': value,
                            'column': col_name,
                            'score': value_score,
                            'type': 'value'
                        })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches