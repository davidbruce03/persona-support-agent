

import os
import glob
import json
import pickle
from typing import Optional
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import faiss
import numpy as np

from src.config import (
    GEMINI_API_KEY, EMBED_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS,
    DATA_DIR
)

INDEX_PATH = "./faiss_index/index.faiss"
CHUNKS_PATH = "./faiss_index/chunks.pkl"


class LocalRAGPipeline:
    def __init__(self, db_dir: str = "./faiss_index"):
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.db_dir = db_dir
        os.makedirs(db_dir, exist_ok=True)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        self.index = None
        self.chunks = []  # List of dicts: {text, source, chunk_index}
        self._load_if_exists()

    def _load_if_exists(self):
        """Load existing FAISS index and chunks from disk if available."""
        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)

    def _save(self):
        """Persist FAISS index and chunks to disk."""
        faiss.write_index(self.index, INDEX_PATH)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

    def get_embedding(self, text: str) -> list[float]:
        response = self.gemini_client.models.embed_content(
            model=EMBED_MODEL,
            contents=text
        )
        return response.embeddings[0].values

    def _parse_txt_or_md(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        pages_text = []
        for page_num, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted and extracted.strip():
                pages_text.append(f"[Page {page_num + 1}]\n{extracted}")
        return "\n\n".join(pages_text)

    def parse_document(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in (".txt", ".md"):
                return self._parse_txt_or_md(file_path)
            elif ext == ".pdf":
                return self._parse_pdf(file_path)
            else:
                return None
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def ingest_document(self, file_path: str, doc_name: Optional[str] = None) -> int:
        if doc_name is None:
            doc_name = os.path.basename(file_path)

        raw_text = self.parse_document(file_path)
        if not raw_text:
            return 0

        chunks = self.text_splitter.split_text(raw_text)
        if not chunks:
            return 0

        print(f"  📄 {doc_name}: {len(chunks)} chunks", end=" → embedding")

        embeddings = []
        for idx, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk)
            embeddings.append(embedding)
            self.chunks.append({
                "text": chunk,
                "source": doc_name,
                "chunk_index": idx,
                "file_path": file_path
            })

        # Build or expand FAISS index
        vectors = np.array(embeddings, dtype=np.float32)
        if self.index is None:
            dim = vectors.shape[1]
            self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine on normalized vectors
        
        # Normalize for cosine similarity
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self._save()

        print(f" ✅ {len(chunks)} vectors stored")
        return len(chunks)

    def ingest_all_documents(self, data_dir: str = DATA_DIR) -> int:
        # Reset existing index
        self.index = None
        self.chunks = []

        supported_exts = ("*.txt", "*.md", "*.pdf")
        all_files = []
        for ext in supported_exts:
            all_files.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))

        if not all_files:
            print(f"No documents found in {data_dir}")
            return 0

        print(f"\n🗂️  Found {len(all_files)} documents\n")
        total_chunks = 0
        for file_path in sorted(all_files):
            total_chunks += self.ingest_document(file_path)

        print(f"\n✅ Total: {total_chunks} chunks indexed\n")
        return total_chunks

    def get_collection_stats(self) -> dict:
        return {
            "total_chunks": len(self.chunks),
            "collection_name": "faiss_index",
            "db_directory": self.db_dir
        }

    def retrieve_context(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        if self.index is None or len(self.chunks) == 0:
            return []

        query_vector = np.array(
            [self.get_embedding(query)], dtype=np.float32
        )
        faiss.normalize_L2(query_vector)

        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_vector, k)

        retrieved_items = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            retrieved_items.append({
                "text": chunk["text"],
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "score": round(float(score), 4)
            })

        retrieved_items.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_items