import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchVectorStore:
    """
    Manages the vector store for equity research documents using ChromaDB
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.collection_name = "equity_research"
        
        # Initialize embeddings using SentenceTransformers (compatible with LangChain)
        self.embeddings = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize Chroma vector store with LangChain-compatible embedding function
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        
        logger.info(f"ChromaDB initialized at {persist_directory}")
    
    def load_documents_from_directory(self, docs_path: str) -> List[Document]:
        """Load and split documents from the docs directory"""
        try:
            # Load markdown files
            loader = DirectoryLoader(
                docs_path, 
                glob="*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""]
            )
            
            split_docs = text_splitter.split_documents(documents)
            
            # Add metadata for better retrieval
            for doc in split_docs:
                # Extract company code from filename
                filename = os.path.basename(doc.metadata.get('source', ''))
                company_code = filename.split('_')[0] if '_' in filename else 'UNKNOWN'
                doc.metadata['company_code'] = company_code
                doc.metadata['document_type'] = 'research_report'
            
            logger.info(f"Loaded {len(split_docs)} document chunks from {docs_path}")
            return split_docs
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def add_documents_to_store(self, documents: List[Document]):
        """Add documents to the vector store"""
        try:
            if documents:
                self.vectorstore.add_documents(documents)
                logger.info(f"Added {len(documents)} documents to vector store")
            else:
                logger.warning("No documents to add to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
    
    def setup_vector_store(self, docs_path: str = "./docs"):
        """Initialize the vector store with research documents"""
        try:
            # Check if vector store already has documents
            collection = self.client.get_collection(self.collection_name)
            if collection.count() > 0:
                logger.info(f"Vector store already contains {collection.count()} documents")
                return
        except:
            # Collection doesn't exist yet, that's fine
            pass
        
        # Load and add documents
        docs_directory = os.path.join(os.path.dirname(__file__), docs_path)
        if os.path.exists(docs_directory):
            documents = self.load_documents_from_directory(docs_directory)
            if documents:
                self.add_documents_to_store(documents)
            else:
                logger.warning(f"No documents found in {docs_directory}")
        else:
            logger.error(f"Docs directory not found: {docs_directory}")
    
    def search_similar_documents(self, query: str, company_code: str = None, k: int = 5) -> List[Document]:
        """Search for similar documents in the vector store"""
        try:
            # Build filter if company code is specified
            filter_dict = None
            if company_code:
                filter_dict = {"company_code": company_code}
            
            # Search similar documents
            results = self.vectorstore.similarity_search(
                query, 
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_context_for_company(self, company_code: str, query: str = "", k: int = 10) -> str:
        """Get relevant context for a specific company"""
        try:
            # If no specific query, get general company information
            search_query = query if query else f"{company_code} financial performance business overview"
            
            # Search for relevant documents
            docs = self.search_similar_documents(search_query, company_code, k)
            
            if not docs:
                return f"No research context found for {company_code}"
            
            # Combine the content from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs):
                content = doc.page_content.strip()
                if content:
                    context_parts.append(f"Context {i+1}:\n{content}")
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"Retrieved {len(docs)} context documents for {company_code}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for {company_code}: {e}")
            return f"Error retrieving context for {company_code}: {str(e)}"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "total_documents": collection.count(),
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

# Global instance
research_vectorstore = None

def get_research_vectorstore() -> ResearchVectorStore:
    """Get or create the global research vector store instance"""
    global research_vectorstore
    if research_vectorstore is None:
        research_vectorstore = ResearchVectorStore()
        research_vectorstore.setup_vector_store()
    return research_vectorstore

def initialize_vector_store():
    """Initialize the vector store - call this on startup"""
    logger.info("Initializing research vector store...")
    vectorstore = get_research_vectorstore()
    stats = vectorstore.get_collection_stats()
    logger.info(f"Vector store stats: {stats}")
    return vectorstore
