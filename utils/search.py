from typing import List, Dict
from fuzzywuzzy import fuzz

def extract_entities_from_llm(sub_query: str, llm) -> List[str]:
    """Extract entities from the sub-query using the Sonnet LLM"""
    if not callable(llm):
        raise ValueError("LLM must be a callable object")
        
    prompt = f"""Extract the key entities from the following query: '{sub_query}'.
    Example:
        For the query "List the utility expenses for Marriott Crystal City during Q4 2022.",
        the entities extracted would be ['utility', 'Marriott Crystal City']. Just the entities, in comma separated list. Don't extract dates.
    """
    try:
        response = llm(prompt)
        # Assuming the LLM returns a comma-separated list of entities
        entities = [entity.strip().strip("'") for entity in response.split(',') if entity.strip()]
        return entities
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")
        return []

def search_financial_terms_without_threshold(sub_query: str, table_info, llm) -> List[Dict]:
    """
    Search for financial terms by extracting entities from the sub-query using LLM
    and matching against complete values without applying a threshold.
    Returns the best match for each entity across all columns.
    """
    if not table_info or not table_info.columns:
        return []

    # Extract entities from the sub-query using the LLM
    entities = extract_entities_from_llm(sub_query, llm)
    
    if not entities:
        return []

    # Track best match for each entity
    entity_matches = {}

    for entity in entities:
        best_match = None
        best_score = 0

        for col_name, col_info in table_info.columns.items():
            if not col_info.distinct_values:
                continue

            for value in col_info.distinct_values:
                if not isinstance(value, str):
                    value = str(value)

                score = fuzz.token_sort_ratio(entity.lower(), value.lower())
                if score > best_score:
                    best_score = score
                    best_match = {
                        'search_term': entity,
                        'matched_value': value,
                        'column': col_name,
                        'score': score
                    }

        if best_match:
            entity_matches[entity] = best_match

    # Return the best matches list
    return list(entity_matches.values())