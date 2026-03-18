import os
import sys
import json
from unittest.mock import MagicMock
import numpy as np
import pypdf
from groq import Groq
import config_manager

# --- 1. KILLS TELEMETRY PERMANENTLY ---
sys.modules['posthog'] = MagicMock()
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# --- 2. NUMPY 2.0 COMPATIBILITY PATCH ---
if not hasattr(np, 'float_'):
    np.float_ = np.float64
if not hasattr(np, 'complex_'):
    np.complex_ = np.complex128

# --- 3. DYNAMIC GROQ CLIENT ---
def get_groq_client():
    return Groq(api_key=config_manager.get_api_key())

# --- 4. LAZY LOADED OCR ---
_reader = None
def get_ocr_reader():
    global _reader
    if _reader is None:
        print("Initializing EasyOCR (this takes a moment)...")
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader

# --- 5. LAZY LOADED DATABASE ---
def get_db_client(workspace_path):
    import chromadb
    from chromadb.config import Settings
    db_path = os.path.join(workspace_path, "chroma_db")
    return chromadb.PersistentClient(
        path=db_path, 
        settings=Settings(anonymized_telemetry=False)
    )

# --- CORE FUNCTIONS ---

def extract_text_from_file(filepath):
    text = ""
    if filepath.lower().endswith('.pdf'):
        try:
            with open(filepath, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            if len(text.strip()) < 50: 
                print("Minimal text found in PDF. Scanned PDFs require image extraction first.")
        except Exception as e:
            print(f"Error reading PDF: {e}")
            
    elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Only loads PyTorch/EasyOCR if an image is actually uploaded!
        reader = get_ocr_reader()
        results = reader.readtext(filepath, detail=0)
        text = " ".join(results)
        
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def setup_chromadb(workspace_path, documents):
    client = get_db_client(workspace_path)
    collection = client.get_or_create_collection(name="granth_collection")
    
    for i, doc in enumerate(documents):
        chunks = chunk_text(doc['text'])
        for j, chunk in enumerate(chunks):
            collection.upsert(
                documents=[chunk],
                metadatas=[{"source": doc['filename']}],
                ids=[f"{doc['filename']}_chunk_{j}"]
            )
    return collection

def load_history(workspace_path):
    history_path = os.path.join(workspace_path, "history.json")
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    return []

def save_history(workspace_path, history):
    history_path = os.path.join(workspace_path, "history.json")
    with open(history_path, 'w') as f:
        json.dump(history, f)

def load_notes(workspace_path):
    notes_path = os.path.join(workspace_path, "notes.json")
    if os.path.exists(notes_path):
        with open(notes_path, 'r') as f:
            return json.load(f)
    return []

def save_notes(workspace_path, notes):
    notes_path = os.path.join(workspace_path, "notes.json")
    with open(notes_path, 'w') as f:
        json.dump(notes, f)

def query_granthex(workspace_path, query_text):
    client = get_db_client(workspace_path)
    collection = client.get_or_create_collection(name="granth_collection")
    
    if collection.count() == 0:
        return "Please upload a document first before asking questions."
        
    results = collection.query(query_texts=[query_text], n_results=3)
    docs = results.get('documents', [[]])[0]
    context = "\n".join([d for d in docs if d]) if docs else ""
    
    chat_history = load_history(workspace_path)
    
    sys_prompt = f"""You are GrantheX, an AI assistant. Use the context to answer. 
    CRITICAL MATH RULE: ALWAYS enclose block equations in $$ and inline math in $. Never use parentheses or brackets for math.
    Context: {context}"""
    
    messages = [{"role": "system", "content": sys_prompt}]
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query_text})
    
    chat_completion = get_groq_client().chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
    )
    answer = chat_completion.choices[0].message.content
    
    chat_history.append({"role": "user", "content": query_text})
    chat_history.append({"role": "assistant", "content": answer})
    save_history(workspace_path, chat_history)
    
    return answer

def generate_source_guide(workspace_path):
    client = get_db_client(workspace_path)
    collection = client.get_or_create_collection(name="granth_collection")
    
    if collection.count() == 0:
        return {"summary": "Upload a document to generate a summary.", "questions": []}

    results = collection.get(limit=10, include=['documents'])
    doc_list = results.get('documents', [])
    valid_docs = [doc for doc in doc_list if doc]
    context = "\n".join(valid_docs)
    
    prompt = f"""You are GrantheX. Based on the following document excerpts, provide:
    1. A brief 2-3 sentence summary of the core topic.
    2. Exactly 3 insightful questions the user could ask to learn more.
    Format your response strictly as valid JSON like this:
    {{"summary": "...", "questions": ["Q1", "Q2", "Q3"]}}
    Context: {context[:15000]}
    """
    
    chat_completion = get_groq_client().chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"} 
    )
    return json.loads(chat_completion.choices[0].message.content)

def generate_audio_overview(workspace_path):
    client = get_db_client(workspace_path)
    collection = client.get_or_create_collection(name="granth_collection")
    
    if collection.count() == 0:
        raise ValueError("No documents found to generate audio.")
        
    results = collection.get(limit=15, include=['documents'])
    doc_list = results.get('documents', [])
    context = "\n".join([doc for doc in doc_list if doc])
    
    prompt = f"""Based on this context, write a very short, engaging 1-minute podcast script. 
    It should be a monologue by a host named 'GrantheX' summarizing the most fascinating points.
    Do not include sound effects or stage directions, just the spoken text.
    Context: {context[:15000]}
    """
    
    chat_completion = get_groq_client().chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    
    script_text = chat_completion.choices[0].message.content
    if not script_text or not script_text.strip():
        raise ValueError("Groq returned an empty script.")
        
    import re
    # Lazy Load gTTS only when audio is actually requested
    from gtts import gTTS 
    
    clean_text = re.sub(r'[*#_]', '', script_text)
    audio_path = os.path.join(workspace_path, "overview.mp3")
    
    tts = gTTS(text=clean_text, lang='en', slow=False)
    tts.save(audio_path)
    
    return "overview.mp3"