"""Background model retraining scheduler.

Periodically re-trains the collaborative model embeddings using the latest
in-memory ratings, then hot-swaps each model's embeddings into the store.
Cooc and SBERT rows already refresh instantly (no retrain needed); this loop
covers every other model row.

Architecture:
  - Runs in a background thread (non-blocking)
  - Interval configurable (default: 1 hour)
  - Uses the store's current user_ratings to build training data
  - Trains each model in turn; one failure does not stop the others
  - Hot-swaps embeddings on the live store
"""

from __future__ import annotations

import logging
import threading
import time

import pandas as pd

logger = logging.getLogger(__name__)

_retrain_thread: threading.Thread | None = None
_stop_event = threading.Event()

MIN_INTERACTIONS = 100
POSITIVE_THRESHOLD = 4.0


def start_retrain_scheduler(interval_seconds: int = 3600) -> None:
    """Start the background retrain loop."""
    global _retrain_thread
    if _retrain_thread and _retrain_thread.is_alive():
        logger.warning("Retrain scheduler already running")
        return

    _stop_event.clear()
    _retrain_thread = threading.Thread(
        target=_retrain_loop, args=(interval_seconds,), daemon=True,
    )
    _retrain_thread.start()
    logger.info("Retrain scheduler started (interval=%ds)", interval_seconds)


def stop_retrain_scheduler() -> None:
    """Stop the background retrain loop."""
    _stop_event.set()
    logger.info("Retrain scheduler stopped")


def _retrain_loop(interval: int) -> None:
    while not _stop_event.is_set():
        if _stop_event.wait(timeout=interval):
            break
        try:
            _run_retrain()
        except Exception:
            logger.exception("Retrain failed")


# ── Training-data builders ──────────────────────────────────────────────────

def _build_sd_train_df(store) -> pd.DataFrame:
    """Game-only positives for SDR models (LightGCN, MF-BPR, NeuMF)."""
    rows = []
    for ext_id, ratings in store.user_ratings.items():
        if ext_id not in store.sd_user_to_idx:
            continue
        for r in ratings:
            if r.get("domain") != "game" or r["rating"] < POSITIVE_THRESHOLD:
                continue
            if r["item_id"] in store.sd_item_to_idx:
                rows.append({"user_id": ext_id, "item_id": r["item_id"],
                             "rating": r["rating"]})
    return pd.DataFrame(rows)


def _build_cd_train_df(store) -> pd.DataFrame:
    """Both-domain positives for CDR models (CMF, EMCDR, PTUPCDR)."""
    rows = []
    for ext_id, ratings in store.user_ratings.items():
        if ext_id not in store.cd_user_to_idx:
            continue
        for r in ratings:
            if r["rating"] < POSITIVE_THRESHOLD or r.get("domain") not in ("movie", "game"):
                continue
            if r["item_id"] in store.cd_item_to_idx:
                rows.append({"user_id": ext_id, "item_id": r["item_id"],
                             "rating": r["rating"], "domain": r["domain"]})
    return pd.DataFrame(rows)


def _sd_dims(store) -> tuple[int, int]:
    n_users = max(store.sd_user_to_idx.values(), default=-1) + 1
    n_items = max(store.sd_item_to_idx.values(), default=-1) + 1
    return n_users, n_items


def _cd_dims(store) -> tuple[int, int]:
    n_users = max(store.cd_user_to_idx.values(), default=-1) + 1
    n_items = max(store.cd_item_to_idx.values(), default=-1) + 1
    return n_users, n_items


# ── Per-model retrainers ────────────────────────────────────────────────────

def _retrain_lightgcn(store, train_df: pd.DataFrame) -> None:
    from ml.models.lightgcn import LightGCN
    n_users, n_items = _sd_dims(store)
    model = LightGCN(n_users, n_items, embedding_dim=96, num_layers=3,
                     device="cpu", dropout=0.1)
    model.fit(train_df, store.sd_user_to_idx, store.sd_item_to_idx,
              epochs=20, lr=0.001, reg_lambda=0.001, batch_size=4096,
              positive_threshold=POSITIVE_THRESHOLD)
    store.lgcn_user = model.get_user_embeddings()
    store.lgcn_item = model.get_item_embeddings()


def _retrain_mf_bpr(store, train_df: pd.DataFrame) -> None:
    from ml.models.matrix_factorization_bpr import MatrixFactorizationBPR
    n_users, n_items = _sd_dims(store)
    model = MatrixFactorizationBPR(n_users, n_items, embedding_dim=96)
    model.fit(train_df, store.sd_user_to_idx, store.sd_item_to_idx,
              epochs=30, lr=0.01, reg_lambda=0.01, batch_size=4096,
              positive_threshold=POSITIVE_THRESHOLD)
    store.mf_bpr_user = model.get_user_embeddings()
    store.mf_bpr_item = model.get_item_embeddings()


