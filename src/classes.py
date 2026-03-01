from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)
import os
import sqlite3
import sqlite3
from datetime import datetime
import io
from pypdf import PdfReader
from langchain_core.documents import Document


load_dotenv()
# Loads environment variables from .env at import time.
# NOTE: This does NOT validate whether required keys (like GROQ_API_KEY) exist.
# Failure is deferred to LLM initialization later, which can slow debugging.

class Database:
    def __init__(self, db_path="studymate.db"):
        self.conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Sessions table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL UNIQUE,
            subject_category TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # Documents table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            doc_name TEXT,
            file_path TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """)

        # Messages table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            sender TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """)
        self.conn.commit()

    # ------------------- Session Methods -------------------

    def add_session(self, session_name, subject_category):
        if self.session_exists(session_name):
            return None  # Already exists
    
        created_at = datetime.now().isoformat()
    
        self.cursor.execute(
            "INSERT INTO sessions (session_name, subject_category, created_at) VALUES (?, ?, ?)",
            (session_name, subject_category, created_at)
        )
    
        self.conn.commit()
        return self.cursor.lastrowid


    def session_exists(self, session_name):
        self.cursor.execute(
            "SELECT 1 FROM sessions WHERE session_name=?",
            (session_name,)
        )
        return self.cursor.fetchone() is not None

    def get_sessions(self):
        self.cursor.execute("SELECT * FROM sessions")
        return self.cursor.fetchall()

    def get_session_id(self, session_name):
        self.cursor.execute(
            "SELECT session_id FROM sessions WHERE session_name=?",
            (session_name,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_subject_category(self, session_name):
        self.cursor.execute(
            "SELECT subject_category FROM sessions WHERE session_name=?",
            (session_name,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def delete_session(self, session_name):
        session_id = self.get_session_id(session_name)
        if not session_id:
            print("No session_id found!")
            return False
        print("Deleting session_id:", session_id)  # DEBUG
        # Delete messages
        deleted_messages = self.cursor.execute("DELETE FROM messages WHERE session_id=?", (session_id,)).rowcount
        print("Messages deleted:", deleted_messages)
        # Delete documents
        deleted_docs = self.cursor.execute("DELETE FROM documents WHERE session_id=?", (session_id,)).rowcount
        print("Documents deleted:", deleted_docs)
        # Delete session
        deleted_sess = self.cursor.execute("DELETE FROM sessions WHERE session_id=?", (session_id,)).rowcount
        print("Session deleted:", deleted_sess)
        self.conn.commit()
        return True

     # ------------------- Document Methods -------------------

    def add_document(self, session_id, doc_name, file_path):
        self.cursor.execute(
            "INSERT INTO documents (session_id, doc_name, file_path) VALUES (?, ?, ?)",
            (session_id, doc_name, file_path)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def add_documents_bulk(self, session_id, docs_list):
        entries = [(session_id, os.path.basename(path), path) for path in docs_list]
        self.cursor.executemany(
            "INSERT INTO documents (session_id, doc_name, file_path) VALUES (?, ?, ?)",
            entries
        )
        self.conn.commit()

    def get_documents(self, session_id):
        self.cursor.execute(
            "SELECT * FROM documents WHERE session_id=?",
            (session_id,)
        )
        return self.cursor.fetchall()

    def get_document_paths(self, session_id):
        self.cursor.execute(
            "SELECT file_path FROM documents WHERE session_id=?",
            (session_id,)
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ------------------- Message Methods -------------------

    def add_message(self, session_id, sender, content):
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO messages (session_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, sender, content, timestamp)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_messages(self, session_id):
        self.cursor.execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY timestamp ASC",
            (session_id,)
        )
        return self.cursor.fetchall()

    def get_latest_message(self, session_id):
        self.cursor.execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY timestamp DESC LIMIT 1",
            (session_id,)
        )
        return self.cursor.fetchone()

    def get_last_k_messages_by_name(self, session_name: str, k: int):
        """
        Fetch last k messages using session_name instead of session_id.
        Returns messages in chronological order (oldest → newest).
        """
        self.cursor.execute("""
            SELECT m.message_id, m.session_id, m.sender, m.content
            FROM messages m
            JOIN sessions s ON m.session_id = s.session_id
            WHERE s.session_name = ?
            ORDER BY m.message_id DESC
            LIMIT ?
        """, (session_name, k))
    
        rows = self.cursor.fetchall()
        return rows[::-1]  # reverse to chronological order

    # ------------------- Cleanup -------------------
    def close(self):
        self.conn.close()



class vectordb:
    def __init__(self, db_path="studymate.db", persist_dir="./chroma_db"):
        self.embedding_model_name = os.environ.get("EMBEDDING_MODEL")
        self.embedding_engine = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name
        )
        self.persist_directory = persist_dir
        self.database = Database(db_path=db_path)
        self.database._create_tables()
        self.textsplitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " "]
        )
        print("Vector database initialized successfully.")


    def _save_session_name(self, session_name, subject_category):
        id = self.database.add_session(session_name, subject_category)



    def create_session(self, session_name, subject_category):
        """
        Attempts to create a new session.
        Returns True if session was created successfully.
        Returns False if session already exists.
        """
        if self.database.session_exists(session_name):  ## Query function 1
            return False  # session exists, do not create
        
        # Create new Chroma collection
        collection = Chroma(
            collection_name=session_name,
            embedding_function=self.embedding_engine,
            persist_directory=self.persist_directory
        )
        # Persist the session name
        self._save_session_name(session_name, subject_category)
        return True

    def list_sessions(self):
        sessions = self.database.get_sessions()
        if not sessions:
            print("[INFO] No sessions found.")
            return
        print("---- Sessions ----")
        for idx, sess in enumerate(sessions, start=1):
            print(f"{idx}. {sess[1]}")  # sess[1] = session_name
        print("-----------------")


    def get_session(self, session_name):
        """
        Retrieve the Chroma collection for a given session name.
        Returns the collection object if exists, else None.
        """
        # Caller must handle None safely.
        # This method also prints a warning, which may cause duplicated warnings
        # if caller prints its own error messages.
        if not self.database.session_exists(session_name):
           print(f"Session {session_name} not exist in the database.") 
           return None
        return Chroma(
             collection_name=session_name,
             embedding_function=self.embedding_engine,
             persist_directory=self.persist_directory
             )


    def chunk_document(self, document):
        # Splits a loaded document into chunks using predefined splitter.
        # Thin wrapper function; mainly for readability and future extensibility.
        chunks = self.textsplitter.split_documents(document)
        return chunks


    def add_file(self, documents_list, session_name):
        """
        Adds one or more PDF documents to a given session.
        Updates both Chroma collection and SQLite database.
        Assumes session existence has already been validated.
        """
        # Get session ID from DB
        session_id = self.database.get_session_id(session_name)
    
        # Instantiate Chroma collection for this session
        collection = Chroma(
            collection_name=session_name,
            embedding_function=self.embedding_engine,
            persist_directory=self.persist_directory
        )
    
        # Process each document
        for i, item in enumerate(documents_list, start=1):
            try:
                if isinstance(item, str):
                    # Handle as file path (CLI compatibility)
                    if not os.path.exists(item):
                        print(f"[WARN] File '{item}' not found, skipping.")
                        continue
                    loader = PyPDFLoader(item)
                    document = loader.load()
                    doc_name = os.path.basename(item)
                    doc_path = item
                else:
                    # Handle as file-like object (Streamlit compatibility)
                    # item is likely an UploadedFile or BytesIO
                    reader = PdfReader(item)
                    document = []
                    for page_idx, page in enumerate(reader.pages):
                        text = page.extract_text()
                        document.append(Document(
                            page_content=text, 
                            metadata={"source": item.name, "page": page_idx}
                        ))
                    doc_name = item.name
                    doc_path = f"in-memory://{item.name}"

                # Chunk the document
                chunks = self.chunk_document(document)
    
                # Add chunks to Chroma
                collection.add_documents(chunks)
    
                # Save document metadata to SQLite
                self.database.add_document(session_id, doc_name, doc_path)
    
                print(f"[INFO] Document {i}: '{doc_name}' added successfully.")
    
            except Exception as e:
                print(f"[ERROR] Failed to add document {i}: {e}")

    
    

    def delete_session(self, session_name):
        deleted = self.database.delete_session(session_name)
        if deleted:
            print(f"Session {session_name} deleted successfully.")
        else:
            print(f"Sesssion not exist to delete.")

class RAGAssistant:
    def __init__(self, vector_database):
        self.llm = self._initialize_llm()
        self.vector_db = vector_database
        self.similarity_threshold = 0.75
        print("[INFO] RAGAssistant initialized successfully.")

    def _initialize_llm(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key not found in environment variables!")
        return ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            reasoning_format="hidden",
            max_retries=2
        )

    # ---------------- Prompt builders ----------------
    def _build_strict_prompt(self, session_name, question, past_conversation, context_text, subject_category):
        """
        Prompt using ONLY session documents + memory
        """
        system_msg = SystemMessagePromptTemplate.from_template(
                            """
                You are StudyMate, an AI educational assistant.
            
                TASK:
                1. First, check if the provided context documents contain the answer to the user's question.
                   - If yes, answer the question **using only the context**, in natural, clear language.
                   - Step-by-step or bullet points are fine if needed.
                2. If the answer is **not in the context**, check if the question is closely related to the session's subject category ({subject_category}).
                   - If yes, answer the question using **general knowledge**, without referencing the context.
                   - If no, respond exactly: "I don't know. No relevant information found."
            
                INPUTS:
                - Session Name: {session_name}
                - Past Conversation: {past_conversation}
                - Context Documents: {context_text}
                - User Question: {question}
                - Session Subject Category: {subject_category}
            
                RULES:
                - Never invent answers from context if it is not present.
                - Always follow the decision process strictly.
                - Keep your answer concise, clear, and relevant.
                """
            )

        human_msg = HumanMessagePromptTemplate.from_template(
            "Question: {question}\nContext: {context_text}\nPast Conversation: {past_conversation}"
        )
        return ChatPromptTemplate.from_messages([system_msg, human_msg])

    def _build_general_prompt(self, session_name, question, past_conversation, subject_category):
        """
        Prompt using general knowledge but filtered by session subject
        """
        system_msg = SystemMessagePromptTemplate.from_template(
             """
             You are StudyMate, an AI educational assistant.
         
             ROLE:
             - Answer questions normally if they relate to the session's subject category: {subject_category}.
             - If the question is unrelated to this subject category, respond exactly: "I don't know. No relevant information found."
            - If the question is unrelated to this subject category but the {subject_category} is "General", answer the question normally.
             - Use past conversation only for context, but do not quote it in your answer.
             
             INPUT:
             - Past conversation: {past_conversation}
             - User question: {question}
             """
        )
        human_msg = HumanMessagePromptTemplate.from_template(
            "Question: {question}\nSession Subject: {subject_category}\nPast Conversation: {past_conversation}"
        )
        return ChatPromptTemplate.from_messages([system_msg, human_msg])

    # ---------------- Query ----------------
    def query(self, session_name: str, question: str, n_results: int = 5):
        """
        Retrieve relevant chunks and past conversation,
        decide which prompt to use (strict or general),
        then stream output.
        """
        # ---------------- Memory ----------------
        last_messages = self.vector_db.database.get_last_k_messages_by_name(session_name, 6)
        memory_text = ""
        for m in last_messages:
            role = "User" if m[2] == "user" else "Assistant"
            memory_text += f"{role}: {m[3]}\n"

        # ---------------- Session & Docs ----------------
        collection = self.vector_db.get_session(session_name)
        subject_category = self.vector_db.database.get_subject_category(session_name)


        # Similarity search
        docs_with_scores = collection.similarity_search_with_score(question, k=n_results)
        # Filter by threshold
        filtered_docs = [doc for doc, score in docs_with_scores if score >= self.similarity_threshold]
        
        # Decide which prompt to use
       
            # Use strict prompt with document context
        context_text = "\n\n".join(doc.page_content for doc in filtered_docs)
        prompt = self._build_strict_prompt(session_name, question, memory_text, context_text, subject_category)
        # Chain
        self.chain = prompt | self.llm

        # Stream output
        for chunk in self.chain.stream({
            "question": question,
            "past_conversation": memory_text,
            "context_text": "\n\n".join(doc.page_content for doc in filtered_docs) if filtered_docs else "",
            "session_name": session_name,
            "subject_category": subject_category
        }):
            yield chunk.content

