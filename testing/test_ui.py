import streamlit as st
import sys
import os
import uuid
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import testing workflow components
from engine.decomposer import QueryDecomposer
from engine.generator import SQLGenerator
from engine.executor import SQLExecutor
from engine.analyzer import SQLAnalyzer
from testing import get_test_llm, get_test_db_connection
from ui.manager import ChatManager

def initialize_session_state():
    """Initialize or reset session state"""
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'initialized': True,
            'current_chat_id': str(uuid.uuid4()),
            'messages': [],
            'query': '',
            'sub_queries': [],
            'results': [],
            'analysis': None,
            'api_key_set': False,
        })

def render_sidebar(chat_manager: ChatManager):
    """Render the sidebar with configuration and chat management"""
    with st.sidebar:
        st.title("Configuration Settings")
        api_key = st.text_input("Anthropic API Key:", type="password", placeholder="Enter your API key here")
        
        if api_key:
            st.session_state.api_key_set = True
        
        st.title("Conversation Management")
        
        if st.button("Start New Analysis", type="primary",
                     key="new_chat_button",
                     disabled=not st.session_state.api_key_set):
            handle_new_chat(chat_manager)

        render_chat_history(chat_manager)
    
    return api_key

def handle_new_chat(chat_manager: ChatManager):
    """Handle creation of a new chat"""
    if st.session_state.messages:
        chat_manager.save_chat(
            st.session_state.current_chat_id,
            st.session_state.messages
        )
    
    new_chat_id = str(uuid.uuid4())
    st.session_state.update({
        'current_chat_id': new_chat_id,
        'messages': [],
        'query': '',
        'sub_queries': [],
        'results': [],
        'analysis': None
    })
    st.rerun()

def render_chat_history(chat_manager: ChatManager):
    """Render the chat history sidebar"""
    st.title("Chat History")
    chats = chat_manager.load_chats()
    
    for chat_id, chat_data in chats.items():
        with st.expander(f"📝 {chat_data['title']}", expanded=False):
            st.write(f"Created: {datetime.fromisoformat(chat_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load Chat", key=f"load_{chat_id}"):
                    handle_load_chat(chat_manager, chat_id, chat_data)
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{chat_id}"):
                    handle_delete_chat(chat_manager, chat_id)

def handle_load_chat(chat_manager: ChatManager, chat_id: str, chat_data: dict):
    """Handle loading a chat"""
    st.session_state.messages = chat_data['messages']
    st.session_state.current_chat_id = chat_id
    st.rerun()

def handle_delete_chat(chat_manager: ChatManager, chat_id: str):
    """Handle deleting a chat"""
    chat_manager.delete_chat(chat_id)
    if chat_id == st.session_state.current_chat_id:
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
    st.rerun()

