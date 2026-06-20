"""
rag_pipeline.py
---------------
Retrieval-Augmented Generation (RAG) Pipeline

This module handles the complete document lifecycle:
  1. Document Ingestion  : Load .txt, .md, and .pdf files from /data
  2. Chunking            : Split documents into manageable pieces using RecursiveCharacterTextSplitter
  3. Embedding           : Convert text chunks to dense vectors using Gemini text-embedding-004
  4. Indexing            : Store embeddings in a persistent ChromaDB collection
  5. Retrieval           : Semantic similarity search at query time (cosine similarity)
"""

import os
import glob
from typing import Optional
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import chromadb

from src.config import (
    GEMINI_API_KEY, EMBED_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    CHROMA_DB_DIR, COLLECTION_NAME, DATA_DIR
)


class LocalRAGPipeline:
    """
    End-to-end RAG pipeline backed by ChromaDB (persistent local vector store)
    and Google Gemini embeddings.

    Usage:
        pipeline = LocalRAGPipeline()
        pipeline.ingest_all_documents()
        chunks = pipeline.retrieve_context("How do I reset my password?")
    """

    def __init__(self, db_dir: str = CHROMA_DB_DIR):
        """Initialize the Gemini client and persistent ChromaDB collection."""
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=db_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            # ChromaDB uses cosine similarity by default with 'cosine' space
            metadata={"hnsw:space": "cosine"}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            # Natural separators in priority order:
            # paragraphs → sentences → words → characters
            separators=["\n\n", "\n", " ", ""]
        )

    # ── Embedding ─────────────────────────────────────────────────────────────

    def get_embedding(self, text: str) -> list[float]:
        """
        Convert a text string to a dense vector embedding using Gemini.

        The text-embedding-004 model produces 768-dimensional vectors that
        capture semantic meaning — similar texts produce geometrically close vectors.
        """
        response = self.gemini_client.models.embed_content(
            model=EMBED_MODEL,
            contents=text
        )
        return response.embeddings[0].values

    # ── Document Parsing ──────────────────────────────────────────────────────

    def _parse_txt_or_md(self, file_path: str) -> str:
        """Read plain text or Markdown files using standard Python I/O."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF using pypdf.

        PDFs store text with complex geometric layout information.
        pypdf extracts the raw text content page-by-page.
        """
        reader = PdfReader(file_path)
        pages_text = []
        for page_num, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted and extracted.strip():
                # Tag each page's content with its page number for metadata
                pages_text.append(f"[Page {page_num + 1}]\n{extracted}")
        return "\n\n".join(pages_text)

    def parse_document(self, file_path: str) -> Optional[str]:
        """
        Dispatch to the correct parser based on file extension.

        Returns:
            Extracted text as a string, or None if unsupported format.
        """
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in (".txt", ".md"):
                return self._parse_txt_or_md(file_path)
            elif ext == ".pdf":
                return self._parse_pdf(file_path)
            else:
                print(f"⚠️  Unsupported file type: {ext} ({file_path})")
                return None
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return None

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest_document(self, file_path: str, doc_name: Optional[str] = None) -> int:
        """
        Ingest a single document into the vector database.

        Process:
          1. Parse the raw text from the file
          2. Split into overlapping chunks using RecursiveCharacterTextSplitter
          3. Generate a Gemini embedding vector for each chunk
          4. Upsert (add or update) into ChromaDB with metadata

        Args:
            file_path : Absolute or relative path to the document
            doc_name  : Optional override for the source label in metadata

        Returns:
            Number of chunks ingested
        """
        if doc_name is None:
            doc_name = os.path.basename(file_path)

        raw_text = self.parse_document(file_path)
        if not raw_text:
            return 0

        # Split into chunks
        chunks = self.text_splitter.split_text(raw_text)
        if not chunks:
            print(f"⚠️  No chunks produced from: {doc_name}")
            return 0

        print(f"  📄 {doc_name}: {len(chunks)} chunks", end=" → embedding")

        ingested_count = 0
        for idx, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk)
            chunk_id = f"{doc_name}_chunk_{idx}"

            self.collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{
                    "source": doc_name,
                    "chunk_index": idx,
                    "file_path": file_path
                }],
                documents=[chunk]
            )
            ingested_count += 1

        print(f" ✅ {ingested_count} vectors stored")
        return ingested_count

    def ingest_all_documents(self, data_dir: str = DATA_DIR) -> int:
        """
        Discover and ingest all supported documents from the data directory.

        Scans for .txt, .md, and .pdf files recursively.

        Returns:
            Total number of chunks ingested across all documents
        """
        supported_exts = ("*.txt", "*.md", "*.pdf")
        all_files = []
        for ext in supported_exts:
            all_files.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))

        if not all_files:
            print(f"⚠️  No documents found in {data_dir}")
            return 0

        print(f"\n🗂️  Found {len(all_files)} documents to ingest:\n")
        total_chunks = 0
        for file_path in sorted(all_files):
            total_chunks += self.ingest_document(file_path)

        print(f"\n✅ Total: {total_chunks} chunks indexed in ChromaDB\n")
        return total_chunks

    def get_collection_stats(self) -> dict:
        """Return basic statistics about the current collection."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "db_directory": CHROMA_DB_DIR
        }

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve_context(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """
        Perform semantic similarity search for a user query.

        Process:
          1. Embed the query using text-embedding-004
          2. Calculate cosine similarity against all indexed chunk vectors
          3. Return the top-k closest chunks with their confidence scores

        The confidence score is derived from the ChromaDB distance metric:
            confidence = 1.0 - cosine_distance
        (ChromaDB with cosine space returns distances in range [0, 2])

        Args:
            query  : The user's support question
            top_k  : Number of most relevant chunks to return

        Returns:
            List of dicts with keys: text, source, chunk_index, score
        """
        if self.collection.count() == 0:
            return []

        query_vector = self.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, self.collection.count())
        )

        retrieved_items = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results.get("distances", [[]])[0]

            for i in range(len(docs)):
                # Convert cosine distance to a 0-1 confidence score
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                raw_distance = distances[i] if distances else 0.0
                confidence = max(0.0, 1.0 - raw_distance)

                retrieved_items.append({
                    "text": docs[i],
                    "source": metas[i].get("source", "unknown"),
                    "chunk_index": metas[i].get("chunk_index", 0),
                    "score": round(confidence, 4)
                })

        # Sort by score descending (highest confidence first)
        retrieved_items.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_items


# ── Quick test when running directly ─────────────────────────────────────────
if __name__ == "__main__":
    pipeline = LocalRAGPipeline()
    stats = pipeline.get_collection_stats()

    if stats["total_chunks"] == 0:
        print("Database empty — ingesting documents...")
        pipeline.ingest_all_documents()
    else:
        print(f"✅ Collection already has {stats['total_chunks']} chunks. Skipping ingestion.")

    # Test retrieval
    test_queries = [
        "How do I reset my password?",
        "API 401 unauthorized error fix",
        "Refund policy for duplicate charges"
    ]
    for q in test_queries:
        print(f"\n🔍 Query: {q}")
        chunks = pipeline.retrieve_context(q, top_k=2)
        for c in chunks:
            print(f"  [{c['score']:.3f}] {c['source']} — {c['text'][:80]}...")
