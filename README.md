# 🚀 Banking AI Assistant

## 📌 Table of Contents
- [🎯 Introduction](#-introduction)
- [🎥 Demo](#-demo)
- [💡 Inspiration](#-inspiration)
- [⚙️ What It Does](#️-what-it-does)
- [🛠️ How We Built It](#️-how-we-built-it)
- [🚧 Challenges We Faced](#-challenges-we-faced)
- [🏃 How to Run](#-how-to-run)
- [🏗️ Tech Stack](#-tech-stack)
- [👥 Team](#-team)  
---

## 🎯 Introduction
The Banking AI Assistant is an AI-powered system that bridges the gap between everyday language and complex database queries. This project tackles the challenge of enabling non-technical users to effortlessly retrieve and analyze banking data by converting natural language questions into accurate SQL commands. Built for the AI Hackathon, it democratizes access to valuable banking insights through conversational AI.

## 🎥 Demo
📹 [[Video Demo](https://github.com/eft-hackathon/hackathon1-ai-avengers/blob/test/artifacts/demo/2025-08-31%2016-21-53.mkv)](#) (if applicable)  

## 💡 Inspiration
Our inspiration came from observing the daily struggles of banking professionals and analysts who need to extract insights from complex databases but lack SQL expertise. We envisioned a system where anyone could ask questions like:
"Show me all customers with checking accounts"
"What's the average transaction amount this quarter?"
"Which employees handled the most transactions?"
And receive immediate, accurate results without writing a single line of SQL code.

## ⚙️ What It Does

Core Features
🗣️ Natural Language Processing: Converts plain English questions to SQL queries
💬 Interactive Chat Interface: Streamlit-based conversational UI with memory
🔍 Smart Query Execution: Real-time database querying with result visualization
❓ Clarification Handling: Asks follow-up questions when queries are ambiguous
📊 Comprehensive Testing: Automated test suite with 35+ banking scenarios
📈 Performance Analytics: Detailed reports on query success rates and execution times


## 🛠️ How We Built It
<img width="2400" height="1600" alt="image" src="https://github.com/user-attachments/assets/c3995fc5-9b32-45bf-978c-79e44f559fce" />


## 🚧 Challenges We Faced
Technical Challenges
🔄 Model Deprecation Crisis: Mid-hackathon, Groq deprecated llama3-8b-8192, requiring urgent migration to llama-3.1-8b-instant
🎯 Schema Alignment: Ensuring AI-generated SQL matched actual database structure and column names
⚡ Performance Optimization: Balancing query accuracy with response speed
🛡️ Error Handling: Creating robust error detection and user-friendly error messages

Solutions Implemented
Adaptive Model Management: Built flexible model configuration for easy updates
Schema Validation: Comprehensive schema verification and testing framework
Query Optimization: Intelligent SQL parsing and execution with detailed logging
User Experience: Clarification system for ambiguous queries

## 🏃 How to Run

Prerequisites:

Python 3.8 or higher

Groq API key (Get one here)

Clone the repository: 

git clone https://github.com/eft-hackathon/hackathon1-ai-avengers.git
cd hackathon1-ai-avengers/code

Install dependencies:

pip install -r requirements.txt

Setup environment variables:

Create a .env file in the code directory:

   GROQ_API_KEY=your_groq_api_key_here
   DB_PATH=src/banking_system.db

Initialize the database: 

python init_db.py

Access the app

Open your browser to http://localhost:8501

Running Tests

Execute the comprehensive test suite:

cd code/src/test
python test_executor.py



## 🏗️ Tech Stack
🎨 Frontend: Streamlit for rapid prototyping and deployment

🧠 AI/NLP: Groq API (llama-3.1-8b-instant) with LangChain framework

💾 Database: SQLite with banking schema (branches, customers, accounts, transactions)

🔧 Backend: Python with pandas for data processing

🧪 Testing: Custom test executor with comprehensive reporting

## 👥 Team
- **Your Name** - [[GitHub](https://github.com/RohitKSadhukhan)](#) | [[LinkedIn](https://www.linkedin.com/in/rohit-sadhukhan-a350981b2/)](#)
- **Teammate 2** - [[GitHub](https://github.com/decocse)](#) | [[LinkedIn](https://www.linkedin.com/in/debanjan-bhattacharjee-05532119a/)](#)
