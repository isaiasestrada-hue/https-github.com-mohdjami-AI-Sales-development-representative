"""
Analytics and Dashboard for the Securiti.ai BDR System.
Tracks progress toward 20 qualified meetings per month.
"""

from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn
from rich.columns import Columns
from rich.text import Text
from rich import box

import database as db
from config import CADENCE_CONFIG

console = Console()

MONTHLY_MEETING_TARGET = CADENCE_CONFIG["monthly_meeting_target"]


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0%"
    return f"{numerator / denominator * 100:.1f}%"


def _tier_color(tier: str) -> str:
    return {"A": "green", "B": "yellow", "C": "orange1", "D": "red"}.get(tier, "white")


def _status_color(status: str) -> str:
    mapping = {
        "new": "white",
        "researched": "cyan",
        "qualified": "blue",
        "in_sequence": "magenta",
        "responded": "yellow",
        "meeting_scheduled": "green",
        "meeting_held": "bright_green",
        "opportunity": "bright_green",
        "closed_won": "green bold",
        "closed_lost": "red",
        "unqualified": "dim",
        "do_not_contact": "red dim",
    }
    return mapping.get(status, "white")


# ─────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────

def render_dashboard():
    """Render the full BDR analytics dashboard."""
    console.clear()
    today = date.today()
    month_label = today.strftime("%B %Y")

    console.print()
    console.rule(f"[bold cyan]Securiti.ai BDR Dashboard — {month_label}[/bold cyan]")
    console.print()

    funnel = db.get_pipeline_funnel()
    activities = funnel.get("activities_this_month", {})
    meetings_by_month = funnel.get("meetings_by_month", [])

    # ── Meeting Target Progress ──────────────────
    meetings_held = db.count_meetings_this_month("held")
    meetings_scheduled = db.count_meetings_this_month("scheduled")
    total_meetings = meetings_held + meetings_scheduled

    target_panel = _render_meeting_target(meetings_held, meetings_scheduled)
    console.print(target_panel)
    console.print()

    # ── Pipeline Funnel ──────────────────────────
    console.print(_render_pipeline_funnel(funnel))
    console.print()

    # ── Activity Summary ─────────────────────────
    console.print(_render_activity_summary(activities))
    console.print()

    # ── Meeting History (last 6 months) ──────────
    if meetings_by_month:
        console.print(_render_meeting_history(meetings_by_month))
        console.print()

    # ── Tier Distribution ────────────────────────
    console.print(_render_tier_distribution())
    console.print()

    # ── Upcoming Touches ────────────────────────
    due_prospects = db.get_sequence_due_prospects()
    if due_prospects:
        console.print(_render_due_touches(due_prospects[:10]))
        console.print()

    # ── Conversion Rates ────────────────────────
    console.print(_render_conversion_rates(activities, total_meetings))
    console.print()


def _render_meeting_target(held: int, scheduled: int) -> Panel:
    target = MONTHLY_MEETING_TARGET
    total = held + scheduled
    pct = min(100, int(total / target * 100))

    # Progress bar
    bar_filled = int(pct / 5)  # 20 chars wide
    bar_empty = 20 - bar_filled
    bar = "[" + "█" * bar_filled + "░" * bar_empty + "]"

    color = "red" if pct < 40 else "yellow" if pct < 70 else "green"

    lines = Text()
    lines.append(f"  Monthly Meeting Target:  ", style="white")
    lines.append(f"{total}", style=f"bold {color}")
    lines.append(f" / {target}", style="white")
    lines.append(f"  ({pct}%)\n\n", style=f"{color}")
    lines.append(f"  {bar}", style=color)
    lines.append(f"  {held} held", style="bright_green")
    lines.append(f"  +  {scheduled} scheduled", style="yellow")

    remaining = max(0, target - total)
    if remaining > 0:
        lines.append(f"\n\n  Need {remaining} more meeting{'s' if remaining != 1 else ''} to hit target", style="dim")
    else:
        lines.append(f"\n\n  Target achieved! 🎯", style="bold green")

    return Panel(lines, title="[bold]🎯 Meeting Target[/bold]", border_style=color, padding=(1, 2))