def run_workflow(query: str, chat_manager: ChatManager):
    """Run the testing workflow using backend components"""
    try:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": query
        })

        # Initialize components with appropriate models
        llm_haiku = get_test_llm("haiku")
        llm_sonnet = get_test_llm("sonnet")
        connection = get_test_db_connection()

        decomposer = QueryDecomposer(llm_haiku)
        generator = SQLGenerator(llm_sonnet)
        executor = SQLExecutor(connection)
        analyzer = SQLAnalyzer(llm_haiku)

        workflow_output = {
            "steps": [],
            "success": True,
            "error": None
        }

        # Step 1: Decomposition
        sub_queries = decomposer._decompose_complex_query(query)
        st.session_state.sub_queries = sub_queries
        
        results = []
        for sub_query in sub_queries:
            step_result = {}
            
            # Get table and entities
            table = decomposer._select_relevant_table(sub_query)
            table_info = decomposer.metadata.get_table_info(table)
            decomposer._initialize_matcher(table_info)
            entities = decomposer._extract_entities(sub_query, table_info)

            # Add to step results
            step_result["sub_query"] = sub_query
            step_result["table"] = table
            step_result["entities"] = entities

            # Step 2: SQL Generation
            query_info = {
                'sub_query': sub_query,
                'table': table,
                'entities': entities
            }
            sql_query = generator.generate_sql(query_info)
            step_result["sql_query"] = sql_query

            # Step 3: SQL Execution
            is_valid, error = executor.validate_query(sql_query)
            if is_valid:
                success, query_results, error = executor.execute_query(sql_query)
                results.append({
                    "sub_query": sub_query,
                    "sql_query": sql_query,
                    "results": query_results,
                    "error": error
                })
                step_result["execution"] = {
                    "success": success,
                    "results": query_results,
                    "error": error
                }
            else:
                results.append({
                    "sub_query": sub_query,
                    "sql_query": sql_query,
                    "results": [],
                    "error": error
                })
                step_result["execution"] = {
                    "success": False,
                    "error": error
                }

            workflow_output["steps"].append(step_result)

        st.session_state.results = results

        # Step 4: Analysis
        analysis = analyzer.analyze_results(
            {'original_query': query},
            [{'sub_query': r['sub_query'], 'sql_query': r['sql_query'], 'results': r['results']} for r in results]
        )
        st.session_state.analysis = analysis
        workflow_output["analysis"] = analysis

        # Add assistant message with workflow results
        st.session_state.messages.append({
            "role": "assistant",
            "content": workflow_output
        })

        # Save chat
        chat_manager.save_chat(
            st.session_state.current_chat_id,
            st.session_state.messages
        )

    except Exception as e:
        error_msg = f"Workflow failed: {str(e)}"
        st.error(error_msg)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ {error_msg}"
        })
        chat_manager.save_chat(
            st.session_state.current_chat_id,
            st.session_state.messages
        )

def render_workflow_results():
    """Render the workflow results in a structured way"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(f"🧑‍💻 **Query:** {message['content']}")
            else:
                if isinstance(message["content"], dict):
                    workflow_output = message["content"]
                    
                    for step in workflow_output.get("steps", []):
                        st.subheader(f"📋 Sub-query: {step['sub_query']}")
                        
                        # Show entities
                        st.write("**Identified Entities:**")
                        for entity in step["entities"]:
                            st.info(
                                f"Found '{entity['search_term']}' in column '{entity['column']}'\n"
                                f"Matched Value: '{entity['matched_value']}' (Score: {entity['score']})"
                            )
                        
                        # Show SQL
                        st.write("**Generated SQL:**")
                        st.code(step["sql_query"], language="sql")
                        
                        # Show execution results
                        if step["execution"]["success"]:
                            st.write("**Results:**")
                            st.dataframe(step["execution"]["results"])
                        else:
                            st.error(f"Execution failed: {step['execution']['error']}")
                    
                    # Show analysis
                    if analysis := workflow_output.get("analysis"):
                        st.header("📊 Analysis Results")
                        st.success(f"Successfully analyzed {analysis['sub_query_count']} sub-queries")
                        
                        if analysis_details := analysis.get("analysis", {}):
                            st.subheader("Summary")
                            st.write(analysis_details.get("summary", "No summary available"))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("Key Insights")
                                st.write(analysis_details.get("insights", "No insights available"))
                                
                                st.subheader("Trends")
                                st.write(analysis_details.get("trends", "No trends available"))
                            
                            with col2:
                                st.subheader("Implications")
                                st.write(analysis_details.get("implications", "No implications available"))
                                
                                st.subheader("Relationships")
                                st.write(analysis_details.get("relationships", "No relationships available"))
                else:
                    st.write(message["content"])

def main():
    st.set_page_config(
        page_title="SQL Analysis Tester",
        page_icon="🧪",
        layout="wide"
    )

    st.title("SQL Analysis Testing Interface")

    # Initialize session state and chat manager
    initialize_session_state()
    chat_manager = ChatManager()

    # Render the sidebar
    api_key = render_sidebar(chat_manager)

    if not api_key:
        st.warning("Please enter the API key to proceed.")
        return

    # Query Input Section
    st.header("Enter Your Query")
    query = st.text_area(
        "Test query:",
        value=st.session_state.query,
        placeholder="e.g., What is the total budget for AC Wailea for November 2023?"
    )

    if st.button("Run Analysis", disabled=not st.session_state.api_key_set):
        st.session_state.query = query
        run_workflow(query, chat_manager)

    # Display Results
    render_workflow_results()

if __name__ == "__main__":
    main()