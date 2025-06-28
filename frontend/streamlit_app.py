import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import time

# Page configuration
st.set_page_config(
    page_title="AI Calendar Booking Assistant",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #007bff;
        color: white;
        margin-left: 20%;
    }
    .chat-message.assistant {
        background-color: #f8f9fa;
        color: #333;
        margin-right: 20%;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    .user .avatar {
        background-color: #0056b3;
    }
    .assistant .avatar {
        background-color: #28a745;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-active { background-color: #28a745; }
    .status-thinking { background-color: #ffc107; }
    .status-error { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "agent_status" not in st.session_state:
    st.session_state.agent_status = "ready"

def send_message_to_agent(message: str, session_id: str) -> Dict[str, Any]:
    """Send message to the booking agent API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message, "session_id": session_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to agent: {str(e)}")
        return {"response": "I'm sorry, I'm having trouble connecting. Please try again.", "state": "error"}

def display_chat_message(message: str, is_user: bool = False):
    """Display a chat message with styling"""
    message_class = "user" if is_user else "assistant"
    avatar_text = "U" if is_user else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div class="avatar">{avatar_text}</div>
        <div class="message-content">{message}</div>
    </div>
    """, unsafe_allow_html=True)

def display_status_indicator(status: str):
    """Display agent status indicator"""
    status_class = {
        "ready": "status-active",
        "thinking": "status-thinking",
        "error": "status-error"
    }.get(status, "status-active")
    
    status_text = {
        "ready": "Ready",
        "thinking": "Thinking...",
        "error": "Error"
    }.get(status, "Unknown")
    
    return f'<span class="{status_class} status-indicator"></span>{status_text}'

# Main app layout
st.title("📅 AI Calendar Booking Assistant")
st.markdown("I'll help you schedule meetings and manage your calendar through natural conversation!")

# Sidebar
with st.sidebar:
    st.header("🛠️ Controls")
    
    # Agent status
    st.markdown("**Agent Status:**")
    st.markdown(display_status_indicator(st.session_state.agent_status), unsafe_allow_html=True)
    
    # Session info
    st.markdown("**Session Info:**")
    st.text(f"Session ID: {st.session_state.session_id}")
    st.text(f"Messages: {len(st.session_state.messages)}")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.rerun()
    
    # API health check
    st.markdown("**API Status:**")
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")
    
    # Quick actions
    st.markdown("**Quick Actions:**")
    if st.button("📅 Schedule for Tomorrow"):
        st.session_state.messages.append({"content": "I want to schedule a meeting for tomorrow afternoon", "is_user": True})
        st.rerun()
    
    if st.button("🕐 Check Availability"):
        st.session_state.messages.append({"content": "What times are available this week?", "is_user": True})
        st.rerun()
    
    if st.button("📞 Quick Call"):
        st.session_state.messages.append({"content": "Schedule a 30-minute call for today", "is_user": True})
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with Assistant")

# Chat container
chat_container = st.container()

# Display chat messages
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-message assistant">
            <div class="avatar">🤖</div>
            <div class="message-content">
                Hi! I'm your AI calendar booking assistant. I can help you:
                <ul>
                    <li>📅 Schedule meetings and appointments</li>
                    <li>🔍 Check your calendar availability</li>
                    <li>⏰ Find suitable time slots</li>
                    <li>📝 Book confirmed appointments</li>
                </ul>
                Just tell me when you'd like to schedule something!
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        display_chat_message(message["content"], message["is_user"])

# Message input
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message...",
            placeholder="e.g., 'Schedule a meeting for tomorrow at 2 PM'",
            label_visibility="collapsed"
        )
    
    with col2:
        submit_button = st.form_submit_button("Send", use_container_width=True)

# Process user input
if submit_button and user_input:
    # Add user message to chat
    st.session_state.messages.append({"content": user_input, "is_user": True})
    
    # Update status
    st.session_state.agent_status = "thinking"
    
    # Send to agent and get response
    with st.spinner("Agent is thinking..."):
        agent_response = send_message_to_agent(user_input, st.session_state.session_id)
    
    # Add agent response to chat
    st.session_state.messages.append({"content": agent_response["response"], "is_user": False})
    
    # Update status
    st.session_state.agent_status = "ready" if agent_response.get("state") != "error" else "error"
    
    # Rerun to display new messages
    st.rerun()

# Example conversations
with st.expander("💡 Example Conversations"):
    st.markdown("""
    **Here are some ways you can interact with me:**
    
    **Basic Scheduling:**
    - "Schedule a meeting for tomorrow at 2 PM"
    - "Book a 30-minute call for next Friday"
    - "I need to meet with someone this Thursday afternoon"
    
    **Availability Checking:**
    - "What times are available this week?"
    - "Do you have any free time tomorrow?"
    - "Show me open slots between 10 AM and 3 PM"
    
    **Flexible Requests:**
    - "Find a good time for a team meeting next week"
    - "When can I schedule a 2-hour workshop?"
    - "Book something for early morning tomorrow"
    
    **Specific Details:**
    - "Schedule a client call for December 15th at 3:30 PM"
    - "Book a 45-minute interview for Monday morning"
    - "I need a meeting room for next Tuesday at 1 PM"
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, FastAPI, and LangGraph")