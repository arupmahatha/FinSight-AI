import streamlit as st
import os
import sys
from datetime import datetime
import uuid
from typing import List, Dict

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.decomposer import QueryDecomposer
from engine.generator import SQLGenerator
from engine.executor import SQLExecutor
from engine.analyzer import SQLAnalyzer
from testing import get_test_llm, get_test_db_connection
from ui.manager import ChatManager

def initialize_session_state():
    """Initialize or reset the session state"""
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'initialized': True,
            'chat_manager': ChatManager(),
            'messages': [],
            'current_chat_id': str(uuid.uuid4()),
            'api_key_set': False,
            'viewing_chat': False,
            'saved_chats': {}  # Added to store loaded chats
        })

def save_chat(chat_id: str, messages: List[Dict]):
    """Save the current chat"""
    try:
        st.session_state.chat_manager.save_chat(chat_id, messages)
        st.success("💾 Chat saved successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to save chat: {str(e)}")
        return False

def load_chats():
    """Load all saved chats"""
    try:
        chats = st.session_state.chat_manager.load_chats()
        st.session_state.saved_chats = chats
        return True
    except Exception as e:
        st.error(f"Failed to load chats: {str(e)}")
        return False

def render_sidebar():
    """Render the sidebar with configuration and chat management"""
    with st.sidebar:
        st.title("⚙️ Configuration")
        api_key = st.text_input("API Key:", type="password")
        
        if api_key:
            st.session_state.api_key_set = True
        
        st.markdown("---")
        
        # New Chat Button
        if st.button("🆕 Start New Analysis", type="primary", 
                     key="new_chat_button", 
                     disabled=not st.session_state.api_key_set):
            st.session_state.viewing_chat = False
            st.session_state.messages = []
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.rerun()
        
        st.markdown("---")
        render_chat_history()
    
    return api_key

def render_chat_history():
    """Render the chat history sidebar"""
    st.title("💬 Chat History")
    
    # Load Chats Button
    if st.button("📂 Load Saved Chats", type="primary", key="load_chats_button"):
        load_chats()
    
    # Display saved chats
    if 'saved_chats' in st.session_state and st.session_state.saved_chats:
        for chat_id, chat_data in st.session_state.saved_chats.items():
            with st.expander(f"📝 {chat_data['title']}", expanded=False):
                st.write(f"Created: {datetime.fromisoformat(chat_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📖 View", key=f"load_{chat_id}"):
                        st.session_state.selected_chat = chat_data
                        st.session_state.viewing_chat = True
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{chat_id}", type="secondary"):
                        if st.session_state.chat_manager.delete_chat(chat_id):
                            # Remove from session state
                            st.session_state.saved_chats.pop(chat_id, None)
                            
                            # Clear selected chat if it was the one deleted
                            if ('selected_chat' in st.session_state and 
                                st.session_state.selected_chat.get('chat_id') == chat_id):
                                del st.session_state.selected_chat
                                st.session_state.viewing_chat = False
                            
                            st.success("🗑️ Chat deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete chat")
    else:
        st.info("No saved chats found. Start a new analysis to create one!")

