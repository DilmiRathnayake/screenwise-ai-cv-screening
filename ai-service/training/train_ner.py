"""
Train spaCy NER model for resume information extraction.

Usage (from ai-service/):
  python -m training.preprocess_it_datasets
  python -m training.train_ner --epochs 30 --weak-rows 0
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger, setup_logging
from training.data_loader import IT_NER_LABELS, load_it_ner_splits

setup_logging()
logger = get_logger(__name__)


def _load_baseline_metrics(metrics_path: Path) -> dict | None:
    if not metrics_path.exists():
        return None
    try:
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        return {
            "precision": data.get("precision"),
            "recall": data.get("recall"),
            "f1": data.get("f1"),
            "accuracy": data.get("accuracy"),
            "dataset": data.get("dataset", "legacy"),
        }
    except Exception:
        return None


def _to_examples(nlp, data: list):
    from spacy.training import Example

    examples = []
    for text, ann in data:
        try:
            doc = nlp.make_doc(text)
            examples.append(Example.from_dict(doc, ann))
        except Exception as exc:
            logger.debug("Skipping bad example: %s", exc)
    return examples


def train_ner(
    epochs: int = 30,
    weak_rows: int = 0,
    dropout: float = 0.2,
    seed: int = 42,
    patience: int = 5,
) -> dict:
    import spacy
    from spacy.util import compounding, minibatch

    settings = get_settings()
    train_path = settings.it_ner_train_path
    val_path = settings.it_ner_val_path
    test_path = settings.it_ner_test_path

    for p in (train_path, val_path, test_path):
        if not p.exists():
            raise FileNotFoundError(
                f"IT NER dataset not found: {p}. Run: python -m training.preprocess_it_datasets"
            )

    train_data, val_data, test_data = load_it_ner_splits(train_path, val_path, test_path)
    logger.info(
        "IT NER splits — train: %s | val: %s | test: %s",
        len(train_data),
        len(val_data),
        len(test_data),
    )

    nlp = spacy.blank("en")
    ner = nlp.add_pipe("ner")
    labels = list(IT_NER_LABELS)
    for label in labels:
        ner.add_label(label)

    train_examples = _to_examples(nlp, train_data)
    val_examples = _to_examples(nlp, val_data)
    if len(train_examples) < 5:
        raise RuntimeError(f"Too few valid training examples: {len(train_examples)}")

    metrics_path = settings.ner_model_path.parent / "metrics.json"
    baseline = _load_baseline_metrics(metrics_path)

    other_pipes = [p for p in nlp.pipe_names if p != "ner"]
    best_val_f1 = -1.0
    best_epoch = 0
    stale_epochs = 0
    best_nlp = None

    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.initialize(get_examples=lambda: train_examples)

        for epoch in range(epochs):
            random.seed(seed + epoch)
            random.shuffle(train_examples)
            losses: dict = {}
            batches = minibatch(train_examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                try:
                    nlp.update(batch, drop=dropout, losses=losses, sgd=optimizer)
                except ValueError as exc:
                    logger.debug("Skipping batch due to: %s", exc)
                    continue

            val_metrics = evaluate_ner(nlp, val_data)
            val_f1 = val_metrics["f1"]
            logger.info(
                "Epoch %s/%s — loss: %s | val F1: %s",
                epoch + 1,
                epochs,
                round(float(losses.get("ner", 0.0)), 4),
                val_f1,
            )

            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch + 1
                stale_epochs = 0
                best_nlp = nlp.to_bytes()
            else:
                stale_epochs += 1
                if stale_epochs >= patience:
                    logger.info("Early stopping at epoch %s (best val F1=%s)", epoch + 1, best_val_f1)
                    break

    if best_nlp is not None:
        nlp.from_bytes(best_nlp)

    test_metrics = evaluate_ner(nlp, test_data)
    val_metrics = evaluate_ner(nlp, val_data)

    out_dir = settings.ner_model_path
    out_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(out_dir)

    payload = {
        "model_path": str(out_dir),
        "dataset": "ScreenWise_IT_NER",
        "eval_split": "test",
        "train_size": len(train_data),
        "val_size": len(val_data),
        "test_size": len(test_data),
        "epochs": epochs,
        "best_epoch": best_epoch,
        "weak_rows": weak_rows,
        "labels": labels,
        "baseline_metrics": baseline,
        "val_metrics": val_metrics,
        **test_metrics,
    }
    metrics_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Saved NER model to %s", out_dir)
    logger.info("Test metrics: %s", json.dumps(test_metrics, indent=2))
    return payload


def evaluate_ner(nlp, test_data: list) -> dict:
    """Entity-level precision / recall / F1 / accuracy."""
    tp = fp = fn = 0
    per_label = {}

    for text, ann in test_data:
        gold = {(s, e, l) for s, e, l in ann.get("entities", [])}
        doc = nlp(text)
        pred = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}

        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)

        labels = {l for _, _, l in gold | pred}
        for label in labels:
            g = {x for x in gold if x[2] == label}
            p = {x for x in pred if x[2] == label}
            stats = per_label.setdefault(label, {"tp": 0, "fp": 0, "fn": 0})
            stats["tp"] += len(g & p)
            stats["fp"] += len(p - g)
            stats["fn"] += len(g - p)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0

    label_metrics = {}
    for label, s in per_label.items():
        p = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 0.0
        r = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 0.0
        f = (2 * p * r / (p + r)) if (p + r) else 0.0
        label_metrics[label] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
            "support": s["tp"] + s["fn"],
        }

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "per_label": label_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Train IT resume NER model")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--weak-rows", type=int, default=0)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience", type=int, default=5)
    args = parser.parse_args()
    train_ner(
        epochs=args.epochs,
        weak_rows=args.weak_rows,
        dropout=args.dropout,
        seed=args.seed,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