def _render_pipeline_funnel(funnel: dict) -> Table:
    table = Table(
        title="Pipeline Funnel",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Stage", style="white", min_width=20)
    table.add_column("Count", justify="right", style="bold")
    table.add_column("Bar", min_width=30)

    stages = [
        ("new", "New"),
        ("researched", "Researched"),
        ("qualified", "Qualified"),
        ("in_sequence", "In Sequence"),
        ("responded", "Responded"),
        ("meeting_scheduled", "Meeting Scheduled"),
        ("meeting_held", "Meeting Held"),
        ("opportunity", "Opportunity Created"),
        ("closed_won", "Closed Won"),
    ]

    max_count = max((funnel.get(s, 0) for s, _ in stages), default=1)
    max_count = max(max_count, 1)

    for status_key, label in stages:
        count = funnel.get(status_key, 0)
        bar_len = max(1, int(count / max_count * 25))
        bar = "▓" * bar_len
        color = _status_color(status_key)
        table.add_row(label, str(count), f"[{color}]{bar}[/{color}]")

    return table


def _render_activity_summary(activities: dict) -> Table:
    table = Table(
        title="Activity This Month",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Activity", style="white", min_width=25)
    table.add_column("Count", justify="right", style="bold yellow")

    activity_labels = {
        "email_sent": "Emails Sent",
        "email_replied": "Email Replies",
        "linkedin_connection_sent": "LinkedIn Connections Sent",
        "linkedin_connection_accepted": "LinkedIn Connections Accepted",
        "linkedin_message_sent": "LinkedIn Messages Sent",
        "linkedin_message_replied": "LinkedIn Replies",
        "call_attempted": "Calls Attempted",
        "call_connected": "Calls Connected",
        "call_voicemail": "Voicemails Left",
        "meeting_scheduled": "Meetings Scheduled",
        "meeting_held": "Meetings Held",
        "meeting_no_show": "No-Shows",
    }

    for key, label in activity_labels.items():
        count = activities.get(key, 0)
        if count > 0:
            table.add_row(label, str(count))

    if not any(activities.get(k, 0) > 0 for k in activity_labels):
        table.add_row("[dim]No activities logged this month[/dim]", "")

    return table


def _render_meeting_history(meetings_by_month: list) -> Table:
    table = Table(
        title="Meeting History (Last 6 Months)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Month", style="white", min_width=12)
    table.add_column("Meetings", justify="right", style="bold")
    table.add_column("vs Target", justify="right")
    table.add_column("Bar", min_width=20)

    for row in meetings_by_month:
        month = row.get("month", "")
        count = row.get("cnt", 0)
        target = MONTHLY_MEETING_TARGET
        pct = count / target * 100
        color = "green" if count >= target else "yellow" if count >= target * 0.7 else "red"
        bar = "█" * max(1, int(count / max(1, target) * 20))
        vs_target = f"+{count - target}" if count >= target else f"{count - target}"
        table.add_row(
            month,
            str(count),
            f"[{color}]{vs_target}[/{color}]",
            f"[{color}]{bar}[/{color}]",
        )

    return table


def _render_tier_distribution() -> Table:
    conn = __import__("sqlite3").connect("securiti_bdr.db")
    conn.row_factory = __import__("sqlite3").Row
    try:
        rows = conn.execute(
            "SELECT icp_tier, COUNT(*) as cnt FROM prospects WHERE icp_tier IS NOT NULL GROUP BY icp_tier ORDER BY icp_tier"
        ).fetchall()
    finally:
        conn.close()

    table = Table(
        title="Prospect ICP Tier Distribution",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Tier", min_width=8)
    table.add_column("Definition", min_width=20)
    table.add_column("Count", justify="right", style="bold")
    table.add_column("Priority", min_width=15)

    tier_defs = {
        "A": ("Score 80-100", "Work immediately"),
        "B": ("Score 60-79", "Standard cadence"),
        "C": ("Score 40-59", "Nurture"),
        "D": ("Score <40", "Deprioritize"),
    }
    tier_counts = {r["icp_tier"]: r["cnt"] for r in rows}

    for tier in ["A", "B", "C", "D"]:
        defn, priority = tier_defs[tier]
        count = tier_counts.get(tier, 0)
        color = _tier_color(tier)
        table.add_row(
            f"[{color}][bold]{tier}[/bold][/{color}]",
            defn,
            str(count),
            f"[{color}]{priority}[/{color}]",
        )

    return table


def _render_due_touches(prospects) -> Table:
    table = Table(
        title=f"Prospects Due for Outreach ({len(prospects)} shown)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", min_width=4)
    table.add_column("Name", min_width=20)
    table.add_column("Company", min_width=18)
    table.add_column("Title", min_width=15)
    table.add_column("Tier", min_width=6, justify="center")
    table.add_column("Next Touch", min_width=12)
    table.add_column("Channel", min_width=10)

    for p in prospects:
        tier_color = _tier_color(p.icp_tier or "D")
        table.add_row(
            str(p.id),
            p.full_name,
            p.company[:18],
            p.title[:15],
            f"[{tier_color}]{p.icp_tier or '?'}[/{tier_color}]",
            p.next_touch_date or "Today",
            p.next_touch_type or "email",
        )

    return table


def _render_conversion_rates(activities: dict, total_meetings: int) -> Panel:
    emails_sent = activities.get("email_sent", 0)
    email_replies = activities.get("email_replied", 0)
    calls = activities.get("call_attempted", 0)
    calls_connected = activities.get("call_connected", 0)
    li_sent = activities.get("linkedin_message_sent", 0)
    li_replied = activities.get("linkedin_message_replied", 0)

    total_touches = emails_sent + calls + li_sent
    total_responses = email_replies + calls_connected + li_replied

    lines = []
    lines.append(f"  Email reply rate:      {_pct(email_replies, emails_sent)}  ({email_replies}/{emails_sent})")
    lines.append(f"  Call connect rate:     {_pct(calls_connected, calls)}  ({calls_connected}/{calls})")
    lines.append(f"  LinkedIn reply rate:   {_pct(li_replied, li_sent)}  ({li_replied}/{li_sent})")
    lines.append(f"  Overall response rate: {_pct(total_responses, total_touches)}")
    lines.append(f"  Meeting conversion:    {_pct(total_meetings, total_touches)}")
    lines.append("")
    lines.append("  Benchmarks: reply 5-10% | connect 15-25% | meeting 1-3%")

    return Panel(
        "\n".join(lines),
        title="[bold]Conversion Rates[/bold]",
        border_style="cyan",
        padding=(0, 1),
    )


# ─────────────────────────────────────────────
#  PROSPECT TABLE
# ─────────────────────────────────────────────

def render_prospect_table(prospects, title: str = "Prospects"):
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("ID", style="dim", min_width=4, justify="right")
    table.add_column("Name", min_width=22)
    table.add_column("Title", min_width=20)
    table.add_column("Company", min_width=18)
    table.add_column("Industry", min_width=15)
    table.add_column("Tier", min_width=5, justify="center")
    table.add_column("Score", min_width=6, justify="right")
    table.add_column("Status", min_width=16)
    table.add_column("Next Touch", min_width=11)

    for p in prospects:
        tier_color = _tier_color(p.icp_tier or "D")
        status_color = _status_color(p.status)
        table.add_row(
            str(p.id or ""),
            p.full_name[:22],
            p.title[:20],
            p.company[:18],
            p.industry[:15],
            f"[{tier_color}]{p.icp_tier or '?'}[/{tier_color}]",
            str(p.icp_score or ""),
            f"[{status_color}]{p.status}[/{status_color}]",
            p.next_touch_date or "",
        )

    console.print(table)


# ─────────────────────────────────────────────
#  MEETING TABLE
# ─────────────────────────────────────────────

def render_meeting_table(meetings, title: str = "Meetings"):
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", justify="right", min_width=4)
    table.add_column("Prospect", min_width=20)
    table.add_column("Company", min_width=18)
    table.add_column("Persona", min_width=8)
    table.add_column("Type", min_width=10)
    table.add_column("Status", min_width=12)
    table.add_column("Scheduled", min_width=12)
    table.add_column("Outcome", min_width=20)

    for m in meetings:
        status_color = {
            "scheduled": "yellow",
            "held": "bright_green",
            "no_show": "red",
            "cancelled": "dim red",
        }.get(m.status, "white")
        table.add_row(
            str(m.id or ""),
            m.prospect_name[:20],
            m.company[:18],
            m.persona_type or "",
            m.meeting_type,
            f"[{status_color}]{m.status}[/{status_color}]",
            m.scheduled_date or "",
            (m.outcome or "")[:20],
        )

    console.print(table)
