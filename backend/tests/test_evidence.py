"""Unit tests for evidence pipeline, edge status classification, and confidence scoring."""
import pytest
from datetime import datetime, timezone
from app.models import Edge, Event, TwinGraph
from app.evidence import evaluate_edge_evidence, process_all_evidence


def test_edge_without_evidence_is_unknown():
    edge = Edge(src="n1", dst="n2", kind="access", business_weight=2)
    events = []
    status, conf, last_seen, ev_ids = evaluate_edge_evidence(edge, events)

    assert status == "unknown"
    assert conf <= 0.05
    assert last_seen is None
    assert ev_ids == []


def test_edge_with_fresh_evidence_is_confirmed():
    edge = Edge(src="web-01", dst="app-01", kind="access", business_weight=3)
    ref_time = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    # Event from 1 day ago (fresh, within 7 days window)
    events = [
        Event(
            id="ev-1",
            timestamp="2026-10-30T12:00:00Z",
            asset_id="web-01",
            kind="connection",
            detail="Valid mTLS connection",
            supports_edge=["web-01->app-01"],
        )
    ]

    status, conf, last_seen, ev_ids = evaluate_edge_evidence(edge, events, ref_time)

    assert status == "confirmed"
    assert conf >= 0.50
    assert "2026-10-30" in last_seen
    assert ev_ids == ["ev-1"]


def test_edge_with_stale_evidence_is_needs_review():
    edge = Edge(src="web-01", dst="jump-01", kind="trust", business_weight=2)
    ref_time = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    # Event from 20 days ago (> 7 days window)
    events = [
        Event(
            id="ev-stale",
            timestamp="2026-10-11T12:00:00Z",
            asset_id="jump-01",
            kind="login",
            detail="Legacy SSH login",
            supports_edge=["web-01->jump-01"],
        )
    ]

    status, conf, last_seen, ev_ids = evaluate_edge_evidence(edge, events, ref_time)

    assert status == "needs_review"
    assert conf < 0.65
    assert ev_ids == ["ev-stale"]


def test_edge_with_conflict_is_needs_review():
    edge = Edge(src="user-01", dst="db-01", kind="access", business_weight=4)
    ref_time = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        Event(
            id="ev-alert",
            timestamp="2026-10-31T08:00:00Z",
            asset_id="db-01",
            kind="alert",
            detail="Revoked credential conflict alert",
            supports_edge=["user-01->db-01"],
        )
    ]

    status, conf, last_seen, ev_ids = evaluate_edge_evidence(edge, events, ref_time)

    assert status == "needs_review"

