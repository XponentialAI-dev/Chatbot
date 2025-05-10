import os
import json
from dotenv import load_dotenv
from google.adk.agents import Agent
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict, Any
from pydantic import BaseModel

load_dotenv()

class PineconeRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name='thenlper/gte-large')
        self.index_name = "xponential-bot"
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        print(f"Initialized Pinecone with index: {self.index_name}")  # Debug
    
    def retrieve_docs(self, query: str, top_k: int = 3, score_threshold: float = 0.4) -> List[Dict[str, Any]]:
        """Retrieve documents from Pinecone"""
        try:
            print(f"Querying Pinecone for: '{query}'")  # Debug
            
            # Get raw results first
            docs = self.vectorstore.similarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Then filter by score
            filtered_docs = [doc for doc in docs if doc[1] >= score_threshold]
            print(f"Found {len(filtered_docs)} matching documents")  # Debug
            
            return [{
                "content": doc[0].page_content,
                "metadata": doc[0].metadata,
                "score": float(doc[1])
            } for doc in filtered_docs]
    
        except Exception as e:
            print(f"Retrieval error: {str(e)}")
            return []

# Create the retriever tool
pinecone_retriever = PineconeRetriever()

def pinecone_retrieval_tool(query: str) -> str:
    """Tool for retrieving documentation from Pinecone vectorstore"""
    print(f"\n=== Retrieval Tool Triggered for: '{query}' ===")  # Debug
    results = pinecone_retriever.retrieve_docs(query)
    
    if not results:
        print("No documents found matching the query")  # Debug
        return json.dumps({
            "status": "no_results",
            "query": query,
            "message": "No relevant documents found"
        })
    
    print(f"Found {len(results)} relevant documents")  # Debug
    return json.dumps({
        "status": "success",
        "query": query,
        "results": results
    })

rag_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='ask_rag_agent',

    instruction="""Always use the retrieval tool to find relevant information before answering. 
    Follow these steps:
    1. First search for relevant documents using the retrieval tool
    2. Analyze the found documents
    3. Provide a comprehensive answer based on the documents
    4. If no documents are found, say "I couldn't find information about [query] in my knowledge base"
    """,
    
    tools=[pinecone_retrieval_tool]
)