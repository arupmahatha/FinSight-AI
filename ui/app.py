import streamlit as st
import uuid
from datetime import datetime
from ..config import Config
from ..database.analyst import DatabaseAnalyst
from ..chat.manager import ChatManager

def initialize_session_state():
    """Initialize or reset the session state"""
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'initialized': True,
            'messages': [],
            'current_context': None,
            'current_chat_id': str(uuid.uuid4()),
            'chats': {},
            'last_query': None,
            'new_chat_clicked': False,
            'api_key_set': False
        })

def render_sidebar(chat_manager: ChatManager):
    """Render the sidebar with configuration and chat management"""
    with st.sidebar:
        st.title("Configuration Settings")
        api_key = st.text_input("Anthropic API Key:", type="password")
        
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
    """Handle the creation of a new chat"""
    if not st.session_state.new_chat_clicked:
        st.session_state.new_chat_clicked = True
        
        if st.session_state.messages:
            chat_manager.save_chat(
                st.session_state.current_chat_id,
                st.session_state.messages
            )
        
        new_chat_id = str(uuid.uuid4())
        st.session_state.update({
            'current_chat_id': new_chat_id,
            'messages': [],
            'current_context': None,
            'last_query': None
        })
        
        welcome_message = {
            "role": "assistant",
            "content": """👋 Hello! I'm your SQL Database Analysis Assistant. 

I can help you analyze your database by:
- Running SQL queries
- Providing data insights
- Answering follow-up questions about the results

Please ask me any question about your database!"""
        }
        st.session_state.messages.append(welcome_message)
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
                if st.button("🗑️ Delete", key=f"delete_{chat_id}", type="secondary"):
                    handle_delete_chat(chat_manager, chat_id)

def handle_load_chat(chat_manager: ChatManager, chat_id: str, chat_data: dict):
    """Handle loading a chat"""
    if st.session_state.messages:
        chat_manager.save_chat(
            st.session_state.current_chat_id,
            st.session_state.messages
        )
    st.session_state.messages = chat_data['messages']
    st.session_state.current_chat_id = chat_id
    st.rerun()

def handle_delete_chat(chat_manager: ChatManager, chat_id: str):
    """Handle deleting a chat"""
    chat_manager.delete_chat(chat_id)
    if chat_id == st.session_state.current_chat_id:
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
    st.session_state.chats = chat_manager.load_chats()
    st.rerun()

def render_messages(analyst: DatabaseAnalyst):
    """Render chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                if isinstance(message.get("content"), dict):
                    formatted_output = analyst.format_output(message["content"])
                    st.markdown(formatted_output)
                else:
                    st.markdown(message["content"])

def main():
    st.set_page_config(
        page_title="SQL Database Analyst",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("SQL Database Analysis Assistant")
    
    initialize_session_state()
    chat_manager = ChatManager()
    
    # Render sidebar and get API key
    api_key = render_sidebar(chat_manager)
    
    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to proceed.")
        return
    
    try:
        config = Config(api_key=api_key)
        analyst = DatabaseAnalyst(config)
    except Exception as e:
        st.error(f"Failed to initialize database analyst: {str(e)}")
        return
    
    # Render existing messages
    render_messages(analyst)
    
    # Query input
    if query := st.chat_input("Ask a question about your data"):
        process_query(query, analyst, chat_manager)

def process_query(query: str, analyst: DatabaseAnalyst, chat_manager: ChatManager):
    """Process a user query and update the chat"""
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.spinner("Analyzing..."):
        try:
            results = analyst.process_query(query)
            formatted_output = analyst.format_output(results)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": formatted_output
            })
            
            chat_manager.save_chat(
                st.session_state.current_chat_id,
                st.session_state.messages
            )
            
            with st.chat_message("assistant"):
                st.markdown(formatted_output)
                
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ {error_msg}"
            })

if __name__ == "__main__":
    main() 