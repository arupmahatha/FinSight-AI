from typing import List, Dict, Tuple
from fuzzywuzzy import fuzz
from nltk import ngrams

def get_ngrams(text: str, n_values: List[int] = [1, 2, 3, 4]) -> List[str]:
    """Generate n-grams from text for given n values"""
    words = text.lower().split()
    all_ngrams = []

    for n in n_values:
        if n <= len(words):
            n_grams = [' '.join(gram) for gram in ngrams(words, n)]
            all_ngrams.extend(n_grams)
    
    # Also include the full text if it's not already in the n-grams
    if text.lower() not in all_ngrams:
        all_ngrams.append(text.lower())
    
    return all_ngrams

def search_financial_terms(search_term: str, table_info, threshold: int = 95) -> List[Dict]:
    """
    Search for financial terms by decomposing search query into n-grams and matching against complete values
    Returns list of matches with column and value information
    """
    matches = []
    
    if not table_info or not table_info.columns:
        return matches
    
    # Generate n-grams ONLY for search term
    search_ngrams = get_ngrams(search_term)
    
    for col_name, col_info in table_info.columns.items():
        if not col_info.distinct_values:
            continue
            
        for value in col_info.distinct_values:
            if not isinstance(value, str):
                value = str(value)
                
            # Find best matching n-grams against the complete value
            best_score = 0
            best_search_term = None
            
            # Try matching full phrases first
            full_score = fuzz.ratio(search_term.lower(), value.lower())
            if full_score >= threshold:
                best_score = full_score
                best_search_term = search_term
            
            # Then try matching each n-gram against the complete value
            for search_gram in search_ngrams:
                score = fuzz.token_sort_ratio(search_gram.lower(), value.lower())
                if score > best_score and score >= threshold:
                    best_score = score
                    best_search_term = search_gram
            
            if best_score > 0:
                matches.append({
                    'search_term': best_search_term,
                    'matched_value': value,  # Keep the complete value
                    'column': col_name,
                    'score': best_score
                })
    
    # Sort by score and remove duplicates keeping highest score
    matches.sort(key=lambda x: (-x['score'], len(x['search_term'].split()), x['matched_value']))
    unique_matches = []
    seen_values = set()
    
    for match in matches:
        key = (match['column'], match['matched_value'])
        if key not in seen_values:
            unique_matches.append(match)
            seen_values.add(key)
    
    return unique_matches

def find_best_match(query: str, table_info, column_name: str) -> Dict:
    """
    Find the best matching value from a specific column regardless of threshold
    
    Args:
        query: The search term to match against
        table_info: Table metadata containing column information
        column_name: The specific column to search in
    
    Returns:
        Dict containing the best match info or None if no match found
    """
    best_match = {
        'search_term': query,
        'column': column_name,
        'matched_value': None,
        'score': 0
    }
    
    if not table_info or not table_info.columns:
        return best_match
        
    column_info = table_info.columns.get(column_name)
    if not column_info or not column_info.distinct_values:
        return best_match
    
    # Match the full query against each value
    for value in column_info.distinct_values:
        if not isinstance(value, str):
            value = str(value)
            
        score = fuzz.token_sort_ratio(query.lower(), value.lower())
        if score > best_match['score']:
            best_match.update({
                'matched_value': value,
                'score': score
            })
    
    return best_match