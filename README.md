<div align="center">
  <img src="static/images.png" alt="Alt text" width="400"/>


<h1>StudyMate 📚</h1>
  <p><b>Your AI-powered academic co-pilot for deep, focused learning.</b></p>
  <p>The “Study Buddy” that actually <i>remembers</i> what you’re studying.</p>
  <p>🎯 Focused Learning · 🧠 Smart Document Q&A · ⚡ Instant Session Recall</p>

</div>

---

## StudyMate: Your Session-Based Study Hub

StudyMate isn’t just a chat tool; it’s a Session-Based Study Hub designed to organize your study materials and give you smarter, context-aware AI assistance. It turns messy PDFs and notes into a structured, interactive learning experience.

## Who It’s For

Students: Get AI help that’s session-specific—answers based only on your uploaded PDFs.

Learners: Keep your study sessions organized and track your progress.

Knowledge Seekers: Ask questions and get answers that combine your session documents with general knowledge, for deeper understanding.


## 🛠️ Installation & Setup

1. **Clone & Environment**
```bash
git clone https://github.com/yourusername/studymate.git
cd studymate
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```
3. Configure Secrets
Create a .env file in the root:
```bash
GROQ_API_KEY="your_groq_api_key_here"
EMBEDDING_MODEL="model_name_here"
```
4. Launch StudyMate
```bash
streamlit run app.py
```

## How to Use StudyMate

### 1. Create a Study Session
Start by creating a session for a course, topic, or exam. Each session keeps its documents and AI context separate.

### 2. Upload Documents
Add PDFs or study material to the session. StudyMate automatically chunks them for AI to read and understand.

### 3. Ask Questions in Chat
Use the chat feature to ask anything about your uploaded documents. The AI answers with session-specific context, so you get precise and relevant responses.

### 4. Manage & Review
Track session activity, review uploaded documents, or delete outdated sessions to keep everything tidy.


### 🛠️ Tech Stack
Langchain · Streamlit · SQLite · Chroma · HuggingFace Embeddings Model

## 📂 Project Structure
```bash
StudyMate/
├── src/
│   ├── app.py
│   └── classes.py
├── static/
├── README.md
├── LICENSE
└── requirements.txt
```


## ⚠️ Note: 
Live deployment is coming soon. 

