"""Evidence pipeline: event association, edge status classification, and confidence scoring."""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import math
from app.config import (
    FRESHNESS_WINDOW_DAYS,
    CONFIDENCE_HALF_LIFE_DAYS,
    MAX_CONFIDENCE_UNKNOWN,
    BASE_CONFIDENCE_MULTIPLIER,
)
from app.models import Edge, Event, EdgeStatus, TwinGraph


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 timestamp string into timezone-aware datetime."""
    if not ts_str:
        return None
    try:
        # Handles standard ISO formats including trailing 'Z'
        clean_ts = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_ts)
    except Exception:
        return None


def evaluate_edge_evidence(
    edge: Edge,
    events: List[Event],
    reference_time: Optional[datetime] = None,
) -> Tuple[EdgeStatus, float, Optional[str], List[str]]:
    """
    Decide edge status and confidence by deterministic rules:
    
    1. Confirmed:
       - Has at least one supporting evidence event.
       - Fresh: Most recent event occurred within FRESHNESS_WINDOW_DAYS (default 7 days).
       - No conflicting alert events.
       
    2. Needs Review:
       - Supporting evidence exists, but is stale (> FRESHNESS_WINDOW_DAYS old),
       - OR evidence contains conflicting alerts/revocations,
       - OR incomplete telemetry.
       
    3. Unknown:
       - No supporting evidence either way.

    Confidence formula:
      If unknown: confidence <= MAX_CONFIDENCE_UNKNOWN (0.05)
      If has evidence:
        decay = exp(- age_days / CONFIDENCE_HALF_LIFE_DAYS)
        volume_factor = log2(1 + count)
        confidence = min(1.0, max(0.1, BASE_CONFIDENCE_MULTIPLIER * volume_factor * decay))
    """
    if reference_time is None:
        # Use current UTC or fixed reference if provided
        reference_time = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    edge_key = edge.key
    # Find all events supporting this edge
    supporting_events = [
        ev for ev in events
        if edge_key in ev.supports_edge or ev.id in edge.evidence_ids
    ]

    if not supporting_events:
        return "unknown", MAX_CONFIDENCE_UNKNOWN, None, []

    # Extract timestamps and sort newest first
    event_ids = [ev.id for ev in supporting_events]
    parsed_events: List[Tuple[datetime, Event]] = []
    has_conflicts = False

    for ev in supporting_events:
        dt = parse_timestamp(ev.timestamp)
        if dt:
            parsed_events.append((dt, ev))
        if ev.kind == "alert" or "conflict" in ev.detail.lower() or "revoked" in ev.detail.lower():
            has_conflicts = True

    if not parsed_events:
        # Events without valid timestamps are incomplete
        return "needs_review", 0.20, None, event_ids

    parsed_events.sort(key=lambda x: x[0], reverse=True)
    newest_dt, newest_event = parsed_events[0]
    last_seen_iso = newest_dt.isoformat()

    # Calculate elapsed age in days
    age_seconds = (reference_time - newest_dt).total_seconds()
    age_days = max(0.0, age_seconds / 86400.0)

    # Classification rules
    if has_conflicts:
        status: EdgeStatus = "needs_review"
    elif age_days > FRESHNESS_WINDOW_DAYS:
        status: EdgeStatus = "needs_review"
    else:
        status: EdgeStatus = "confirmed"

    # Confidence calculation
    count = len(parsed_events)
    volume_score = math.log2(1.0 + count)
    decay = math.exp(-age_days / CONFIDENCE_HALF_LIFE_DAYS)
    raw_confidence = BASE_CONFIDENCE_MULTIPLIER * volume_score * decay

    if status == "needs_review":
        confidence = min(0.65, max(0.15, raw_confidence))
    else:
        confidence = min(0.99, max(0.50, raw_confidence))

    return status, round(confidence, 2), last_seen_iso, event_ids


def process_all_evidence(
    twin: TwinGraph,
    events: List[Event],
    reference_time: Optional[datetime] = None,
) -> TwinGraph:
    """Process all edges in twin graph through the evidence evaluation pipeline."""
    updated_edges: List[Edge] = []
    for edge in twin.edges:
        status, conf, last_seen, ev_ids = evaluate_edge_evidence(edge, events, reference_time)
        updated_edge = Edge(
            src=edge.src,
            dst=edge.dst,
            kind=edge.kind,
            status=status,
            confidence=conf,
            last_seen=last_seen or edge.last_seen,
            evidence_ids=list(set(edge.evidence_ids + ev_ids)),
            business_weight=edge.business_weight,
        )
        updated_edges.append(updated_edge)

    return TwinGraph(nodes=twin.nodes, edges=updated_edges)

