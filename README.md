# TalentScout AI Hiring Assistant

## Project Overview

The TalentScout AI Hiring Assistant is a Streamlit-based application designed to streamline the initial stages of the technical recruitment process. It leverages Artificial Intelligence, specifically Large Language Models (LLMs), to conduct personalized technical interviews, evaluate candidate responses, and provide insights into candidate sentiment. This project demonstrates the effective application of LLMs in a real-world recruitment scenario.

## Features

*   **Multilingual Support:** Conducts interviews in multiple languages, including English, Spanish, French, German, Hindi, and Chinese, for both UI and LLM responses.
*   **Personalized Technical Questions:** Generates exactly 4 technical questions (2 Easy, 1 Medium, 1 Hard) tailored to the candidate's specified tech stack and years of experience.
*   **Intelligent Answer Evaluation:** Uses LLM to evaluate answers as ADEQUATE, NEEDS_CLARIFICATION, or IRRELEVANT, with clear criteria for each category:
    - ADEQUATE: Technically correct, complete, and well-explained answers
    - NEEDS_CLARIFICATION: Partially correct but incomplete answers
    - IRRELEVANT: Off-topic or incorrect answers
*   **Input Validation:** Performs thorough validation of answers before evaluation, checking for:
    - Blank or very short responses
    - Gibberish or repeated characters
    - Insufficient technical detail
*   **Sentiment Analysis:** Analyzes the sentiment of candidate responses during the interview to provide insights into their confidence level.
*   **Context Handling:** Maintains the flow and context of the conversation to ensure a coherent and seamless user experience throughout the interview.
*   **Fallback Mechanism:** Provides meaningful responses and alternative questions when the LLM does not understand user input or encounters unexpected issues, ensuring a robust interaction.
*   **Local Data Storage:** Securely stores candidate information, interview chat history, and analytics data locally in a structured directory, compliant with data privacy best practices.
*   **GDPR Compliance:** Incorporates a data consent mechanism to ensure adherence to data privacy standards.
*   **User-Friendly Interface:** Provides a clean and intuitive Streamlit interface for an engaging user experience.

## Local Development Setup

To run the TalentScout AI Hiring Assistant on your local machine, follow these steps:

### Prerequisites

*   Python 3.9+
*   pip (Python package installer)
*   Git

### 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone https://github.com/your-username/talentscout_hiring_chatbot.git
cd talentscout_hiring_chatbot
```

### 2. Set Up a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
```

Activate the virtual environment:

*   **Windows:**
    ```bash
    .\venv\Scripts\activate
    ```
*   **macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The application requires an API key for Groq. Create a `.env` file in the root directory of the project and add your Groq API key:

```env
GROQ_API_KEY="your_groq_api_key_here"
```

Replace `"your_groq_api_key_here"` with your actual Groq API key.

### 5. Run the Application

Once the environment is set up and dependencies are installed, you can run the Streamlit application:

```bash
streamlit run main.py
```

This command will open the application in your default web browser.

## Technical Details

This project is developed using Python and leverages the following key libraries and tools:

*   **Streamlit:** For building the interactive and user-friendly web interface.
*   **Groq API:** Utilized as the Large Language Model provider.
*   **llama3-8b-8192:** The specific pre-trained LLM model from Groq used for generating technical questions and evaluating candidate answers.
*   **textblob:** For sentiment analysis of user responses.
*   **python-dotenv:** For managing environment variables securely.

## Answer Evaluation System

The application uses a sophisticated answer evaluation system that:

1. **Pre-evaluation Validation:**
   - Checks for blank or very short responses
   - Detects gibberish or repeated characters
   - Ensures sufficient technical detail

2. **LLM-based Evaluation:**
   - Evaluates answers as ADEQUATE, NEEDS_CLARIFICATION, or IRRELEVANT
   - Provides specific feedback for each evaluation type
   - Uses clear criteria for each evaluation category

3. **Retry Mechanism:**
   - Allows up to 2 attempts for each question
   - Provides constructive feedback for improvement
   - Automatically progresses after 2 failed attempts

4. **Progress Tracking:**
   - Maintains question progression state
   - Tracks evaluation history
   - Stores final evaluation results

## Prompt Design

Effective prompt engineering is central to the chatbot's functionality. Prompts are carefully crafted to:

*   **Gather Information Accurately:** Guide the language model to collect essential candidate details comprehensively.
*   **Generate Relevant Questions:** Ensure that technical questions are precisely tailored to the candidate's declared tech stack and experience level, covering a variety of technologies and frameworks.
*   **Ensure Desired Output Format:** Structure prompts to guide the LLM in producing clear, concise, and structured outputs, such as the exact format for technical questions and answer evaluations.

## Data Handling

The application stores all candidate interview data, including personal information, chat history, and interview analytics, locally within a `data/` directory created in the project root. The data is organized as follows:

*   `data/candidates/[YYYY-MM-DD]/`: Stores individual candidate JSON files.
*   `data/analytics/`: Contains aggregated interview analytics.
*   `data/backups/[YYYY-MM-DD]/`: Stores backups of individual candidate JSON files.

Each candidate's data is saved in a JSON format, ensuring a structured and retrievable record of the interview process. All data handling is designed to comply with data privacy standards, such as GDPR.

## Usage

1.  **Consent Stage:** Users must consent to data collection and privacy policies before proceeding.
2.  **Form Stage:** Candidates fill in their personal details, including full name, email, phone, years of experience, desired position, location, and tech stack.
3.  **Interview Stage:** The AI assistant generates and asks 4 technical questions based on the provided tech stack and experience. Candidates provide their answers. The interview can be ended prematurely by typing 'end', 'quit', or 'stop'.
4.  **Completion/Ended Stage:** Upon completing all questions or ending the interview, the application provides a summary and saves all collected data.

## Code Quality

This project adheres to strong code quality standards:

*   **Structure & Readability:** The codebase is well-structured and modular, following best practices for readability and maintainability.
*   **Documentation:** Comprehensive comments and docstrings are included to explain complex logic, functions, and key architectural decisions.
*   **Version Control:** Git is utilized for version control, ensuring clear commit messages and a well-organized repository history.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License.

## Contact

For any inquiries or support, please contact Dev Parekh | devparekh21@gmail.com | 
