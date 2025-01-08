import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_test_llm():
    """Get test LLM instance"""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is not installed. "
            "Please install it using: pip install anthropic"
        )

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def wrapped_client(prompt):
        try:
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract content from the response
            if hasattr(response, 'content') and response.content:
                return response.content[0].text
            return "No content found in response"
            
        except Exception as e:
            print(f"Exception occurred while querying LLM: {e}")
            return f"Exception occurred: {e}"

    # Add a dummy invoke method to maintain compatibility
    wrapped_client.invoke = lambda prompt: type('Response', (), {'content': wrapped_client(prompt)})()
    
    return wrapped_client

def get_test_db_connection():
    """Get test database connection"""
    return sqlite3.connect("final_working_database.db")

# Example usage
if __name__ == "__main__":
    prompt = "what is the room revenue for ac wailea for the month of dec 2024?"
    llm_client = get_test_llm()
    sql_query = llm_client(prompt)
    print(f"Generated SQL Query: {sql_query}")
