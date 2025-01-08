from typing import List, Dict, Tuple
from fuzzywuzzy import fuzz
from nltk import ngrams

def get_ngrams(text: str, n_values: List[int] = [1, 2, 3]) -> List[str]:
    """Generate n-grams from text for given n values"""
    words = text.lower().split()
    all_ngrams = []
    
    for n in n_values:
        if n <= len(words):
            n_grams = [' '.join(gram) for gram in ngrams(words, n)]
            all_ngrams.extend(n_grams)
    
    return all_ngrams

def search_financial_terms(search_term: str, table_info, threshold: int = 100) -> List[Dict]:
    """
    Search for financial terms using n-gram based fuzzy matching
    Returns list of matches with column and value information
    """
    matches = []
    
    if not table_info or not table_info.columns:
        return matches
    
    # Generate n-grams from search term
    search_ngrams = get_ngrams(search_term)
    
    for col_name, col_info in table_info.columns.items():
        if not col_info.distinct_values:
            continue
            
        for value in col_info.distinct_values:
            if not isinstance(value, str):
                value = str(value)
                
            # Generate n-grams for the current value
            value_ngrams = get_ngrams(value)
            
            # Find best matching n-grams
            best_score = 0
            best_match = None
            
            for search_gram in search_ngrams:
                for value_gram in value_ngrams:
                    score = fuzz.ratio(search_gram.lower(), value_gram.lower())
                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = {
                            'search_term': search_gram,
                            'matched_value': value,
                            'column': col_name,
                            'score': score
                        }
            
            if best_match:
                matches.append(best_match)
    
    # Sort by score and remove duplicates keeping highest score
    matches.sort(key=lambda x: x['score'], reverse=True)
    unique_matches = []
    seen_values = set()
    
    for match in matches:
        key = (match['column'], match['matched_value'])
        if key not in seen_values:
            unique_matches.append(match)
            seen_values.add(key)
    
    return unique_matches