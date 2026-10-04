"""Lightweight in-process metrics for the recommendation engine.

Counters are per worker process and reset on restart; they complement the
durable per-request records in ``RecommendationHistory``. This is intentionally
minimal – a Prometheus exporter would be the next step at real scale.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RecommendationMetrics:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requests: int = 0
    total_latency_ms: float = 0.0
    total_candidates: int = 0
    total_results: int = 0
    budget_relaxations: int = 0
    empty_results: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, *, latency_ms: float, candidates: int, results: int, relaxed: bool) -> None:
        with self._lock:
            self.requests += 1
            self.total_latency_ms += latency_ms
            self.total_candidates += candidates
            self.total_results += results
            self.budget_relaxations += int(relaxed)
            self.empty_results += int(results == 0)

    def snapshot(self) -> dict:
        with self._lock:
            requests = self.requests
            return {
                "since": self.started_at.isoformat(),
                "requests": requests,
                "average_latency_ms": round(self.total_latency_ms / requests, 2) if requests else None,
                "average_candidates": round(self.total_candidates / requests, 2) if requests else None,
                "average_results": round(self.total_results / requests, 2) if requests else None,
                "budget_relaxation_rate": round(self.budget_relaxations / requests, 4) if requests else None,
                "empty_result_rate": round(self.empty_results / requests, 4) if requests else None,
            }

    def reset(self) -> None:
        with self._lock:
            self.started_at = datetime.now(timezone.utc)
            self.requests = 0
            self.total_latency_ms = 0.0
            self.total_candidates = 0
            self.total_results = 0
            self.budget_relaxations = 0
            self.empty_results = 0


recommendation_metrics = RecommendationMetrics()
