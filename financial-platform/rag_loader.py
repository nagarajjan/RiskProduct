import pandas as pd
import json
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader

class RAGKnowledgeBase:
    def __init__(self, api_key: str):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.db = None
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

    def ingest_data_from_csv(self, file_path: str):
        """Processes a CSV file and ingests it."""
        print(f"Ingesting data from CSV: {file_path}")
        df = pd.read_csv(file_path)
        docs = [Document(page_content=row.to_json()) for _, row in df.iterrows()]
        return self.text_splitter.split_documents(docs)

    def ingest_data_from_json(self, file_path: str):
        """Processes a JSON file and ingests it."""
        print(f"Ingesting data from JSON: {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        docs = [Document(page_content=json.dumps(item)) for item in data]
        return self.text_splitter.split_documents(docs)
    
    def ingest_data_from_pdf(self, file_path: str):
        """Processes a PDF file and ingests it."""
        print(f"Ingesting data from PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        docs = loader.load_and_split()
        return self.text_splitter.split_documents(docs)

    def build_knowledge_base(self, files: list):
        """Ingests all documents from the provided file list."""
        all_docs = []
        for file in files:
            if file.endswith('.csv'):
                all_docs.extend(self.ingest_data_from_csv(file))
            elif file.endswith('.json'):
                all_docs.extend(self.ingest_data_from_json(file))
            elif file.endswith('.pdf'):
                all_docs.extend(self.ingest_data_from_pdf(file))
            else:
                print(f"Skipping unsupported file format: {file}")

        self.db = FAISS.from_documents(all_docs, self.embeddings)

    def retrieve_context(self, query: str, k: int = 5):
        """Retrieves relevant context from the vector database."""
        if not self.db:
            return "Knowledge base not yet populated."
        docs = self.db.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in docs])

