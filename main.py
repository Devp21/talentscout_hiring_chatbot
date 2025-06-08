import streamlit as st
import json
import os
import re
from datetime import datetime
from groq import Groq
from textblob import TextBlob
import time

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
    
    .positive { background-color: #d4edda; color: #155724; }
    .neutral { background-color: #fff3cd; color: #856404; }
    .negative { background-color: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

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
                return "positive", "😊"
            elif polarity < -0.1:
                return "negative", "😟"
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
    
    def generate_technical_questions(self, tech_stack, experience_level):
        """Generate technical questions based on tech stack"""
        try:
            if not self.groq_client:
                if not self.initialize_groq():
                    return self.get_fallback_questions(tech_stack)
            
            prompt = f"""
            You are an experienced technical interviewer. Generate exactly 4 technical questions for a candidate with the following profile:
            
            Tech Stack: {tech_stack}
            Experience Level: {experience_level} years
            
            Requirements:
            - 2 Easy questions (fundamental concepts)
            - 1 Medium question (practical application)
            - 1 Hard question (advanced concepts or problem-solving)
            
            Format each question as:
            DIFFICULTY: [Easy/Medium/Hard]
            QUESTION: [The actual question]
            
            Make questions specific to their tech stack and appropriate for their experience level.
            Focus on practical knowledge and real-world scenarios.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=1000
            )
            
            questions = self.parse_questions(response.choices[0].message.content)
            if not questions or len(questions) < 4:
                st.warning("Generated fewer questions than expected. Using fallback questions.")
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
    
    def evaluate_answer(self, question, answer, tech_stack):
        """Evaluate candidate's answer using Groq"""
        if not self.groq_client or not answer.strip():
            return False, "Please provide a more detailed answer."
            
        try:
            prompt = f"""
            You are a technical interviewer evaluating a candidate's answer.
            
            Question: {question}
            Answer: {answer}
            Candidate's Tech Stack: {tech_stack}
            
            Evaluate if this answer demonstrates:
            1. Basic understanding of the concept
            2. Relevant technical knowledge
            3. Clear communication
            
            Respond with either:
            - "ADEQUATE" if the answer shows reasonable understanding
            - "NEEDS_CLARIFICATION" if the answer is vague, incomplete, or shows lack of understanding
            
            Then provide a brief explanation in 1-2 sentences.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=200
            )
            
            evaluation = response.choices[0].message.content.strip()
            
            if "ADEQUATE" in evaluation.upper():
                return True, "Good answer! Moving to the next question."
            else:
                return False, "Could you please elaborate more on your answer or provide more specific details?"
                
        except Exception as e:
            # Fallback evaluation
            if len(answer.strip()) < 20:
                return False, "Please provide a more detailed answer."
            return True, "Thank you for your answer."
    
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
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 TalentScout AI Hiring Assistant</h1>
        <p>Your intelligent recruitment partner for technology placements</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Consent Stage
    if st.session_state.stage == 'consent':
        st.markdown("""
        <div class="form-container">
            <h2>📋 Data Consent & Privacy Notice</h2>
            <p><strong>Welcome to TalentScout's AI Hiring Assistant!</strong></p>
            
            <p>Before we begin, please note that:</p>
            <ul>
                <li>✅ All your data will be stored locally and securely</li>
                <li>✅ We comply with GDPR and data privacy standards</li>
                <li>✅ Your information will only be used for recruitment purposes</li>
                <li>✅ You can end the interview at any time by typing 'end', 'quit', or 'stop'</li>
                <li>✅ We use sentiment analysis to ensure a positive interview experience</li>
            </ul>
            
            <p><em>By proceeding, you consent to the collection and processing of your data for recruitment purposes.</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ I Consent & Continue", use_container_width=True, type="primary"):
                st.session_state.stage = 'form'
                st.session_state.chat_history.append({
                    "type": "bot",
                    "message": "Thank you for your consent! Let's start by collecting some basic information about you.",
                    "timestamp": datetime.now()
                })
                st.rerun()
            
            if st.button("❌ I Do Not Consent", use_container_width=True):
                st.error("We respect your decision. Thank you for your time!")
                st.stop()
    
    # Form Stage
    elif st.session_state.stage == 'form':
        st.markdown("""
        <div class="form-container">
            <h2>📝 Candidate Information Form</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("candidate_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name *", placeholder="Enter your full name")
                email = st.text_input("Email Address *", placeholder="your.email@example.com")
                phone = st.text_input("Phone Number *", placeholder="+1234567890")
                experience = st.selectbox("Years of Experience *", 
                                        options=["0-1", "1-3", "3-5", "5-8", "8-12", "12+"])
            
            with col2:
                position = st.text_input("Desired Position *", placeholder="e.g., Software Engineer, Data Scientist")
                location = st.text_input("Current Location *", placeholder="City, Country")
                tech_stack = st.text_area("Tech Stack *", 
                                         placeholder="List your technical skills (e.g., Python, React, AWS, PostgreSQL)",
                                         height=100)
            
            submitted = st.form_submit_button("Submit & Start Interview", use_container_width=True, type="primary")
            
            if submitted:
                # Validation
                errors = []
                
                if not full_name.strip():
                    errors.append("Full name is required")
                if not email.strip() or not assistant.validate_email(email):
                    errors.append("Valid email address is required")
                if not phone.strip() or not assistant.validate_phone(phone):
                    errors.append("Valid phone number is required")
                if not position.strip():
                    errors.append("Desired position is required")
                if not location.strip():
                    errors.append("Current location is required")
                if not tech_stack.strip():
                    errors.append("Tech stack is required")
                
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
                            tech_stack, exp_years
                        )
                    
                    st.session_state.stage = 'interview'
                    st.session_state.chat_history.append({
                        "type": "bot",
                        "message": f"Hello {full_name}! Thank you for providing your information. I've prepared 4 technical questions based on your tech stack: {tech_stack}. Let's begin the technical interview!",
                        "timestamp": datetime.now()
                    })
                    st.success("✅ Information saved! Starting technical interview...")
                    time.sleep(2)
                    st.rerun()
    
    # Interview Stage
    elif st.session_state.stage == 'interview':
        # Chat History Display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for chat in st.session_state.chat_history:
            if chat["type"] == "user":
                sentiment, emoji = assistant.analyze_sentiment(chat["message"])
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {chat["message"]}
                    <span class="sentiment-indicator {sentiment}">{emoji} {sentiment}</span>
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
                    questions = assistant.generate_technical_questions(tech_stack, exp_years)
                    
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
            </div>
            """, unsafe_allow_html=True)
            
            # Answer Input
            user_input = st.text_area("Your Answer:", placeholder="Type your answer here...", height=100, key=f"answer_{st.session_state.current_question}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("Submit Answer", use_container_width=True, type="primary"):
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
                            st.session_state.candidate_data['tech_stack']
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
                if st.button("End Interview", use_container_width=True, type="secondary"):
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
            
            <p>Your responses have been saved and someone from our team will contact you regarding the next steps.</p>
            
            <p><em>We appreciate your interest in our opportunities!</em></p>
        </div>
        """, unsafe_allow_html=True)
        
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
        - 😊 Sentiment analysis
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