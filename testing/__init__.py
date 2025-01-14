import sqlite3
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from config import Config

def get_test_db_connection():
    """Get test database connection"""
    return sqlite3.connect("final_working_database.db")

def get_test_llm(model_type: str = "haiku", api_key: str = None):
    """Get test LLM client with appropriate model"""
    if not api_key:
        raise ValueError("API key is required")
    
    # Create base client
    client = Anthropic(api_key=api_key)
    
    # Create a wrapper function that mimics the behavior we want
    def wrapped_client(prompt: str):
        # Choose model based on type
        model = Config.haiku_model if model_type == "haiku" else Config.sonnet_model
        
        response = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1000
        )
        return response.content[0].text
    
    # Add invoke method to match object-style interface
    wrapped_client.api_key = api_key
    wrapped_client.invoke = lambda prompt: type('Response', (), {'content': wrapped_client(prompt)})()
    
    return wrapped_client

# Example usage
if __name__ == "__main__":
    prompt = "what is the room revenue for ac wailea for the month of dec 2024?"
    llm_client = get_test_llm()
    sql_query = llm_client(prompt)
    print(f"Generated SQL Query: {sql_query}")
