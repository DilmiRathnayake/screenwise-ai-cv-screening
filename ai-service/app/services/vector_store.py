"""Vector store: Pinecone when configured, otherwise local NPZ cosine index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.backend = "local"
        self._index = None
        self._ids: List[str] = []
        self._vectors: Optional[np.ndarray] = None
        self._metadatas: List[Dict[str, Any]] = []
        self._texts: List[str] = []
        self._init_backend()

    def _init_backend(self) -> None:
        key = (self.settings.pinecone_api_key or "").strip()
        if key:
            try:
                from pinecone import Pinecone, ServerlessSpec

                pc = Pinecone(api_key=key)
                name = self.settings.pinecone_index_name
                existing = {i["name"] for i in pc.list_indexes()}
                if name not in existing:
                    pc.create_index(
                        name=name,
                        dimension=384,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud=self.settings.pinecone_cloud,
                            region=self.settings.pinecone_region,
                        ),
                    )
                    logger.info("Created Pinecone index %s", name)
                self._index = pc.Index(name)
                self.backend = "pinecone"
                logger.info("Using Pinecone vector backend")
                return
            except Exception as exc:
                logger.warning("Pinecone unavailable (%s) — using local store", exc)

        self.backend = "local"
        self._load_local()
        logger.info("Using local NPZ vector backend at %s", self.settings.local_vector_path)

    def _load_local(self) -> None:
        path = Path(self.settings.local_vector_path)
        meta_path = path.with_suffix(".json")
        if path.exists() and meta_path.exists():
            data = np.load(path, allow_pickle=False)
            self._vectors = data["vectors"]
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            self._ids = payload.get("ids", [])
            self._metadatas = payload.get("metadatas", [])
            self._texts = payload.get("texts", [])
        else:
            self._vectors = None
            self._ids, self._metadatas, self._texts = [], [], []

    def _save_local(self) -> None:
        path = Path(self.settings.local_vector_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._vectors is None or not len(self._ids):
            return
        np.savez_compressed(path, vectors=self._vectors.astype(np.float32))
        path.with_suffix(".json").write_text(
            json.dumps(
                {
                    "ids": self._ids,
                    "metadatas": self._metadatas,
                    "texts": self._texts,
                }
            ),
            encoding="utf-8",
        )

    def upsert(
        self,
        ids: List[str],
        vectors: np.ndarray,
        metadatas: List[Dict[str, Any]],
        texts: List[str],
    ) -> int:
        if self.backend == "pinecone" and self._index is not None:
            items = []
            for i, vid in enumerate(ids):
                meta = dict(metadatas[i] or {})
                meta["_text"] = (texts[i] or "")[:2000]
                items.append(
                    {
                        "id": vid,
                        "values": vectors[i].tolist(),
                        "metadata": meta,
                    }
                )
            # Pinecone upsert in batches
            batch = 100
            for start in range(0, len(items), batch):
                self._index.upsert(vectors=items[start : start + batch])
            return len(items)

        # Local upsert / replace by id
        id_to_idx = {vid: i for i, vid in enumerate(self._ids)}
        for i, vid in enumerate(ids):
            vec = vectors[i].astype(np.float32)
            meta = metadatas[i] or {}
            text = texts[i] or ""
            if vid in id_to_idx:
                idx = id_to_idx[vid]
                self._vectors[idx] = vec
                self._metadatas[idx] = meta
                self._texts[idx] = text
            else:
                if self._vectors is None:
                    self._vectors = vec.reshape(1, -1)
                else:
                    self._vectors = np.vstack([self._vectors, vec.reshape(1, -1)])
                self._ids.append(vid)
                self._metadatas.append(meta)
                self._texts.append(text)
                id_to_idx[vid] = len(self._ids) - 1
        self._save_local()
        return len(ids)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.backend == "pinecone" and self._index is not None:
            kwargs: Dict[str, Any] = {
                "vector": query_vector.tolist(),
                "top_k": top_k,
                "include_metadata": True,
            }
            if metadata_filter:
                kwargs["filter"] = metadata_filter
            res = self._index.query(**kwargs)
            hits = []
            for m in res.get("matches") or []:
                meta = dict(m.get("metadata") or {})
                preview = meta.pop("_text", None)
                hits.append(
                    {
                        "id": m.get("id"),
                        "score": float(m.get("score") or 0),
                        "metadata": meta,
                        "text_preview": preview,
                    }
                )
            return hits

        if self._vectors is None or not len(self._ids):
            return []

        q = query_vector.astype(np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)
        mat = self._vectors / (
            np.linalg.norm(self._vectors, axis=1, keepdims=True) + 1e-9
        )
        scores = mat @ q
        order = np.argsort(-scores)

        hits = []
        for idx in order:
            meta = self._metadatas[idx] or {}
            if metadata_filter:
                ok = all(str(meta.get(k)) == str(v) for k, v in metadata_filter.items())
                if not ok:
                    continue
            hits.append(
                {
                    "id": self._ids[idx],
                    "score": float(scores[idx]),
                    "metadata": meta,
                    "text_preview": (self._texts[idx] or "")[:400],
                }
            )
            if len(hits) >= top_k:
                break
        return hits

    def delete(self, ids: List[str]) -> int:
        if self.backend == "pinecone" and self._index is not None:
            self._index.delete(ids=ids)
            return len(ids)

        if not self._ids:
            return 0
        keep = [i for i, vid in enumerate(self._ids) if vid not in set(ids)]
        removed = len(self._ids) - len(keep)
        if removed == 0:
            return 0
        self._ids = [self._ids[i] for i in keep]
        self._metadatas = [self._metadatas[i] for i in keep]
        self._texts = [self._texts[i] for i in keep]
        self._vectors = self._vectors[keep] if keep else None
        self._save_local()
        return removed
