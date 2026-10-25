import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCUMENTS_DIR = "data/documents"
VECTOR_STORE_DIR = "data/vector_store"

# Free, local embedding model - no API key needed, runs on CPU.
# all-MiniLM-L6-v2 is small (~80MB) and fast, a solid default for a
# project like this where we're not embedding millions of documents.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_documents() -> list:
    """Load every PDF in the documents directory into LangChain Document objects."""
    documents = []
    for filename in os.listdir(DOCUMENTS_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            # Tag each chunk with its source filename so retrieval results
            # can tell us (and the LLM) which policy a chunk came from.
            for doc in docs:
                doc.metadata["source"] = filename
            documents.extend(docs)
            print(f"Loaded {filename}: {len(docs)} page(s)")
    return documents


def split_documents(documents: list) -> list:
    """
    Break documents into smaller overlapping chunks.

    chunk_size=500: roughly a paragraph - small enough that a retrieved
    chunk is focused on one topic, not padded with unrelated policy text.
    chunk_overlap=50: chunks share a little text at their boundaries, so
    we don't accidentally split a sentence's key fact right at a chunk
    edge and lose it from both sides.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def build_vector_store(chunks: list) -> Chroma:
    """
    Embed each chunk and store it in a persistent Chroma vector database
    on disk, so we don't need to re-embed documents every time the app
    starts.
    """
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_DIR,
    )
    print(f"Vector store built and saved to {VECTOR_STORE_DIR}")
    return vector_store


if __name__ == "__main__":
    docs = load_documents()
    if not docs:
        print(f"No PDFs found in {DOCUMENTS_DIR}. Add policy PDFs and re-run.")
    else:
        chunks = split_documents(docs)
        build_vector_store(chunks)