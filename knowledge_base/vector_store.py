"""
向量存储 —— 基于 ChromaDB
存储豆瓣Top100书籍特征 + AI自身写作经验
"""
import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Optional
from config import config

# 确保 HuggingFace 镜像在导入 sentence_transformers 之前已设置
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


class VectorStore:
    """统一的向量存储接口，管理两个Collection：
    - top100_books: 豆瓣Top100书籍文风特征
    - writing_experience: AI自己的写作经验
    """

    def __init__(self, persist_path: Optional[str] = None):
        path = persist_path or config.vector_db_path
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False),
        )
        # 使用 sentence-transformers 嵌入函数（走 HuggingFace 链路，享受镜像加速）
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
        )
        self._init_collections()

    def _init_collections(self):
        self.books_collection = self.client.get_or_create_collection(
            name="top100_books",
            metadata={"description": "豆瓣Top100书籍文风特征库"},
            embedding_function=self.embedding_fn,
        )
        self.experience_collection = self.client.get_or_create_collection(
            name="writing_experience",
            metadata={"description": "AI写作经验积累库"},
            embedding_function=self.embedding_fn,
        )

    # ========== 书籍特征操作 ==========

    def add_book_features(self, book_id: str, features: dict, embedding_text: str):
        """添加一本书的文风特征到向量库"""
        self.books_collection.add(
            ids=[book_id],
            documents=[embedding_text],
            metadatas=[features],
        )

    def search_similar_books(self, query: str, k: Optional[int] = None) -> list[dict]:
        """检索最相似的Top100书籍特征"""
        k = k or config.top100_retrieval_k
        results = self.books_collection.query(query_texts=[query], n_results=k)
        if not results["ids"][0]:
            return []
        return [
            {
                "id": results["ids"][0][i],
                "metadata": results["metadatas"][0][i],
                "document": results["documents"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]

    # ========== 写作经验操作 ==========

    def add_experience(self, exp_id: str, experience: dict, embedding_text: str):
        """添加一条写作经验"""
        self.experience_collection.add(
            ids=[exp_id],
            documents=[embedding_text],
            metadatas=[experience],
        )

    def search_experiences(self, query: str, k: Optional[int] = None) -> list[dict]:
        """检索最相关的写作经验"""
        k = k or config.experience_retrieval_k
        results = self.experience_collection.query(query_texts=[query], n_results=k)
        if not results["ids"][0]:
            return []
        return [
            {
                "id": results["ids"][0][i],
                "metadata": results["metadatas"][0][i],
                "document": results["documents"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]

    def get_experience_stats(self) -> dict:
        """获取经验库统计信息"""
        count = self.experience_collection.count()
        return {"total_experiences": count}

    def clear_all(self):
        """清空所有数据（慎用）"""
        self.client.delete_collection("top100_books")
        self.client.delete_collection("writing_experience")
        self._init_collections()


# 全局实例
store = VectorStore()
