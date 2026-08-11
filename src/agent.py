import os
import glob
import chromadb
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    raise ValueError("Valid GEMINI_API_KEY not found in .env file. Please add it.")
    
# Initialize the new Google GenAI client
client = genai.Client(api_key=api_key)

# Initialize ChromaDB (Local vector database)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="research_docs")

def load_documents(data_dir="data"):
    """Reads all text files in the data directory and adds them to ChromaDB."""
    global collection
    print(f"Loading documents from {data_dir}...")
    
    # Clear existing documents to avoid duplicates during testing
    if collection.count() > 0:
        chroma_client.delete_collection("research_docs")
        collection = chroma_client.create_collection("research_docs")

    documents = []
    metadatas = []
    ids = []
    
    file_paths = glob.glob(os.path.join(data_dir, "*.txt"))
    if not file_paths:
        print("No documents found in the data directory.")
        return collection
        
    for idx, file_path in enumerate(file_paths):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            filename = os.path.basename(file_path)
            
            # For simplicity in this demo, each file is treated as a single chunk.
            documents.append(content)
            metadatas.append({"source": filename})
            ids.append(f"doc_{idx}")
            
    # Add to ChromaDB. It uses a local embedding model automatically!
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Successfully loaded {len(documents)} documents into the database.")
    return collection

def ask_agent(query):
    """Retrieves relevant documents and uses Gemini to answer with citations."""
    print(f"\n[Question]: {query}")
    
    # 1. Retrieve the most relevant documents using semantic search
    results = collection.query(
        query_texts=[query],
        n_results=2 # Fetch top 2 most relevant chunks
    )
    
    retrieved_docs = results['documents'][0]
    retrieved_metadata = results['metadatas'][0]
    
    # 2. Format the context for the prompt
    context = ""
    for i in range(len(retrieved_docs)):
        source = retrieved_metadata[i]['source']
        text = retrieved_docs[i]
        context += f"--- START SOURCE: {source} ---\n{text}\n--- END SOURCE ---\n\n"
        
    # 3. Construct the prompt with strict rules to prevent hallucination
    prompt = f"""You are a strict and precise research assistant.
Your job is to answer the user's question using ONLY the provided sources below.

RULES:
1. You must answer based ONLY on the provided sources. 
2. If the sources do not contain the answer, you must reply EXACTLY with: "The provided sources do not contain the answer to this question."
3. For every claim you make, you MUST cite the source file it came from at the end of the sentence like this: [Source: filename.txt]

SOURCES:
{context}

USER QUESTION: {query}
"""

    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    
    print("\n[Answer]:")
    print(response.text.strip())
    print("-" * 60)
    return response.text

if __name__ == "__main__":
    # 1. Load documents into the vector database
    load_documents()
    
    print("\n" + "="*60)
    print("Research Agent (with Citations) Initialized")
    print("="*60)
    
    # 2. Run test questions
    ask_agent("What is the fundamental unit of information in a quantum computer, and what special state allows it to perform simultaneous calculations?")
    
    ask_agent("Which rover is currently searching for signs of ancient life on Mars, and where did it land?")
    
    # This question tests if the model will hallucinate or follow rule #2
    ask_agent("When did the Apollo 11 mission land on the moon?")
