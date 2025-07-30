import streamlit as st
import asyncio
import threading
import time
import queue
import json
import numpy as np
from typing import Optional, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
from streamlit_javascript import st_javascript
import base64

# Import Yuvan components
from yuvan.task_handler import TaskHandler
from yuvan.voice_system import speak_text as speak, cleanup_voice
from yuvan.silero_tts import speak_text_async, cleanup_silero_tts

# Import voice animation components
from voice_animation import VoiceAnimator, create_voice_status_indicator, get_voice_animation_css

class YuvanUI:
    def __init__(self):
        self.task_handler = TaskHandler()
        self.is_speaking = False
        self.is_thinking = False
        self.voice_animator = VoiceAnimator()
        self.speaking_queue = queue.Queue()
        self.current_status = "idle"  # idle, thinking, speaking
        
    def set_status(self, status: str):
        """Update the current status"""
        self.current_status = status
        if status == "speaking":
            self.is_speaking = True
        else:
            self.is_speaking = False
            
        if status == "thinking":
            self.is_thinking = True
        else:
            self.is_thinking = False

    def get_current_animation(self):
        """Get the current animation based on status"""
        if self.current_status == "speaking":
            return self.voice_animator.create_speaking_animation()
        elif self.current_status == "thinking":
            return self.voice_animator.create_thinking_animation()
        else:
            return self.voice_animator.create_idle_animation()

    def speak_with_animation(self, text: str):
        """Speak text and update animation state"""
        self.set_status("speaking")
        try:
            speak(text)
        finally:
            self.set_status("idle")

def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm Yuvan, your AI assistant. How can I help you today?"}
        ]
    if 'is_speaking' not in st.session_state:
        st.session_state.is_speaking = False
    if 'yuvan_ui' not in st.session_state:
        st.session_state.yuvan_ui = YuvanUI()

def apply_custom_css():
    """Apply custom CSS for ChatGPT-like styling"""
    # Include voice animation CSS
    voice_css = get_voice_animation_css()
    
    st.markdown(voice_css, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Message styling */
    .user-message {
        background: #f7f7f8;
        padding: 15px 20px;
        border-radius: 18px;
        margin: 10px 0;
        margin-left: 50px;
        border: 1px solid #e5e5e7;
        position: relative;
    }
    
    .user-message::before {
        content: "👤";
        position: absolute;
        left: -40px;
        top: 15px;
        font-size: 24px;
    }
    
    .assistant-message {
        background: #ffffff;
        padding: 15px 20px;
        border-radius: 18px;
        margin: 10px 0;
        margin-right: 50px;
        border: 1px solid #e5e5e7;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        position: relative;
    }
    
    .assistant-message::before {
        content: "🤖";
        position: absolute;
        right: -40px;
        top: 15px;
        font-size: 24px;
    }
    
    /* Voice animation container */
    .voice-animation {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
        padding: 20px;
        background: rgba(16, 163, 127, 0.05);
        border-radius: 20px;
        border: 2px solid rgba(16, 163, 127, 0.1);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e5e5e7;
        padding: 12px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #10A37F;
        box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
        outline: none;
    }
    
    /* Button styling */
    .stButton > button {
        background: #10A37F;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(16, 163, 127, 0.2);
    }
    
    .stButton > button:hover {
        background: #0d8f6f;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(16, 163, 127, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(16, 163, 127, 0.2);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        margin-bottom: 30px;
        padding: 30px;
        background: linear-gradient(135deg, #10A37F, #1a7a63);
        color: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(16, 163, 127, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        pointer-events: none;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Chat history styling */
    .chat-history {
        max-height: 60vh;
        overflow-y: auto;
        padding: 20px 0;
        border-radius: 10px;
    }
    
    .chat-history::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-history::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.1);
        border-radius: 4px;
    }
    
    .chat-history::-webkit-scrollbar-thumb {
        background: rgba(16, 163, 127, 0.3);
        border-radius: 4px;
    }
    
    .chat-history::-webkit-scrollbar-thumb:hover {
        background: rgba(16, 163, 127, 0.5);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Animation for new messages */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-message, .assistant-message {
        animation: slideIn 0.3s ease-out;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .chat-container {
            padding: 10px;
        }
        
        .user-message, .assistant-message {
            margin-left: 0;
            margin-right: 0;
        }
        
        .user-message::before, .assistant-message::before {
            display: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def display_message(role: str, content: str):
    """Display a message with appropriate styling"""
    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>🤖 Yuvan:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="Yuvan AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    init_session_state()
    
    # Apply custom styling
    apply_custom_css()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Yuvan AI Assistant</h1>
        <p>Your intelligent voice-enabled assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Voice animation area
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Create voice animation container
            st.markdown('<div class="voice-animation">', unsafe_allow_html=True)
            
            # Status indicator
            status_html = create_voice_status_indicator(st.session_state.yuvan_ui.current_status)
            st.markdown(status_html, unsafe_allow_html=True)
            
            # Animation visualization
            animation_placeholder = st.empty()
            fig = st.session_state.yuvan_ui.get_current_animation()
            animation_placeholder.plotly_chart(fig, use_container_width=True, key=f"voice_animation_{st.session_state.yuvan_ui.current_status}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat history
        st.markdown("### Chat History")
        chat_container = st.container()
        
        with chat_container:
            st.markdown('<div class="chat-history">', unsafe_allow_html=True)
            for message in st.session_state.messages:
                display_message(message["role"], message["content"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message...",
                key="user_input",
                placeholder="Ask Yuvan anything...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send 📤", key="send_button", use_container_width=True)
        
        # Voice input button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            voice_button = st.button("🎤 Voice Input", key="voice_button", use_container_width=True)
        
        # Process input
        if send_button and user_input:
            process_user_input(user_input)
        
        if voice_button:
            st.info("🎤 Voice input feature coming soon! For now, please type your message.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar with controls
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I'm Yuvan, your AI assistant. How can I help you today?"}
            ]
            st.rerun()
        
        st.markdown("### ℹ️ About Yuvan")
        st.markdown("""
        Yuvan is an intelligent AI assistant that can:
        - Answer questions and provide information
        - Help with tasks and calculations
        - Provide weather updates
        - Assist with various queries
        - Respond with voice synthesis
        """)
        
        st.markdown("### 🔧 Settings")
        st.checkbox("Enable voice output", value=True, key="voice_enabled")
        st.selectbox("Voice speed", ["Slow", "Normal", "Fast"], index=1, key="voice_speed")

def process_user_input(user_input: str):
    """Process user input and generate response"""
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Set thinking status
    st.session_state.yuvan_ui.set_status("thinking")
    
    # Show thinking indicator
    with st.spinner("🤔 Yuvan is thinking..."):
        # Get response from Yuvan's task handler
        response = st.session_state.yuvan_ui.task_handler.process_command(user_input)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # If voice is enabled, speak the response
    if st.session_state.get("voice_enabled", True):
        # Start speaking in a separate thread
        def speak_response():
            try:
                st.session_state.yuvan_ui.speak_with_animation(response)
            except Exception as e:
                print(f"Voice synthesis error: {e}")
                st.session_state.yuvan_ui.set_status("idle")
        
        threading.Thread(target=speak_response, daemon=True).start()
    else:
        st.session_state.yuvan_ui.set_status("idle")
    
    # Clear input and rerun
    st.session_state.user_input = ""
    st.rerun()

if __name__ == "__main__":
    main()