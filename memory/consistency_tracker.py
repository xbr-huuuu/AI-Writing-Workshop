"""
一致性追踪器（v2 新增）
伏笔埋设/回收追踪 + 角色性格快照 + 回收率统计 + 检查清单生成
"""
import json
import os


class ConsistencyTracker:
    """追踪全书伏笔与角色一致性，防止前后脱节"""

    def __init__(self, novel_dir: str = ""):
        self.foreshadowings: list[dict] = []
        self.character_snapshots: dict[str, dict] = {}
        self._file = os.path.join(novel_dir, "consistency.json") if novel_dir else ""

    def load(self):
        if self._file and os.path.exists(self._file):
            with open(self._file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.foreshadowings = data.get("foreshadowings", [])
                self.character_snapshots = data.get("character_snapshots", {})

    def save(self):
        if self._file:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump({
                    "foreshadowings": self.foreshadowings,
                    "character_snapshots": self.character_snapshots,
                }, f, ensure_ascii=False, indent=2)

    # ========== 伏笔 ==========

    def plant(self, chapter: int, description: str, expected_chapter: int = None):
        self.foreshadowings.append({
            "id": len(self.foreshadowings) + 1,
            "planted": chapter,
            "description": description,
            "expected_payoff": expected_chapter,
            "status": "open",
            "resolved_at": None,
            "resolution": "",
        })
        self.save()

    def resolve(self, fid: int, chapter: int, how: str):
        for f in self.foreshadowings:
            if f["id"] == fid and f["status"] == "open":
                f["status"] = "resolved"
                f["resolved_at"] = chapter
                f["resolution"] = how
                self.save()
                return

    def open_list(self) -> list[dict]:
        return [f for f in self.foreshadowings if f["status"] == "open"]

    def stats(self) -> dict:
        total = len(self.foreshadowings)
        resolved = sum(1 for f in self.foreshadowings if f["status"] == "resolved")
        return {"total": total, "resolved": resolved, "open": total - resolved,
                "rate": f"{resolved}/{total}" if total > 0 else "0/0"}

    # ========== 角色快照 ==========

    def snapshot_character(self, name: str, traits: dict):
        self.character_snapshots[name] = traits

    # ========== 检查清单 ==========

    def checklist(self) -> str:
        parts = []
        opens = self.open_list()
        if opens:
            parts.append("【伏笔回收清单】")
            for f in opens:
                parts.append(f"  ☐ 伏笔#{f['id']}（第{f['planted']}章）：{f['description']}")
        if self.character_snapshots:
            parts.append("\n【角色性格约束】")
            for name, t in self.character_snapshots.items():
                parts.append(f"  • {name}：{t}")
        return "\n".join(parts) if parts else "（暂无一致性约束）"
