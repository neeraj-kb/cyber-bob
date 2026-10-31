"""SQLite database storage layer for twin state, incidents, events, and runs."""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import DB_PATH, DATA_DIR
from app.models import Node, Edge, Event, Incident, TwinGraph, SimulationRun, VerificationResult


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables for digital twin, events, incidents, and runs."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS twin_nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                type TEXT NOT NULL,
                criticality INTEGER NOT NULL,
                is_entry BOOLEAN NOT NULL,
                is_critical BOOLEAN NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS twin_edges (
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                last_seen TEXT,
                evidence_ids TEXT NOT NULL,
                business_weight INTEGER NOT NULL,
                PRIMARY KEY (src, dst)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT NOT NULL,
                supports_edge TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                compromised_nodes TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                run_data TEXT NOT NULL,
                approved_defense_id TEXT,
                approver_note TEXT,
                verification_data TEXT
            )
        """)
        conn.commit()


def save_twin(twin: TwinGraph) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM twin_nodes")
        cursor.execute("DELETE FROM twin_edges")
        for n in twin.nodes:
            cursor.execute(
                "INSERT INTO twin_nodes (id, label, type, criticality, is_entry, is_critical) VALUES (?, ?, ?, ?, ?, ?)",
                (n.id, n.label, n.type, n.criticality, 1 if n.is_entry else 0, 1 if n.is_critical else 0),
            )
        for e in twin.edges:
            cursor.execute(
                "INSERT INTO twin_edges (src, dst, kind, status, confidence, last_seen, evidence_ids, business_weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (e.src, e.dst, e.kind, e.status, e.confidence, e.last_seen, json.dumps(e.evidence_ids), e.business_weight),
            )
        conn.commit()


def get_twin() -> TwinGraph:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, label, type, criticality, is_entry, is_critical FROM twin_nodes")
        nodes = [
            Node(
                id=row["id"],
                label=row["label"],
                type=row["type"],
                criticality=row["criticality"],
                is_entry=bool(row["is_entry"]),
                is_critical=bool(row["is_critical"]),
            )
            for row in cursor.fetchall()
        ]
        cursor.execute("SELECT src, dst, kind, status, confidence, last_seen, evidence_ids, business_weight FROM twin_edges")
        edges = [
            Edge(
                src=row["src"],
                dst=row["dst"],
                kind=row["kind"],
                status=row["status"],
                confidence=row["confidence"],
                last_seen=row["last_seen"],
                evidence_ids=json.loads(row["evidence_ids"]),
                business_weight=row["business_weight"],
            )
            for row in cursor.fetchall()
        ]
        return TwinGraph(nodes=nodes, edges=edges)


def save_node(node: Node) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO twin_nodes (id, label, type, criticality, is_entry, is_critical)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                label=excluded.label,
                type=excluded.type,
                criticality=excluded.criticality,
                is_entry=excluded.is_entry,
                is_critical=excluded.is_critical
            """,
            (node.id, node.label, node.type, node.criticality, 1 if node.is_entry else 0, 1 if node.is_critical else 0),
        )
        conn.commit()


def delete_node(node_id: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM twin_nodes WHERE id = ?", (node_id,))
        cursor.execute("DELETE FROM twin_edges WHERE src = ? OR dst = ?", (node_id, node_id))
        conn.commit()


def save_edge(edge: Edge) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO twin_edges (src, dst, kind, status, confidence, last_seen, evidence_ids, business_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(src, dst) DO UPDATE SET
                kind=excluded.kind,
                status=excluded.status,
                confidence=excluded.confidence,
                last_seen=excluded.last_seen,
                evidence_ids=excluded.evidence_ids,
                business_weight=excluded.business_weight
            """,
            (edge.src, edge.dst, edge.kind, edge.status, edge.confidence, edge.last_seen, json.dumps(edge.evidence_ids), edge.business_weight),
        )
        conn.commit()


def delete_edge(src: str, dst: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM twin_edges WHERE src = ? AND dst = ?", (src, dst))
        conn.commit()


def get_events() -> List[Event]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, asset_id, kind, detail, supports_edge FROM events")
        return [
            Event(
                id=row["id"],
                timestamp=row["timestamp"],
                asset_id=row["asset_id"],
                kind=row["kind"],
                detail=row["detail"],
                supports_edge=json.loads(row["supports_edge"]),
            )
            for row in cursor.fetchall()
        ]


def get_incidents() -> List[Incident]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, compromised_nodes FROM incidents")
        return [
            Incident(
                id=row["id"],
                title=row["title"],
                compromised_nodes=json.loads(row["compromised_nodes"]),
            )
            for row in cursor.fetchall()
        ]


def get_incident(incident_id: str) -> Optional[Incident]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, compromised_nodes FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Incident(
            id=row["id"],
            title=row["title"],
            compromised_nodes=json.loads(row["compromised_nodes"]),
        )


def save_run(run: SimulationRun) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runs (run_id, incident_id, timestamp, run_data, approved_defense_id, approver_note, verification_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                approved_defense_id=excluded.approved_defense_id,
                approver_note=excluded.approver_note,
                verification_data=excluded.verification_data
            """,
            (
                run.run_id,
                run.incident_id,
                run.timestamp,
                run.model_dump_json(),
                run.approved_defense_id,
                run.approver_note,
                None,
            ),
        )
        conn.commit()


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT run_id, incident_id, timestamp, run_data, approved_defense_id, approver_note, verification_data FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if not row:
            return None
        run_dict = json.loads(row["run_data"])
        run_dict["approved_defense_id"] = row["approved_defense_id"]
        run_dict["approver_note"] = row["approver_note"]
        if row["verification_data"]:
            run_dict["verification_result"] = json.loads(row["verification_data"])
        return run_dict


def save_approval(run_id: str, defense_id: str, approver_note: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET approved_defense_id = ?, approver_note = ? WHERE run_id = ?",
            (defense_id, approver_note, run_id),
        )
        conn.commit()


def save_verification(run_id: str, verification: VerificationResult) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET verification_data = ? WHERE run_id = ?",
            (verification.model_dump_json(), run_id),
        )
        conn.commit()


def load_seed_data(org_path: Optional[Path] = None, events_path: Optional[Path] = None, force: bool = False) -> None:
    """Populate database from seed JSON files if empty or forced."""
    init_db()
    twin = get_twin()
    if len(twin.nodes) > 0 and not force:
        return

    org_file = org_path or (DATA_DIR / "seed_org.json")
    events_file = events_path or (DATA_DIR / "seed_events.json")

    if org_file.exists():
        with open(org_file, "r", encoding="utf-8") as f:
            org_data = json.load(f)

        nodes = [Node(**n) for n in org_data.get("nodes", [])]
        edges = [Edge(**e) for e in org_data.get("edges", [])]
        save_twin(TwinGraph(nodes=nodes, edges=edges))

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidents")
            for inc in org_data.get("incidents", []):
                cursor.execute(
                    "INSERT INTO incidents (id, title, compromised_nodes) VALUES (?, ?, ?)",
                    (inc["id"], inc["title"], json.dumps(inc["compromised_nodes"])),
                )
            conn.commit()

    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            events_data = json.load(f)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events")
            for ev in events_data:
                cursor.execute(
                    "INSERT INTO events (id, timestamp, asset_id, kind, detail, supports_edge) VALUES (?, ?, ?, ?, ?, ?)",
                    (ev["id"], ev["timestamp"], ev["asset_id"], ev["kind"], ev["detail"], json.dumps(ev.get("supports_edge", []))),
                )
            conn.commit()