def _retrain_neumf(store, train_df: pd.DataFrame) -> None:
    from ml.models.ncf import NCF
    n_users, n_items = _sd_dims(store)
    model = NCF(n_users, n_items, embedding_dim=64, device="cpu")
    model.fit(train_df, store.sd_user_to_idx, store.sd_item_to_idx,
              epochs=10, lr=0.001, reg_lambda=0.001, batch_size=4096,
              positive_threshold=POSITIVE_THRESHOLD)
    store.neumf_user = model.get_user_embeddings()
    store.neumf_item = model.get_item_embeddings()


def _retrain_cmf(store, train_df: pd.DataFrame) -> None:
    from ml.models.cmf import CMF
    n_users, n_items = _cd_dims(store)
    model = CMF(n_users, n_items, embedding_dim=64, device="cpu")
    model.fit(train_df, store.cd_user_to_idx, store.cd_item_to_idx,
              epochs=30, lr=0.0005, batch_size=8192,
              positive_threshold=POSITIVE_THRESHOLD)
    store.cmf_user = model.get_user_embeddings()
    store.cmf_item = model.get_item_embeddings()


def _retrain_emcdr(store, train_df: pd.DataFrame) -> None:
    from ml.models.emcdr import EMCDRWrapper
    n_users, n_items = _cd_dims(store)
    model = EMCDRWrapper(n_users, n_items, embedding_dim=64, device="cpu")
    model.fit(train_df, store.cd_user_to_idx, store.cd_item_to_idx,
              epochs=10, lr=0.001, reg_lambda=1e-4, batch_size=4096,
              positive_threshold=POSITIVE_THRESHOLD)
    store.emcdr_user = model.get_user_embeddings()
    store.emcdr_item = model.get_item_embeddings()


def _retrain_ptupcdr(store, train_df: pd.DataFrame) -> None:
    from ml.models.ptupcdr import PTUPCDRWrapper
    n_users, n_items = _cd_dims(store)
    model = PTUPCDRWrapper(n_users, n_items, embedding_dim=64, device="cpu")
    model.fit(train_df, store.cd_user_to_idx, store.cd_item_to_idx,
              epochs=10, lr=0.001, reg_lambda=1e-4, batch_size=4096,
              positive_threshold=POSITIVE_THRESHOLD,
              meta_epochs=10, meta_lr=0.001, n_experts=8)
    store.ptupcdr_user = model.get_user_embeddings()
    store.ptupcdr_item = model.get_item_embeddings()


_SD_MODELS = [
    ("LightGCN", _retrain_lightgcn),
    ("MF-BPR", _retrain_mf_bpr),
    ("NeuMF", _retrain_neumf),
]
_CD_MODELS = [
    ("CMF", _retrain_cmf),
    ("EMCDR", _retrain_emcdr),
    ("PTUPCDR", _retrain_ptupcdr),
]


def _run_retrain() -> None:
    """Run one retrain cycle across all collaborative models."""
    from backend.demo.store import DemoStore

    store = DemoStore.get()
    if not store.loaded:
        return

    logger.info("=== Starting scheduled retrain ===")
    cycle_t0 = time.time()

    sd_df = _build_sd_train_df(store)
    cd_df = _build_cd_train_df(store)
    logger.info("Retrain training pool: SD=%d positives, CD=%d positives",
                len(sd_df), len(cd_df))

    if len(sd_df) >= MIN_INTERACTIONS:
        for name, fn in _SD_MODELS:
            try:
                t0 = time.time()
                fn(store, sd_df)
                logger.info("  %s retrained in %.1fs", name, time.time() - t0)
            except Exception:
                logger.exception("  %s retrain failed", name)
    else:
        logger.info("Too few SD positives (%d < %d), skipping SDR models",
                    len(sd_df), MIN_INTERACTIONS)

    if len(cd_df) >= MIN_INTERACTIONS:
        for name, fn in _CD_MODELS:
            try:
                t0 = time.time()
                fn(store, cd_df)
                logger.info("  %s retrained in %.1fs", name, time.time() - t0)
            except Exception:
                logger.exception("  %s retrain failed", name)
    else:
        logger.info("Too few CD positives (%d < %d), skipping CDR models",
                    len(cd_df), MIN_INTERACTIONS)

    logger.info("=== Retrain complete in %.1fs ===", time.time() - cycle_t0)
