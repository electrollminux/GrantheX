# GrantheX - AI Notebook
![icon](https://github.com/electrollminux/GrantheX/blob/main/icon_file.jpeg)
The name itself is derived from the word Grantha (ग्रन्थ) from Sanskrit which refers to a literary work, book, treatise, or binding of verses. GrantheX is a small offline-first Desktop application built in Python that acts as an intelligent, RAG-powered notebook. Inspired by Google's NotebookLM, it allows users to upload documents, generate instant summaries, chat with their sources, and even generate fully voiced Audio Deep Dives.

## Features
* **Local Document Processing:** Uses EasyOCR and PyPDF to read documents entirely on your CPU.
* **Intelligent RAG:** Powered by ChromaDB for fast vector retrieval and the Groq API (llama-3.3-70b-versatile) for incredibly fast, accurate answers.
* **Audio Deep Dives:** Automatically generates and synthesizes a 1~4 minutes podcast script summarizing your documents using `gTTS`.
* **Interactive UI:** Built with Flask and PyWebview for a native desktop feel, featuring a custom audio scrubber, markdown/LaTeX equation rendering, and a pinboard for saving notes.
* **Portable Workspaces:** Saves your entire notebook history and databases into shareable `.gex` files.

##  How to Run from Source
1. Clone this repository: `git clone https://github.com/electrollminux/GrantheX.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`

##  Download the App
Not a developer? You can download the standalone Windows installer from the [Releases page](../../releases).