def render_analysis_steps(analysis_data):
    """Render the analysis steps with custom styling"""
    query = analysis_data['query']
    decomposer = analysis_data['decomposer']
    generator = analysis_data['generator']
    executor = analysis_data['executor']
    analyzer = analysis_data['analyzer']
    
    # Step 1: Query Understanding and Decomposition
    with st.expander("📊 1. Query Understanding and Decomposition", expanded=True):
        sub_queries = decomposer._decompose_complex_query(query)
        st.write("Decomposed Queries:")
        
        for i, sub_query in enumerate(sub_queries, 1):
            st.write(f"\nSub-query {i}: {sub_query}")
            
            table = decomposer._select_relevant_table(sub_query)
            st.write(f"Table: {table}")
            
            table_info = decomposer.metadata.get_table_info(table)
            decomposer._initialize_matcher(table_info)
            entities = decomposer._extract_entities(sub_query, table_info)
            
            st.write("\nExtracted Entities:")
            for entity in entities:
                st.write(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
                st.write(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")

    # Step 2: SQL Generation
    with st.expander("💡 2. SQL Generation", expanded=True):
        query_info = {
            'sub_query': sub_query,
            'table': table,
            'extracted_entities': entities
        }
        
        st.write(f"\nGenerating SQL for: {sub_query}")
        st.write(f"Using table: {table}")
        st.write("Available columns:")
        for col, info in table_info.columns.items():
            st.write(f"- {col}: {info.description}")
        
        sql_query = generator.generate_sql(query_info)
        st.code(sql_query, language="sql")

    # Step 3: Query Execution
    with st.expander("⚡ 3. Query Execution", expanded=True):
        is_valid, error = executor.validate_query(sql_query)
        if is_valid:
            st.success("SQL validation passed")
            success, results, error = executor.execute_query(sql_query)
            if success:
                st.write(f"Execution successful: {len(results)} rows returned")
                if results:
                    st.write("\nResults Preview:")
                    st.dataframe(results)
            else:
                st.error(f"Execution failed: {error}")
        else:
            st.error(f"SQL validation failed: {error}")

    # Step 4: Final Analysis
    with st.expander("📈 4. Results Analysis", expanded=True):
        analysis = analyzer.analyze_results(
            {'original_query': query},
            [{'sub_query': q, 'sql_query': sql_query, 'results': results} 
             for q in sub_queries]
        )
        
        if analysis['success']:
            st.write("\nAnalysis Results:")
            st.write(f"Success: {analysis['success']}")
            st.write(f"Sub-query count: {analysis['sub_query_count']}")
            st.write(f"Total result count: {analysis['total_result_count']}")
            
            st.markdown("#### Key Findings:")
            st.write(f"📊 Summary: {analysis['analysis'].get('summary', 'N/A')}")
            st.write(f"💡 Insights: {analysis['analysis'].get('insights', 'N/A')}")
            st.write(f"📈 Trends: {analysis['analysis'].get('trends', 'N/A')}")
            st.write(f"🎯 Implications: {analysis['analysis'].get('implications', 'N/A')}")
            st.write(f"🔗 Relationships: {analysis['analysis'].get('relationships', 'N/A')}")
        else:
            st.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
    
    return analysis

def load_chat_content(chat_data):
    """Load and display a saved chat's content"""
    st.markdown(f"### 📝 Viewing: {chat_data['title']}")
    st.markdown("---")
    
    # Display messages
    for msg in chat_data['messages']:
        with st.chat_message(msg['role']):
            if msg['role'] == 'user':
                st.markdown("🧑‍💻 **User Query:**")
                st.info(msg['content'])
            else:
                try:
                    # Parse the analysis content
                    analysis = eval(msg['content'])
                    if isinstance(analysis, dict):
                        # Step 1: Query Understanding and Decomposition
                        with st.expander("📊 1. Query Understanding and Decomposition", expanded=True):
                            for sub_query_data in analysis.get('sub_queries', []):
                                st.write(f"\nSub-query: {sub_query_data['sub_query']}")
                                st.write(f"Table: {sub_query_data['table']}")
                                
                                st.write("\nExtracted Entities:")
                                for entity in sub_query_data.get('entities', []):
                                    st.write(f"- Found '{entity['search_term']}' in column '{entity['column']}'")
                                    st.write(f"  Matched Value: '{entity['matched_value']}' (Score: {entity['score']})")

                        # Step 2: SQL Generation
                        with st.expander("💡 2. SQL Generation", expanded=True):
                            for sub_query_data in analysis.get('sub_queries', []):
                                st.write(f"\nGenerating SQL for: {sub_query_data['sub_query']}")
                                st.write(f"Using table: {sub_query_data['table']}")
                                if 'sql_query' in sub_query_data:
                                    st.code(sub_query_data['sql_query'], language="sql")

                        # Step 3: Query Execution
                        with st.expander("⚡ 3. Query Execution", expanded=True):
                            for sub_query_data in analysis.get('sub_queries', []):
                                if 'execution_results' in sub_query_data:
                                    results = sub_query_data['execution_results']
                                    if results.get('success'):
                                        st.success("SQL validation passed")
                                        st.write(f"Execution successful: {len(results.get('data', []))} rows returned")
                                        if results.get('data'):
                                            st.write("\nResults Preview:")
                                            st.dataframe(results['data'])
                                    else:
                                        st.error(f"Execution failed: {results.get('error')}")

                        # Step 4: Final Analysis
                        with st.expander("📈 4. Results Analysis", expanded=True):
                            if analysis.get('success'):
                                st.write("\nAnalysis Results:")
                                st.write(f"Success: {analysis['success']}")
                                st.write(f"Sub-query count: {analysis['sub_query_count']}")
                                st.write(f"Total result count: {analysis['total_result_count']}")
                                
                                st.markdown("#### Key Findings:")
                                st.write(f"📊 Summary: {analysis['analysis'].get('summary', 'N/A')}")
                                st.write(f"💡 Insights: {analysis['analysis'].get('insights', 'N/A')}")
                                st.write(f"📈 Trends: {analysis['analysis'].get('trends', 'N/A')}")
                                st.write(f"🎯 Implications: {analysis['analysis'].get('implications', 'N/A')}")
                                st.write(f"🔗 Relationships: {analysis['analysis'].get('relationships', 'N/A')}")
                            else:
                                st.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
                except Exception as e:
                    # If parsing fails, display as regular message
                    st.write(msg['content'])
                    st.error(f"Error parsing analysis: {str(e)}")
    
    # Add a button to return to query input
    if st.button("← Back to Query Input", type="secondary"):
        st.session_state.viewing_chat = False
        st.rerun()

def main():
    st.set_page_config(
        page_title="SQL Query Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Render sidebar and get API key
    api_key = render_sidebar()
    
    if not api_key:
        st.warning("⚠️ Please enter your API key in the sidebar to proceed.")
        return

    st.title("🔍 SQL Query Assistant")
    st.markdown("#### Interactive SQL Query Testing & Analysis Tool")
    st.markdown("---")

    if st.session_state.viewing_chat and 'selected_chat' in st.session_state:
        load_chat_content(st.session_state.selected_chat)
    else:
        query = st.chat_input("Ask a question about your data",
            disabled=not st.session_state.api_key_set)

        if query:
            with st.spinner('Processing your query...'):
                try:
                    # Initialize components
                    llm_haiku = get_test_llm("haiku", api_key=api_key)
                    llm_sonnet = get_test_llm("sonnet", api_key=api_key)
                    connection = get_test_db_connection()
                    
                    decomposer = QueryDecomposer(llm_haiku)
                    generator = SQLGenerator(llm_sonnet)
                    executor = SQLExecutor(connection)
                    analyzer = SQLAnalyzer(llm_haiku)

                    # Process query and collect all steps
                    # Step 1: Decomposition
                    sub_queries = decomposer._decompose_complex_query(query)
                    all_sub_query_data = []
                    
                    for sub_query in sub_queries:
                        sub_query_data = {}
                        sub_query_data['sub_query'] = sub_query
                        
                        # Get table and entities
                        table = decomposer._select_relevant_table(sub_query)
                        sub_query_data['table'] = table
                        
                        table_info = decomposer.metadata.get_table_info(table)
                        decomposer._initialize_matcher(table_info)
                        entities = decomposer._extract_entities(sub_query, table_info)
                        sub_query_data['entities'] = entities
                        
                        # SQL Generation
                        query_info = {
                            'sub_query': sub_query,
                            'table': table,
                            'extracted_entities': entities
                        }
                        sql_query = generator.generate_sql(query_info)
                        sub_query_data['sql_query'] = sql_query
                        
                        # Query Execution
                        is_valid, error = executor.validate_query(sql_query)
                        execution_results = {
                            'success': is_valid,
                            'error': error if not is_valid else None,
                            'data': None
                        }
                        
                        if is_valid:
                            success, results, error = executor.execute_query(sql_query)
                            execution_results['success'] = success
                            execution_results['error'] = error if not success else None
                            execution_results['data'] = results if success else None
                        
                        sub_query_data['execution_results'] = execution_results
                        all_sub_query_data.append(sub_query_data)

                    # Final Analysis
                    analysis = analyzer.analyze_results(
                        {'original_query': query},
                        [{'sub_query': data['sub_query'], 
                          'sql_query': data['sql_query'], 
                          'results': data['execution_results'].get('data')} 
                         for data in all_sub_query_data]
                    )

                    # Combine all data
                    complete_analysis = {
                        'sub_queries': all_sub_query_data,
                        'success': analysis['success'],
                        'sub_query_count': analysis['sub_query_count'],
                        'total_result_count': analysis['total_result_count'],
                        'analysis': analysis['analysis']
                    }

                    # Display results
                    with st.chat_message("user"):
                        st.markdown("🧑‍💻 **User Query:**")
                        st.info(query)

                    with st.chat_message("assistant"):
                        render_analysis_steps({
                            'query': query,
                            'decomposer': decomposer,
                            'generator': generator,
                            'executor': executor,
                            'analyzer': analyzer
                        })

                    # Save chat with complete analysis
                    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    messages = [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": str(complete_analysis)}
                    ]
                    save_chat(chat_id, messages)
                    load_chats()

                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    main()
