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
        
    def get_system_prompt(self, stage: str, tech_stack: str = None, language: str = "English", 
                          question_number: int = 0, candidate_name: str = "", is_clarification: bool = False) -> str:
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
            
            IMPORTANT: If you receive blank, incomplete, or unclear responses, politely ask the candidate to clarify or provide the missing information. 
            Don't move to the next question until you have a satisfactory answer.
            
            CRITICAL: You are still in the information gathering stage. Do NOT ask technical questions yet. Only ask for basic profile information.
            """
            
        elif stage == "technical_questions":
            difficulty_levels = ["Easy", "Easy", "Medium", "Hard"]
            current_difficulty = difficulty_levels[question_number - 1] if question_number <= 4 else "Easy"
            
            clarification_note = ""
            if is_clarification:
                clarification_note = """
                
                IMPORTANT: You are asking for clarification/more details on the SAME technical question. 
                This is NOT a new question. Ask the candidate to elaborate or provide more detail on their previous answer.
                Be encouraging and give them another chance to expand their response.
                """
            
            return f"""{base_prompt}
            
            Based on the candidate's tech stack: {tech_stack}
            
            You are on technical question #{question_number} of 4 (Difficulty: {current_difficulty}).
            
            Question Difficulty Guidelines:
            - Easy (Questions 1-2): Basic concepts, syntax, definitions
            - Medium (Question 3): Practical application, problem-solving scenarios
            - Hard (Question 4): Advanced concepts, system design, optimization, best practices
            
            After receiving an answer:
            1. If the answer is blank, too short (less than 5 words), or seems like gibberish, politely ask: 
               "I notice your response seems incomplete. Could you please elaborate on your answer? Take your time."
            2. If the answer is reasonable but brief, ask for clarification: "Could you provide a bit more detail?"
            3. If the answer is good, provide brief encouraging feedback and move to next question.
            4. After receiving a satisfactory answer to question 4, provide a brief thank you and indicate that the technical questions are complete.
            
            Make questions specific to their declared technologies. Stay in context and don't repeat questions.
            {clarification_note}
            """
            
        elif stage == "input_validation":
            return f"""{base_prompt}
            
            The candidate provided an unclear, blank, or very short response. Politely ask them to clarify or provide more information.
            Be encouraging and give them another chance. Mention that it's okay to take their time.
            Don't lose the context of what you were asking about.
            """
            
        elif stage == "conclusion":
            name_part = f" {candidate_name}" if candidate_name else ""
            return f"""{base_prompt}
            
            The candidate has completed all 4 technical questions. Provide a professional conclusion message:
            
            "Thank you{name_part} for completing the interview with TalentScout! 
            
            You have successfully answered all our technical questions. Our hiring team will now evaluate your responses along with your profile information.
            
            If you are shortlisted, a member from our hiring team will contact you within 3-5 business days to discuss the next steps in the recruitment process.
            
            We appreciate the time you've invested in this interview. Good luck with your application!"
            
            Be warm, professional, and encouraging. This concludes the interview.
            """
            
        return base_prompt

    def validate_user_input(self, user_input: str, context: str = "") -> Dict:
        """Validate user input and determine if it needs clarification"""
        input_length = len(user_input.strip())
        word_count = len(user_input.strip().split())
        
        # Check for blank or very short responses
        if input_length == 0:
            return {"valid": False, "reason": "blank", "message": "I didn't receive any input from you. Could you please provide an answer?"}
        
        if input_length < 3:
            return {"valid": False, "reason": "too_short", "message": "Your response seems very brief. Could you please provide more details?"}
            
        # Check for gibberish or repeated characters
        if len(set(user_input.lower())) < 3 and input_length > 5:
            return {"valid": False, "reason": "gibberish", "message": "I'm having trouble understanding your response. Could you please rephrase it?"}
            
        # Check if it's mostly numbers or special characters (for non-technical contexts)
        if "technical_questions" not in context and user_input.replace(" ", "").isdigit():
            return {"valid": False, "reason": "numbers_only", "message": "I received only numbers. Could you please provide a more complete answer?"}
            
        # Check for very short answers in technical questions
        if "technical_questions" in context and word_count < 3:
            return {"valid": False, "reason": "insufficient_detail", "message": "Your technical answer seems quite brief. Could you provide more detail or explanation?"}
            
        return {"valid": True, "reason": "good", "message": ""}

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

    def check_information_completeness(self, candidate_info: Dict) -> Dict:
        """Check if all required information is collected"""
        required_fields = {
            "name": "Full Name",
            "email": "Email Address", 
            "tech_stack": "Tech Stack"
        }
        
        missing_fields = []
        for field, display_name in required_fields.items():
            if not candidate_info.get(field) or str(candidate_info.get(field)).strip().lower() in ['null', 'none', '']:
                missing_fields.append(display_name)
        
        return {
            "complete": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }

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
    if 'current_question_number' not in st.session_state:
        st.session_state.current_question_number = 0
    if 'questions_asked' not in st.session_state:
        st.session_state.questions_asked = 0  # Track actual questions asked
    if 'language' not in st.session_state:
        st.session_state.language = "English"
    if 'conversation_ended' not in st.session_state:
        st.session_state.conversation_ended = False
    if 'awaiting_clarification' not in st.session_state:
        st.session_state.awaiting_clarification = False
    if 'awaiting_tech_clarification' not in st.session_state:
        st.session_state.awaiting_tech_clarification = False
    if 'last_question_context' not in st.session_state:
        st.session_state.last_question_context = ""
    if 'information_gathering_complete' not in st.session_state:
        st.session_state.information_gathering_complete = False

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
            if i < current_stage_idx:
                st.success(f"✅ {stage}")
            elif i == current_stage_idx:
                if stage == "Technical Questions" and st.session_state.questions_asked > 0:
                    st.info(f"🔄 {stage} ({st.session_state.questions_asked}/4)")
                else:
                    st.info(f"🔄 {stage}")
            else:
                st.write(f"⏳ {stage}")
                
        # Show validation status
        if st.session_state.awaiting_clarification:
            st.warning("⚠️ Awaiting information clarification")
        elif st.session_state.awaiting_tech_clarification:
            st.warning("⚠️ Awaiting technical answer clarification")

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
                        "adiós", "au revoir", "auf wiedenhören", "अलविदा", "再见"]
        return any(keyword in user_input.lower() for keyword in exit_keywords)
    
    # Chat input
    if not st.session_state.conversation_ended:
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Check for exit keywords
            if check_exit_keywords(user_input):
                st.session_state.stage = "conclusion"
                st.session_state.conversation_ended = True
            
            # Validate user input
            context = f"{st.session_state.stage}_{st.session_state.current_question_number}"
            validation_result = assistant.validate_user_input(user_input, context)
            
            # Handle invalid input during information gathering
            if not validation_result["valid"] and st.session_state.stage == "information_gathering" and not st.session_state.awaiting_clarification:
                st.session_state.awaiting_clarification = True
                
                # Add user's invalid input
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Add clarification request
                clarification_message = f"{validation_result['message']} I'm here to help, so please take your time to provide a complete response."
                st.session_state.messages.append({"role": "assistant", "content": clarification_message})
                st.rerun()
            
            # Handle invalid input during technical questions
            elif not validation_result["valid"] and st.session_state.stage == "technical_questions" and not st.session_state.awaiting_tech_clarification:
                st.session_state.awaiting_tech_clarification = True
                
                # Add user's invalid input
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Add clarification request using technical questions prompt with clarification flag
                tech_stack = st.session_state.candidate_info.get("tech_stack", "")
                candidate_name = st.session_state.candidate_info.get("name", "")
                system_prompt = assistant.get_system_prompt(
                    "technical_questions", 
                    tech_stack, 
                    selected_language,
                    st.session_state.current_question_number,
                    candidate_name,
                    is_clarification=True
                )
                
                with st.spinner("AI is thinking..."):
                    clarification_response = assistant.chat_with_groq(st.session_state.messages, system_prompt)
                
                st.session_state.messages.append({"role": "assistant", "content": clarification_response})
                st.rerun()
            
            # Handle valid input or retry after clarification
            else:
                # Reset clarification flags
                if st.session_state.awaiting_clarification:
                    st.session_state.awaiting_clarification = False
                if st.session_state.awaiting_tech_clarification:
                    st.session_state.awaiting_tech_clarification = False
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Generate appropriate system prompt
                if st.session_state.stage == "technical_questions":
                    tech_stack = st.session_state.candidate_info.get("tech_stack", "")
                    candidate_name = st.session_state.candidate_info.get("name", "")
                    system_prompt = assistant.get_system_prompt(
                        "technical_questions", 
                        tech_stack, 
                        selected_language,
                        st.session_state.current_question_number,
                        candidate_name,
                        is_clarification=False
                    )
                elif st.session_state.stage == "conclusion":
                    candidate_name = st.session_state.candidate_info.get("name", "")
                    system_prompt = assistant.get_system_prompt(
                        "conclusion", 
                        language=selected_language,
                        candidate_name=candidate_name
                    )
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
                    completeness_check = assistant.check_information_completeness(st.session_state.candidate_info)
                    
                    if completeness_check["complete"] and not st.session_state.information_gathering_complete:
                        st.session_state.stage = "technical_questions"
                        st.session_state.current_question_number = 1
                        st.session_state.questions_asked = 0
                        st.session_state.information_gathering_complete = True
                        
                elif st.session_state.stage == "technical_questions":
                    # Only increment question number for actual new questions, not clarifications
                    if not st.session_state.awaiting_tech_clarification:
                        # Check if AI is asking a new question (not just giving feedback or asking for clarification on same question)
                        is_new_question = False
                        
                        # Look for indicators of a new question
                        new_question_indicators = [
                            "next question", "question 2", "question 3", "question 4",
                            "second question", "third question", "fourth question",
                            "moving on", "let's move to", "now for", "final question"
                        ]
                        
                        # Check if it's asking for a new technical concept/topic
                        question_patterns = [
                            "explain", "describe", "what is", "how does", "can you tell me about",
                            "discuss", "compare", "implement", "design", "optimize"
                        ]
                        
                        ai_response_lower = ai_response.lower()
                        
                        # It's a new question if it mentions moving to next question or contains new question patterns
                        # and doesn't contain clarification keywords
                        clarification_keywords = ["more detail", "elaborate", "expand", "clarify", "can you provide more"]
                        
                        has_new_question_indicator = any(indicator in ai_response_lower for indicator in new_question_indicators)
                        has_question_pattern = any(pattern in ai_response_lower for pattern in question_patterns) and "?" in ai_response
                        has_clarification_keyword = any(keyword in ai_response_lower for keyword in clarification_keywords)
                        
                        # It's a new question if:
                        # 1. It explicitly mentions next question, OR
                        # 2. It has question patterns and no clarification keywords, OR
                        # 3. We haven't asked any questions yet and it contains a question
                        if (has_new_question_indicator or 
                            (has_question_pattern and not has_clarification_keyword) or 
                            (st.session_state.questions_asked == 0 and "?" in ai_response)):
                            is_new_question = True
                        
                        if is_new_question:
                            st.session_state.questions_asked += 1
                            # Update current question number only for display
                            st.session_state.current_question_number = st.session_state.questions_asked
                    
                    # Move to conclusion only after candidate has answered all 4 questions
                    # Check if AI is providing feedback/conclusion after the 4th question
                    if (st.session_state.questions_asked >= 4 and 
                        not st.session_state.awaiting_tech_clarification and
                        ("thank you" in ai_response.lower() or 
                         "completed" in ai_response.lower() or
                         "final question" in ai_response.lower() or
                         "conclude" in ai_response.lower())):
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
                if value and str(value).strip().lower() not in ['null', 'none', '']:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

if __name__ == "__main__":
    main()