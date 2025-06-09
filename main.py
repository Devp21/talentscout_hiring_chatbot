import streamlit as st
import json
import os
import re
from datetime import datetime
from groq import Groq
from textblob import TextBlob
import time
from dotenv import load_dotenv

# Load dotenv
load_dotenv()

# Configure page
st.set_page_config(
    page_title="TalentScout AI Hiring Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 20px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: right;
    }
    
    .bot-message {
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .form-container {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    
    .sentiment-indicator {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        margin-left: 10px;
    }
    
    .confident { background-color: #d4edda; color: #155724; }
    .neutral { background-color: #fff3cd; color: #856404; }
    .not_confident { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Place this at the top, before translations and t()
supported_languages = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Hindi': 'hi',
    'Chinese': 'zh'
}

translations = {
    'en': {
        'consent_title': "📋 Data Consent & Privacy Notice",
        'welcome': "Welcome to TalentScout's AI Hiring Assistant!",
        'consent_continue': "✅ I Consent & Continue",
        'consent_decline': "❌ I Do Not Consent",
        'form_title': "📝 Candidate Information Form",
        'full_name': "Full Name *",
        'email': "Email Address *",
        'phone': "Phone Number *",
        'experience': "Years of Experience *",
        'position': "Desired Position *",
        'location': "Current Location *",
        'tech_stack': "Tech Stack *",
        'submit': "Submit & Start Interview",
        'answer_placeholder': "Type your answer here...",
        'submit_answer': "Submit Answer",
        'end_interview': "End Interview",
        # ...add all other UI strings
    },
    'es': {
        'consent_title': "📋 Consentimiento de Datos y Aviso de Privacidad",
        'welcome': "¡Bienvenido al Asistente de Contratación de TalentScout!",
        'consent_continue': "✅ Consiento y Continuar",
        'consent_decline': "❌ No Consiento",
        'form_title': "📝 Formulario de Información del Candidato",
        'full_name': "Nombre completo *",
        'email': "Correo electrónico *",
        'phone': "Número de teléfono *",
        'experience': "Años de experiencia *",
        'position': "Puesto deseado *",
        'location': "Ubicación actual *",
        'tech_stack': "Stack tecnológico *",
        'submit': "Enviar y comenzar entrevista",
        'answer_placeholder': "Escribe tu respuesta aquí...",
        'submit_answer': "Enviar respuesta",
        'end_interview': "Terminar entrevista",
        # ...add all other UI strings
    },
    # Add more languages...
}

def t(key):
    lang_code = supported_languages[st.session_state.language]
    return translations.get(lang_code, translations['en']).get(key, key)

class HiringAssistant:
    def __init__(self):
        self.groq_client = None
        self.initialize_groq()
        
    def initialize_groq(self):
        """Initialize Groq client with API key"""
        try:
            # You'll need to set your Groq API key
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("Please set your GROQ_API_KEY in environment variables")
                st.stop()
            self.groq_client = Groq(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Error initializing Groq client: {e}")
            return False
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of user input"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "confident", "💪"
            elif polarity < -0.1:
                return "not_confident", "😟"
            else:
                return "neutral", "😐"
        except:
            return "neutral", "😐"
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        """Validate phone number format"""
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        cleaned_phone = re.sub(r'[^\d\+]', '', phone)
        return len(cleaned_phone) >= 10 and len(cleaned_phone) <= 15
    
    def generate_technical_questions(self, tech_stack, experience_level, language='English'):
        """Generate technical questions based on tech stack and language"""
        try:
            if not self.groq_client:
                if not self.initialize_groq():
                    return self.get_fallback_questions(tech_stack)

            # Improved prompt for more reliable output
            prompt = f"""
You are an expert technical interviewer. Generate exactly 4 technical interview questions for a candidate with the following profile:

Tech Stack: {tech_stack}
Experience Level: {experience_level} years

Respond ONLY in {language}.

CRITICAL INSTRUCTIONS:
- Output ONLY the questions, no introduction or summary.
- Each question must be on a new line, and follow this format:
  DIFFICULTY: [Easy/Medium/Hard]
  QUESTION: [The actual question]
- The first two questions must be Easy, the third Medium, the fourth Hard.
- Make each question specific to the tech stack and experience level.
- Do NOT include any explanations, just the 4 questions in the required format.

Example:
DIFFICULTY: Easy
QUESTION: What is a Python list and how do you use it?
DIFFICULTY: Easy
QUESTION: How do you create a virtual environment in Python?
DIFFICULTY: Medium
QUESTION: How would you use Django ORM to perform a database migration?
DIFFICULTY: Hard
QUESTION: Explain how you would optimize a Django REST API for high concurrency.
"""

            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=800
            )

            # Robust parsing: Only accept if exactly 4 questions are found
            questions = self.parse_questions(response.choices[0].message.content)
            if not questions or len(questions) != 4:
                st.warning("Generated an incorrect number of questions. Using fallback questions.")
                return self.get_fallback_questions(tech_stack)
            # Ensure order: 2 Easy, 1 Medium, 1 Hard
            difficulties = [q['difficulty'].lower() for q in questions]
            if difficulties != ['easy', 'easy', 'medium', 'hard']:
                st.warning("Questions did not match required difficulty order. Using fallback questions.")
                return self.get_fallback_questions(tech_stack)
            return questions
        except Exception as e:
            st.error(f"Error generating questions: {e}")
            return self.get_fallback_questions(tech_stack)
    
    def parse_questions(self, response_text):
        """Parse the generated questions"""
        questions = []
        lines = response_text.strip().split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith('DIFFICULTY:'):
                if current_question:
                    questions.append(current_question)
                current_question = {'difficulty': line.replace('DIFFICULTY:', '').strip()}
            elif line.startswith('QUESTION:'):
                current_question['question'] = line.replace('QUESTION:', '').strip()
        
        if current_question:
            questions.append(current_question)
            
        return questions[:4]  # Ensure we only have 4 questions
    
    def get_fallback_questions(self, tech_stack):
        """Fallback questions if API fails"""
        tech = tech_stack.split(',')[0].strip() if tech_stack else 'programming'
        return [
            {
                "difficulty": "Easy",
                "question": f"Explain the basic concepts and principles of {tech}. What are its main features and use cases?"
            },
            {
                "difficulty": "Easy",
                "question": f"What are the key differences between {tech} and similar technologies? When would you choose {tech} over alternatives?"
            },
            {
                "difficulty": "Medium",
                "question": f"Describe a real-world scenario where you would use {tech}. How would you implement it and what challenges might you face?"
            },
            {
                "difficulty": "Hard",
                "question": f"Explain how you would optimize a {tech} application for performance and scalability. What best practices would you follow?"
            }
        ]
    
    def evaluate_answer(self, question, answer, tech_stack, language='English'):
        """Evaluate candidate's answer using Groq and language"""
        if not self.groq_client or not answer.strip():
            return False, "Please provide a more detailed answer."
            
        try:
            prompt = f"""
            You are a technical interviewer evaluating a candidate's answer to a technical question.
            
            Question: {question}
            Answer: {answer}
            Candidate's Tech Stack: {tech_stack}
            
            Respond in {language}.
            
            Instructions:
            - On the FIRST LINE, write ONLY one of the following: ADEQUATE, NEEDS_CLARIFICATION, or IRRELEVANT.
            - On the SECOND LINE, provide a brief explanation (1-2 sentences) for your evaluation.
            - An answer is ADEQUATE if it is technically correct, complete, and directly answers the question.
            - An answer NEEDS_CLARIFICATION if it is partially correct, vague, incomplete, or requires more detail.
            - An answer is IRRELEVANT if it does not address the question asked at all.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=200
            )
            
            evaluation = response.choices[0].message.content.strip()
            first_line = evaluation.splitlines()[0].strip().upper()
            
            if first_line == "ADEQUATE":
                return True, "Good answer! Moving to the next question."
            elif first_line == "IRRELEVANT":
                return False, "Your answer does not seem to be relevant to the question. Could you please provide a relevant answer?"
            else:
                return False, "Could you please elaborate more on your answer or provide more specific details?"
            
        except Exception as e:
            # Fallback evaluation for API errors or unexpected responses
            st.warning(f"API evaluation failed: {e}. Falling back to basic validation.")
            if len(answer.strip()) < 50 or "not sure" in answer.lower() or "don't know" in answer.lower(): # Increased minimum length and added keyword checks
                return False, "Your answer is too short or indicates uncertainty. Please provide a more detailed and relevant response."
            return True, "Thank you for your answer. We will proceed with this, but please try to be more detailed in future responses."
    
    def save_candidate_data(self, data):
        """Save candidate data locally"""
        try:
            filename = f"candidate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Create data directory if it doesn't exist
            os.makedirs("candidate_data", exist_ok=True)
            
            filepath = os.path.join("candidate_data", filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, filepath
        except Exception as e:
            st.error(f"Error saving data: {e}")
            return False, None

def main():
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'consent'
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'candidate_data' not in st.session_state:
        st.session_state.candidate_data = {}
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    
    assistant = HiringAssistant()
    
    # Multilingual support: Add language selector
    if 'language' not in st.session_state:
        st.session_state.language = 'English'
    st.sidebar.markdown('### 🌐 Language')
    st.session_state.language = st.sidebar.selectbox('Select your language:', list(supported_languages.keys()), index=0)
    selected_language = st.session_state.language
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 TalentScout AI Hiring Assistant</h1>
        <p>Your intelligent recruitment partner for technology placements</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Consent Stage
    if st.session_state.stage == 'consent':
        st.markdown(f"""
        ## {t('consent_title')}
        **{t('welcome')}**
        
        **Before we begin, please note that:**
        - ✅ All your data will be stored locally and securely
        - ✅ We comply with GDPR and data privacy standards
        - ✅ Your information will only be used for recruitment purposes
        - ✅ You can end the interview at any time by typing 'end', 'quit', or 'stop'
        - ✅ We use sentiment analysis to ensure a positive interview experience
        
        *By proceeding, you consent to the collection and processing of your data for recruitment purposes.*
        """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(t('consent_continue'), use_container_width=True, type="primary"):
                st.session_state.stage = 'form'
                st.session_state.chat_history.append({
                    "type": "bot",
                    "message": "Thank you for your consent! Let's start by collecting some basic information about you.",
                    "timestamp": datetime.now()
                })
            st.rerun()
            
            if st.button(t('consent_decline'), use_container_width=True):
                st.error("We respect your decision. Thank you for your time!")
                st.stop()
    
    # Form Stage
    elif st.session_state.stage == 'form':
        st.markdown(f"## {t('form_title')}")
        
        with st.form("candidate_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input(t('full_name'), placeholder=t('full_name'))
                email = st.text_input(t('email'), placeholder=t('email'))
                phone = st.text_input(t('phone'), placeholder=t('phone'))
                experience = st.selectbox(t('experience'), 
                                        options=["0-1", "1-3", "3-5", "5-8", "8-12", "12+"])
            
            with col2:
                position = st.text_input(t('position'), placeholder=t('position'))
                location = st.text_input(t('location'), placeholder=t('location'))
                tech_stack = st.text_area(t('tech_stack'), 
                                         placeholder=t('tech_stack'),
                                         height=100)
            
            submitted = st.form_submit_button(t('submit'), use_container_width=True, type="primary")
            
            if submitted:
                # Validation
                errors = []
                
                if not full_name.strip():
                    errors.append(t('full_name'))
                if not email.strip() or not assistant.validate_email(email):
                    errors.append(t('email'))
                if not phone.strip() or not assistant.validate_phone(phone):
                    errors.append(t('phone'))
                if not position.strip():
                    errors.append(t('position'))
                if not location.strip():
                    errors.append(t('location'))
                if not tech_stack.strip():
                    errors.append(t('tech_stack'))
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Save candidate data
                    st.session_state.candidate_data = {
                        "full_name": full_name.strip(),
                        "email": email.strip(),
                        "phone": phone.strip(),
                        "experience": experience,
                        "position": position.strip(),
                        "location": location.strip(),
                        "tech_stack": tech_stack.strip(),
                        "interview_date": datetime.now().isoformat()
                    }
                    
                    # Generate questions
                    with st.spinner("Generating personalized technical questions..."):
                        exp_years = experience.split('-')[0] if '-' in experience else experience.replace('+', '')
                        st.session_state.questions = assistant.generate_technical_questions(
                            tech_stack, exp_years, language=selected_language
                        )
                    
                    st.session_state.stage = 'interview'
                    st.session_state.chat_history.append({
                        "type": "bot",
                        "message": f"Hello {full_name}! Thank you for providing your information for the {position} position. I've prepared 4 technical questions based on your tech stack: {tech_stack}. Let's begin the technical interview!",
                        "timestamp": datetime.now()
                    })
                    st.success("✅ Information saved! Starting technical interview...")
                    time.sleep(2)
                st.rerun()
            
    # Interview Stage
    elif st.session_state.stage == 'interview':
        # Chat History Display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        sentiment_labels = {
            "confident": "Confident",
            "neutral": "Neutral",
            "not_confident": "Not Confident"
        }
        
        for chat in st.session_state.chat_history:
            if chat["type"] == "user":
                sentiment, emoji = assistant.analyze_sentiment(chat["message"])
                label = sentiment_labels.get(sentiment, sentiment.capitalize())
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {chat["message"]}
                    <span class="sentiment-indicator {sentiment}">{emoji} {label}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="bot-message">
                    <strong>🤖 Assistant:</strong> {chat["message"]}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Ensure questions are generated
        if not st.session_state.questions:
            try:
                with st.spinner("Generating personalized technical questions..."):
                    exp_years = st.session_state.candidate_data.get('experience', '0-1').split('-')[0]
                    tech_stack = st.session_state.candidate_data.get('tech_stack', '')
                    
                    # First try with Groq
                    questions = assistant.generate_technical_questions(tech_stack, exp_years, language=selected_language)
                    
                    if not questions or len(questions) < 4:
                        # If Groq fails, use fallback questions
                        questions = assistant.get_fallback_questions(tech_stack)
                    
                    st.session_state.questions = questions
                    
                    if not st.session_state.questions:
                        st.error("Failed to generate questions. Using default questions.")
                        st.session_state.questions = [
                            {"difficulty": "Easy", "question": "Explain the basic concepts of programming and software development."},
                            {"difficulty": "Easy", "question": "What are the key differences between debugging and testing?"},
                            {"difficulty": "Medium", "question": "How would you optimize performance in a software application?"},
                            {"difficulty": "Hard", "question": "Describe a challenging technical problem you've solved and your approach to solving it."}
                        ]
            except Exception as e:
                st.error(f"Error generating questions: {e}")
                st.session_state.questions = assistant.get_fallback_questions(
                    st.session_state.candidate_data.get('tech_stack', '')
                )
        
        # Current Question Display
        if st.session_state.current_question < len(st.session_state.questions):
            current_q = st.session_state.questions[st.session_state.current_question]
            
            st.markdown(f"""
            <div class="form-container">
                <h3>Question {st.session_state.current_question + 1}/4 
                <span style="color: {'green' if current_q['difficulty'] == 'Easy' else 'orange' if current_q['difficulty'] == 'Medium' else 'red'};">
                [{current_q['difficulty']}]
                </span></h3>
                <p><strong>{current_q['question']}</strong></p>
                <p><em>({st.session_state.candidate_data.get('full_name', 'Candidate')}, this question is tailored for your experience in {st.session_state.candidate_data.get('tech_stack', 'technology')})</em></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Answer Input
            user_input = st.text_area(t('answer_placeholder'), placeholder=t('answer_placeholder'), height=100, key=f"answer_{st.session_state.current_question}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(t('submit_answer'), use_container_width=True, type="primary"):
                    if user_input.strip().lower() in ['end', 'quit', 'stop', 'exit']:
                        st.session_state.stage = 'ended'
                        st.session_state.chat_history.append({
                            "type": "user",
                            "message": user_input,
                            "timestamp": datetime.now()
                        })
                        st.session_state.chat_history.append({
                            "type": "bot",
                            "message": "Thank you for your time! The interview has been ended at your request. Someone from our team will contact you regarding the next steps.",
                            "timestamp": datetime.now()
                        })
                        st.rerun()
                    
                    if user_input.strip():
                        # Add user message to chat
                        st.session_state.chat_history.append({
                            "type": "user",
                            "message": user_input,
                            "timestamp": datetime.now()
                        })
                        
                        # Evaluate answer
                        is_adequate, feedback = assistant.evaluate_answer(
                            current_q['question'], 
                            user_input, 
                            st.session_state.candidate_data['tech_stack'],
                            language=selected_language
                        )
                        
                        if is_adequate:
                            st.session_state.chat_history.append({
                                "type": "bot",
                                "message": feedback,
                                "timestamp": datetime.now()
                            })
                            st.session_state.current_question += 1
                            
                            if st.session_state.current_question >= len(st.session_state.questions):
                                st.session_state.stage = 'completed'
                        else:
                            st.session_state.chat_history.append({
                                "type": "bot",
                                "message": feedback,
                                "timestamp": datetime.now()
                            })
                        
                        st.rerun()
                    else:
                        st.warning("Please provide an answer before submitting.")
            
            with col2:
                if st.button(t('end_interview'), use_container_width=True, type="secondary"):
                    st.session_state.stage = 'ended'
                    st.session_state.chat_history.append({
                        "type": "bot",
                        "message": "Thank you for your time! The interview has been ended. Someone from our team will contact you regarding the next steps.",
                        "timestamp": datetime.now()
                    })
        st.rerun()
    
        # Progress Bar
        if st.session_state.questions:  # Only show progress if questions exist
            progress = st.session_state.current_question / len(st.session_state.questions)
            st.progress(progress)
            st.write(f"Progress: {st.session_state.current_question}/{len(st.session_state.questions)} questions completed")
    
    # Completed Stage
    elif st.session_state.stage == 'completed':
        # Save complete interview data
        interview_data = {
            **st.session_state.candidate_data,
            "questions": st.session_state.questions,
            "chat_history": st.session_state.chat_history,
            "status": "completed",
            "completion_time": datetime.now().isoformat()
        }
        
        saved, filepath = assistant.save_candidate_data(interview_data)
        
        st.markdown("""
        <div class="form-container">
            <h2>🎉 Interview Completed Successfully!</h2>
            <p><strong>Thank you for completing the technical interview!</strong></p>
            
            **Here's what happens next:**

            - ✅ Your responses have been recorded and saved securely
            - ✅ Our technical team will review your answers
            - ✅ Someone from our team will contact you within 3-5 business days
            - ✅ You'll receive an email confirmation shortly

            *We appreciate your time and interest in joining our team!*
        </div>
        """, unsafe_allow_html=True)
        
        if saved:
            st.success(f"✅ Interview data saved successfully!")
        
        if st.button("Start New Interview", use_container_width=True, type="primary"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Ended Stage
    elif st.session_state.stage == 'ended':
        # Save partial interview data
        interview_data = {
            **st.session_state.candidate_data,
            "questions": st.session_state.questions,
            "chat_history": st.session_state.chat_history,
            "status": "ended_early",
            "end_time": datetime.now().isoformat(),
            "questions_completed": st.session_state.current_question
        }
        
        saved, filepath = assistant.save_candidate_data(interview_data)
        
        st.markdown("""
        <div class="form-container">
            <h2>👋 Interview Ended</h2>
            <p><strong>Thank you for your time!</strong></p>
            
            Your responses have been saved and someone from our team will contact you regarding the next steps.

            *We appreciate your interest in our opportunities!*
        </div>
        """)
        
        if saved:
            st.success("✅ Your responses have been saved successfully!")
        
        if st.button("Start New Interview", use_container_width=True, type="primary"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Sidebar with instructions
    with st.sidebar:
        st.markdown("### 📖 Instructions")
        st.markdown("""
        **How to use:**
        1. **Consent**: Agree to data processing
        2. **Form**: Fill in your details
        3. **Interview**: Answer 4 technical questions
        4. **Complete**: Receive next steps
        
        **Commands:**
        - Type 'end', 'quit', or 'stop' to end interview
        - All data is stored locally and securely
        
        **Features:**
        - 💪 Sentiment analysis
        - 🎯 Personalized questions
        - 🔒 Secure data handling
        - 📱 Responsive design
        """)
        
        if st.session_state.stage in ['interview', 'completed', 'ended']:
            st.markdown("### 👤 Candidate Info")
            if st.session_state.candidate_data:
                st.write(f"**Name:** {st.session_state.candidate_data.get('full_name', 'N/A')}")
                st.write(f"**Position:** {st.session_state.candidate_data.get('position', 'N/A')}")
                st.write(f"**Experience:** {st.session_state.candidate_data.get('experience', 'N/A')} years")

if __name__ == "__main__":
    main()
