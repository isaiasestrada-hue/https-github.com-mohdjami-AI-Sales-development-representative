"""
SQLite database layer for the Securiti.ai BDR System.
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime, date
from models import Prospect, Activity, Meeting


DB_PATH = "securiti_bdr.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                title TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                linkedin_url TEXT,
                phone TEXT,
                company TEXT NOT NULL,
                industry TEXT NOT NULL,
                employees INTEGER,
                revenue_usd INTEGER,
                website TEXT,
                hq_location TEXT,
                persona_type TEXT,
                status TEXT DEFAULT 'new',
                icp_score INTEGER,
                icp_tier TEXT,
                company_summary TEXT,
                pain_points_identified TEXT,
                trigger_events TEXT,
                tech_stack TEXT,
                notes TEXT,
                sequence_day INTEGER DEFAULT 0,
                last_touch_date TEXT,
                next_touch_date TEXT,
                next_touch_type TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                outcome TEXT,
                sequence_touch INTEGER,
                channel TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (prospect_id) REFERENCES prospects(id)
            );

            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER NOT NULL,
                prospect_name TEXT NOT NULL,
                company TEXT NOT NULL,
                persona_type TEXT,
                scheduled_date TEXT,
                held_date TEXT,
                meeting_type TEXT DEFAULT 'discovery',
                status TEXT DEFAULT 'scheduled',
                outcome TEXT,
                next_steps TEXT,
                opportunity_created INTEGER DEFAULT 0,
                deal_value_usd INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (prospect_id) REFERENCES prospects(id)
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  PROSPECT OPERATIONS
# ─────────────────────────────────────────────

def create_prospect(p: Prospect) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO prospects (
                first_name, last_name, full_name, title, email, linkedin_url, phone,
                company, industry, employees, revenue_usd, website, hq_location,
                persona_type, status, icp_score, icp_tier,
                company_summary, pain_points_identified, trigger_events, tech_stack,
                notes, sequence_day, last_touch_date, next_touch_date, next_touch_type,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            p.first_name, p.last_name, p.full_name, p.title, p.email,
            p.linkedin_url, p.phone, p.company, p.industry, p.employees,
            p.revenue_usd, p.website, p.hq_location, p.persona_type,
            p.status, p.icp_score, p.icp_tier,
            p.company_summary, p.pain_points_identified, p.trigger_events,
            p.tech_stack, p.notes, p.sequence_day,
            p.last_touch_date, p.next_touch_date, p.next_touch_type,
            p.created_at, p.updated_at,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_prospect(prospect_id: int) -> Optional[Prospect]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
        return Prospect(**dict(row)) if row else None
    finally:
        conn.close()


def get_prospect_by_email(email: str) -> Optional[Prospect]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM prospects WHERE email = ?", (email,)).fetchone()
        return Prospect(**dict(row)) if row else None
    finally:
        conn.close()


def list_prospects(status: Optional[str] = None, tier: Optional[str] = None,
                   limit: int = 100, offset: int = 0) -> List[Prospect]:
    conn = get_connection()
    try:
        query = "SELECT * FROM prospects WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if tier:
            query += " AND icp_tier = ?"
            params.append(tier)
        query += " ORDER BY icp_score DESC, created_at DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = conn.execute(query, params).fetchall()
        return [Prospect(**dict(r)) for r in rows]
    finally:
        conn.close()


def update_prospect(prospect_id: int, **fields) -> bool:
    if not fields:
        return False
    fields["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [prospect_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE prospects SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def count_prospects(status: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        if status:
            row = conn.execute("SELECT COUNT(*) FROM prospects WHERE status = ?", (status,)).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM prospects").fetchone()
        return row[0]
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  ACTIVITY OPERATIONS
# ─────────────────────────────────────────────

def log_activity(a: Activity) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO activities
                (prospect_id, activity_type, subject, body, outcome, sequence_touch, channel, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            a.prospect_id, a.activity_type, a.subject, a.body,
            a.outcome, a.sequence_touch, a.channel, a.created_at,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_activities_for_prospect(prospect_id: int) -> List[Activity]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM activities WHERE prospect_id = ? ORDER BY created_at DESC",
            (prospect_id,)
        ).fetchall()
        return [Activity(**dict(r)) for r in rows]
    finally:
        conn.close()


def count_activities_this_month(activity_type: Optional[str] = None) -> int:
    month_start = date.today().replace(day=1).isoformat()
    conn = get_connection()
    try:
        if activity_type:
            row = conn.execute(
                "SELECT COUNT(*) FROM activities WHERE activity_type = ? AND created_at >= ?",
                (activity_type, month_start)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM activities WHERE created_at >= ?",
                (month_start,)
            ).fetchone()
        return row[0]
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  MEETING OPERATIONS
# ─────────────────────────────────────────────

def create_meeting(m: Meeting) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO meetings (
                prospect_id, prospect_name, company, persona_type,
                scheduled_date, held_date, meeting_type, status,
                outcome, next_steps, opportunity_created, deal_value_usd,
                notes, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            m.prospect_id, m.prospect_name, m.company, m.persona_type,
            m.scheduled_date, m.held_date, m.meeting_type, m.status,
            m.outcome, m.next_steps, int(m.opportunity_created), m.deal_value_usd,
            m.notes, m.created_at, m.updated_at,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_meeting(meeting_id: int) -> Optional[Meeting]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return Meeting(**dict(row)) if row else None
    finally:
        conn.close()


def list_meetings(status: Optional[str] = None, month: Optional[str] = None) -> List[Meeting]:
    conn = get_connection()
    try:
        query = "SELECT * FROM meetings WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if month:
            query += " AND (scheduled_date LIKE ? OR held_date LIKE ?)"
            params += [f"{month}%", f"{month}%"]
        query += " ORDER BY scheduled_date DESC"
        rows = conn.execute(query, params).fetchall()
        return [Meeting(**dict(r)) for r in rows]
    finally:
        conn.close()


def update_meeting(meeting_id: int, **fields) -> bool:
    if not fields:
        return False
    fields["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [meeting_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE meetings SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def count_meetings_this_month(status: Optional[str] = None) -> int:
    month_start = date.today().replace(day=1).isoformat()
    conn = get_connection()
    try:
        if status:
            row = conn.execute(
                "SELECT COUNT(*) FROM meetings WHERE status = ? AND created_at >= ?",
                (status, month_start)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM meetings WHERE created_at >= ?",
                (month_start,)
            ).fetchone()
        return row[0]
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  ANALYTICS QUERIES
# ─────────────────────────────────────────────

def get_pipeline_funnel() -> dict:
    conn = get_connection()
    try:
        statuses = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM prospects GROUP BY status"
        ).fetchall()
        funnel = {row["status"]: row["cnt"] for row in statuses}

        monthly_meetings = conn.execute("""
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as cnt
            FROM meetings
            WHERE status IN ('scheduled','held')
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """).fetchall()
        funnel["meetings_by_month"] = [dict(r) for r in monthly_meetings]

        activity_summary = conn.execute("""
            SELECT activity_type, COUNT(*) as cnt
            FROM activities
            WHERE created_at >= date('now', 'start of month')
            GROUP BY activity_type
        """).fetchall()
        funnel["activities_this_month"] = {r["activity_type"]: r["cnt"] for r in activity_summary}

        return funnel
    finally:
        conn.close()


def get_sequence_due_prospects() -> List[Prospect]:
    """Return prospects due for their next outreach touch."""
    today = date.today().isoformat()
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM prospects
            WHERE status IN ('qualified', 'in_sequence')
            AND next_touch_date <= ?
            ORDER BY icp_score DESC, next_touch_date ASC
        """, (today,)).fetchall()
        return [Prospect(**dict(r)) for r in rows]
    finally:
        conn.close()
