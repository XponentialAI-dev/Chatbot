# Just Run it once!

import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

#Extract Data From the PDF File
def load_pdf_file(data):
    loader= DirectoryLoader(
        data,
        glob="*.pdf",
        loader_cls=PyPDFLoader
        )

    documents=loader.load()
    return documents

#Split the Data into Text Chunks
def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks

#Download the Embeddings from HuggingFace 
def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='thenlper/gte-large') 
    return embeddings

extracted_data=load_pdf_file(data='data/')

text_chunks=text_split(extracted_data)

embeddings = download_hugging_face_embeddings()

index_name = "xponential-bot"

# Embed each chunk and upsert the embeddings into your Pinecone index.
vectorstore = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings, 
)