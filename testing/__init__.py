import sqlite3
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_test_llm():
    """Get test LLM instance"""
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def wrapped_client(prompt):
        try:
            # Send prompt to LLM
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Log the raw response to inspect the structure
            print("Raw Response:", response)
            
            # Check if the response is a dictionary and contains 'content'
            if isinstance(response, dict):
                if 'content' in response:
                    print("Response has 'content' attribute.")
                    print("Response Content:", response['content'])  # Log the content directly
                    if isinstance(response['content'], list) and len(response['content']) > 0:
                        first_block = response['content'][0]
                        if hasattr(first_block, "text"):
                            print("Extracted Text:", first_block.text)  # Log extracted text
                            return first_block.text  # Return the extracted SQL query
                        else:
                            print("Error: TextBlock has no 'text' attribute")
                            return "Error: TextBlock has no 'text' attribute"
                    else:
                        print("Error: Response content is not a valid list")
                        return "Error: Response content is not a valid list"
                else:
                    print("Error: Response dictionary does not contain 'content' key")
                    return "Error: Response dictionary does not contain 'content' key"
            
            # Check if the response is a string
            elif isinstance(response, str):
                print("Response is a string.")
                return response  # If response is a plain string, return it directly
            else:
                print("Error: Unexpected response format.")
                return "Error: Unexpected response format"
        
        except Exception as e:
            print(f"Exception occurred while querying LLM: {e}")
            return f"Exception occurred: {e}"
    
    # Making wrapped_client callable as a function
    wrapped_client.invoke = lambda x: wrapped_client(x)
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
