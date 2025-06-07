import streamlit as st
import os
from groq import Groq
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

# Configure page
st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Groq client
@st.cache_resource
def init_groq_client():
    api_key =os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("Please set your GROQ_API_KEY in Streamlit secrets or environment variables")
        st.stop()
    return Groq(api_key=api_key)

class HiringAssistant:
    def __init__(self):
        self.client = init_groq_client()
        self.model = "llama3-8b-8192"
        self.languages = {
            "English": "en",
            "Spanish": "es", 
            "French": "fr",
            "German": "de",
            "Hindi": "hi",
            "Chinese": "zh"
        }
        
    def get_system_prompt(self, stage: str, tech_stack: str = None, language: str = "English") -> str:
        """Generate system prompts for different conversation stages"""
        
        base_prompt = f"""You are a professional hiring assistant chatbot for TalentScout, a technology recruitment agency. 
        Respond in {language}. Be professional, friendly, and concise."""
        
        if stage == "greeting":
            return f"""{base_prompt}
            
            Your task is to greet the candidate and explain your purpose. Keep it brief and welcoming.
            Mention that you'll be collecting some basic information and then asking technical questions based on their tech stack.
            """
            
        elif stage == "information_gathering":
            return f"""{base_prompt}
            
            You are collecting candidate information. Ask for ONE piece of information at a time in this order:
            1. Full Name
            2. Email Address  
            3. Phone Number
            4. Years of Experience
            5. Desired Position(s)
            6. Current Location
            7. Tech Stack (programming languages, frameworks, databases, tools)
            
            Be conversational and ask follow-up questions if needed. Once you have all information, confirm it with the candidate.
            """
            
        elif stage == "technical_questions":
            return f"""{base_prompt}
            
            Based on the candidate's tech stack: {tech_stack}
            
            Generate exactly 4 technical questions:
            - 2 Easy questions (basic concepts, syntax)
            - 1 Medium question (practical application, problem-solving)  
            - 1 Hard question (advanced concepts, system design, optimization)
            
            Ask ONE question at a time. After each answer, provide brief feedback and move to the next question.
            Make questions specific to their declared technologies.
            """
            
        elif stage == "conclusion":
            return f"""{base_prompt}
            
            Thank the candidate for their time, summarize the interview process, and inform them about next steps.
            Be encouraging and professional. End the conversation gracefully.
            """
            
        return base_prompt

    def chat_with_groq(self, messages: List[Dict], system_prompt: str) -> str:
        """Send messages to Groq and get response"""
        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}"

    def extract_candidate_info(self, conversation: List[Dict]) -> Dict:
        """Extract candidate information from conversation using LLM"""
        try:
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
            
            extraction_prompt = """Extract the following information from this conversation and return as JSON:
            {
                "name": "full name",
                "email": "email address", 
                "phone": "phone number",
                "experience": "years of experience",
                "position": "desired position",
                "location": "current location",
                "tech_stack": "technologies mentioned"
            }
            
            If any information is missing, use null for that field."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": conversation_text}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
            
        except Exception as e:
            st.error(f"Error extracting information: {e}")
            return {}

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'stage' not in st.session_state:
        st.session_state.stage = "greeting"
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = {}
    if 'question_count' not in st.session_state:
        st.session_state.question_count = 0
    if 'language' not in st.session_state:
        st.session_state.language = "English"
    if 'conversation_ended' not in st.session_state:
        st.session_state.conversation_ended = False

def main():
    st.title("🤖 TalentScout Hiring Assistant")
    st.markdown("*Your AI-powered technical interview companion*")
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize assistant
    assistant = HiringAssistant()
    
    # Sidebar with language selection and info
    with st.sidebar:
        st.header("Settings")
        
        # Language selection
        selected_language = st.selectbox(
            "Select Language:",
            options=list(assistant.languages.keys()),
            index=0
        )
        st.session_state.language = selected_language
        
        # GDPR Compliance Notice
        st.header("Privacy Notice")
        st.markdown("""
        **Data Privacy & GDPR Compliance:**
        - Your data is processed temporarily for interview purposes
        - No personal information is permanently stored
        - You can request data deletion anytime
        - Data is used only for recruitment evaluation
        - Session data is cleared when you close the browser
        """)
        
        if st.button("Clear Session Data"):
            st.session_state.clear()
            st.rerun()
            
        # Current stage indicator
        st.header("Interview Progress")
        stages = ["Greeting", "Information Gathering", "Technical Questions", "Conclusion"]
        current_stage_idx = {
            "greeting": 0,
            "information_gathering": 1, 
            "technical_questions": 2,
            "conclusion": 3
        }.get(st.session_state.stage, 0)
        
        for i, stage in enumerate(stages):
            if i <= current_stage_idx:
                st.success(f"✅ {stage}")
            else:
                st.info(f"⏳ {stage}")

    # Main chat interface
    st.header("Interview Chat")
    
    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Handle conversation ending keywords
    def check_exit_keywords(user_input: str) -> bool:
        exit_keywords = ["goodbye", "bye", "exit", "quit", "end", "stop", "finish", 
                        "adiós", "au revoir", "auf wiederhören", "अलविदा", "再见"]
        return any(keyword in user_input.lower() for keyword in exit_keywords)
    
    # Chat input
    if not st.session_state.conversation_ended:
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Check for exit keywords
            if check_exit_keywords(user_input):
                st.session_state.stage = "conclusion"
                st.session_state.conversation_ended = True
            
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Generate appropriate system prompt
            if st.session_state.stage == "technical_questions":
                tech_stack = st.session_state.candidate_info.get("tech_stack", "")
                system_prompt = assistant.get_system_prompt("technical_questions", tech_stack, selected_language)
            else:
                system_prompt = assistant.get_system_prompt(st.session_state.stage, language=selected_language)
            
            # Get AI response
            with st.spinner("AI is thinking..."):
                ai_response = assistant.chat_with_groq(st.session_state.messages, system_prompt)
            
            # Add AI response
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            # Stage management logic
            if st.session_state.stage == "greeting":
                st.session_state.stage = "information_gathering"
                
            elif st.session_state.stage == "information_gathering":
                # Extract candidate info
                candidate_info = assistant.extract_candidate_info(st.session_state.messages)
                st.session_state.candidate_info.update(candidate_info)
                
                # Check if we have enough information
                required_fields = ["name", "email", "tech_stack"]
                if all(st.session_state.candidate_info.get(field) for field in required_fields):
                    st.session_state.stage = "technical_questions"
                    
            elif st.session_state.stage == "technical_questions":
                st.session_state.question_count += 1
                if st.session_state.question_count >= 8:  # 4 questions + 4 responses
                    st.session_state.stage = "conclusion"
                    st.session_state.conversation_ended = True
                    
            st.rerun()
    
    # Start conversation if no messages
    if not st.session_state.messages:
        system_prompt = assistant.get_system_prompt("greeting", language=selected_language)
        with st.spinner("Initializing interview..."):
            greeting = assistant.chat_with_groq([], system_prompt)
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.rerun()
    
    # Display candidate information summary
    if st.session_state.candidate_info:
        with st.expander("Candidate Information Summary", expanded=False):
            for key, value in st.session_state.candidate_info.items():
                if value:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

if __name__ == "__main__":
    main()