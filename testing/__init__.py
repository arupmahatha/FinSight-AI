import sqlite3
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_test_llm():
    """Get test LLM instance"""
    return Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )

def get_test_db_connection():
    """Get test database connection"""
    return sqlite3.connect("final_working_database.db") 