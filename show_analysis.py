"""查看豆瓣Top100书籍分析报告"""
from knowledge_base.vector_store import store
import sys

title = sys.argv[1] if len(sys.argv) > 1 else None

if title:
    # 查单本
    book_id = f"book_{title.replace(' ', '_')}"
    r = store.books_collection.get(ids=[book_id], include=["metadatas"])
    if r["ids"]:
        m = r["metadatas"][0]
        print(f"\n{'='*50}")
        print(f"《{m['title']}》 — {m['author']} | {m['genre']} | 豆瓣{m['douban_score']}分")
        print(f"{'='*50}\n")
        print(m["style_analysis"])
    else:
        print(f"未找到《{title}》")
else:
    # 列出所有
    r = store.books_collection.get(include=["metadatas"])
    print(f"\n共 {len(r['ids'])} 本已分析：\n")
    for i, m in enumerate(r["metadatas"], 1):
        preview = m["style_analysis"][:120].replace("\n", " ")
        print(f"[{i}] 《{m['title']}》 — {preview}...")
        print()
