#!/usr/bin/env python3
"""
Securiti.ai Outbound Strategic BDR System
Target: 20 qualified meetings/month with ICP personas

Usage:
  python main.py dashboard
  python main.py add-prospect --company "Acme Corp" --first-name Jane --last-name Doe \
        --title "Chief Privacy Officer" --email jane@acme.com --industry "Financial Services"
  python main.py run-pipeline 1
  python main.py generate-touch 1 --channel email --touch 1
  python main.py book-meeting 1 --date 2024-02-15
  python main.py log-activity 1 --type email_sent
  python main.py list-prospects
  python main.py list-meetings
  python main.py show-prospect 1
"""

import os
import sys
import json
from datetime import date, datetime, timedelta
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich import box
from dotenv import load_dotenv

load_dotenv()

import database as db
from models import Prospect, Activity, Meeting
from analytics import (
    render_dashboard, render_prospect_table, render_meeting_table, console
)
from config import CADENCE_CONFIG, PERSONAS, ICP_SCORING
from sequences import SequenceScheduler

db.init_db()


# ─────────────────────────────────────────────
#  CLI GROUP
# ─────────────────────────────────────────────

@click.group()
def cli():
    """Securiti.ai BDR System — 20 meetings/month with ICP personas."""
    pass


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

@cli.command()
def dashboard():
    """Show the BDR analytics dashboard."""
    render_dashboard()


# ─────────────────────────────────────────────
#  ADD PROSPECT
# ─────────────────────────────────────────────

@cli.command("add-prospect")
@click.option("--first-name", required=True, help="Contact first name")
@click.option("--last-name", required=True, help="Contact last name")
@click.option("--title", required=True, help="Job title (e.g. 'Chief Privacy Officer')")
@click.option("--email", required=True, help="Contact email")
@click.option("--company", required=True, help="Company name")
@click.option("--industry", required=True,
              help="Industry (e.g. 'Financial Services', 'Healthcare')")
@click.option("--employees", type=int, help="Number of employees")
@click.option("--revenue", type=int, help="Annual revenue in USD")
@click.option("--linkedin", help="LinkedIn profile URL")
@click.option("--phone", help="Direct phone number")
@click.option("--website", help="Company website")
@click.option("--location", help="HQ location (e.g. 'New York, USA')")
@click.option("--notes", help="Any additional notes")
@click.option("--auto-qualify", is_flag=True, default=False,
              help="Automatically run qualification after adding")
def add_prospect(first_name, last_name, title, email, company, industry,
                 employees, revenue, linkedin, phone, website, location, notes,
                 auto_qualify):
    """Add a new prospect to the pipeline."""
    # Detect persona type from title
    persona_type = _detect_persona(title)

    p = Prospect(
        first_name=first_name,
        last_name=last_name,
        title=title,
        email=email,
        company=company,
        industry=industry,
        employees=employees,
        revenue_usd=revenue,
        linkedin_url=linkedin,
        phone=phone,
        website=website,
        hq_location=location,
        persona_type=persona_type,
        notes=notes,
        status="new",
    )

    try:
        prospect_id = db.create_prospect(p)
        console.print(f"\n[green]Prospect added:[/green] ID {prospect_id} — {p.full_name} @ {p.company}")
        console.print(f"  Persona detected: [cyan]{persona_type}[/cyan]")
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            console.print(f"[yellow]Prospect with email {email} already exists.[/yellow]")
            return
        raise

    if auto_qualify:
        _run_qualification(prospect_id)


# ─────────────────────────────────────────────
#  RUN FULL PIPELINE (research + qualify + generate all messages)
# ─────────────────────────────────────────────

@cli.command("run-pipeline")
@click.argument("prospect_id", type=int)
@click.option("--save-messages", is_flag=True, default=False,
              help="Save generated messages to a JSON file")
def run_pipeline(prospect_id, save_messages):
    """Run the full AI pipeline for a prospect (research + qualify + generate all outreach)."""
    p = db.get_prospect(prospect_id)
    if not p:
        console.print(f"[red]Prospect {prospect_id} not found.[/red]")
        return

    console.print(f"\n[bold cyan]Running BDR pipeline for:[/bold cyan] {p.full_name} @ {p.company}")
    console.print()

    from bdr_agents import BDROrchestrator
    orchestrator = BDROrchestrator()

    try:
        result = orchestrator.run_full_pipeline(p)
    except EnvironmentError as e:
        console.print(f"[red]{e}[/red]")
        return

    research = result["research"]
    qualification = result["qualification"]
    messages = result["messages"]

    # Update prospect in DB
    scheduler = SequenceScheduler()
    next_date, next_channel, next_touch = scheduler.get_next_touch(date.today(), 0)

    db.update_prospect(
        prospect_id,
        status="qualified" if qualification.tier in ("A", "B") else "unqualified",
        icp_score=qualification.total_score,
        icp_tier=qualification.tier,
        persona_type=qualification.recommended_persona,
        company_summary=research.business_summary,
        pain_points_identified=", ".join(qualification.top_pain_points),
        trigger_events=", ".join(research.recent_trigger_events),
        tech_stack=", ".join(research.tech_stack_signals),
        next_touch_date=next_date.isoformat() if next_date else None,
        next_touch_type=next_channel,
        sequence_day=0,
    )

    # Display results
    _display_pipeline_results(p, research, qualification, messages)

    if save_messages:
        filename = f"outreach_{prospect_id}_{p.company.replace(' ', '_')}.json"
        _save_messages_to_file(filename, p, research, qualification, messages)
        console.print(f"\n[green]Messages saved to {filename}[/green]")


# ─────────────────────────────────────────────
#  GENERATE SINGLE TOUCH
# ─────────────────────────────────────────────

@cli.command("generate-touch")
@click.argument("prospect_id", type=int)
@click.option("--channel", required=True,
              type=click.Choice(["email", "linkedin", "phone"]), help="Outreach channel")
@click.option("--touch", "touch_number", required=True, type=int,
              help="Touch number in sequence (1-5 for email, 1-3 for linkedin/phone)")
def generate_touch(prospect_id, channel, touch_number):
    """Generate a single AI-personalized outreach message for a prospect."""
    p = db.get_prospect(prospect_id)
    if not p:
        console.print(f"[red]Prospect {prospect_id} not found.[/red]")
        return

    console.print(f"\n[cyan]Generating {channel} touch {touch_number} for {p.full_name} @ {p.company}...[/cyan]")

    from bdr_agents import BDROrchestrator
    orchestrator = BDROrchestrator()

    try:
        msg = orchestrator.run_single_touch(p, channel, touch_number)
    except EnvironmentError as e:
        console.print(f"[red]{e}[/red]")
        return

    _display_message(msg, p)


# ─────────────────────────────────────────────
#  LOG ACTIVITY
# ─────────────────────────────────────────────

@cli.command("log-activity")
@click.argument("prospect_id", type=int)
@click.option("--type", "activity_type", required=True,
              type=click.Choice(CADENCE_CONFIG["activity_types"]),
              help="Activity type")
@click.option("--subject", help="Email subject or call topic")
@click.option("--outcome", help="Outcome or notes")
@click.option("--channel", type=click.Choice(["email", "linkedin", "phone"]))
@click.option("--touch", "sequence_touch", type=int, help="Sequence touch number")
def log_activity(prospect_id, activity_type, subject, outcome, channel, sequence_touch):
    """Log an outreach activity for a prospect."""
    p = db.get_prospect(prospect_id)
    if not p:
        console.print(f"[red]Prospect {prospect_id} not found.[/red]")
        return

    a = Activity(
        prospect_id=prospect_id,
        activity_type=activity_type,
        subject=subject,
        outcome=outcome,
        channel=channel,
        sequence_touch=sequence_touch,
    )
    activity_id = db.log_activity(a)

    # Auto-update prospect status based on activity
    status_transitions = {
        "email_replied": "responded",
        "linkedin_message_replied": "responded",
        "call_connected": "responded",
        "meeting_scheduled": "meeting_scheduled",
        "meeting_held": "meeting_held",
    }
    new_status = status_transitions.get(activity_type)
    if new_status:
        db.update_prospect(prospect_id, status=new_status)

    console.print(f"[green]Activity logged:[/green] {activity_type} for {p.full_name} @ {p.company}")


# ─────────────────────────────────────────────
#  BOOK MEETING
# ─────────────────────────────────────────────

@cli.command("book-meeting")
@click.argument("prospect_id", type=int)
@click.option("--date", "scheduled_date", required=True,
              help="Scheduled date (YYYY-MM-DD)")
@click.option("--type", "meeting_type", default="discovery",
              type=click.Choice(["discovery", "demo", "technical", "executive"]))
@click.option("--notes", help="Meeting notes or agenda")
def book_meeting(prospect_id, scheduled_date, meeting_type, notes):
    """Book a meeting for a prospect (updates pipeline toward 20/month target)."""
    p = db.get_prospect(prospect_id)
    if not p:
        console.print(f"[red]Prospect {prospect_id} not found.[/red]")
        return

    m = Meeting(
        prospect_id=prospect_id,
        prospect_name=p.full_name,
        company=p.company,
        persona_type=p.persona_type,
        scheduled_date=scheduled_date,
        meeting_type=meeting_type,
        status="scheduled",
        notes=notes,
    )
    meeting_id = db.create_meeting(m)
    db.update_prospect(prospect_id, status="meeting_scheduled")
    db.log_activity(Activity(
        prospect_id=prospect_id,
        activity_type="meeting_scheduled",
        subject=f"{meeting_type.title()} call scheduled for {scheduled_date}",
        outcome=f"Meeting ID: {meeting_id}",
    ))

    # Show updated progress toward target
    meetings_this_month = db.count_meetings_this_month()
    target = CADENCE_CONFIG["monthly_meeting_target"]
    remaining = max(0, target - meetings_this_month)

    console.print(f"\n[green]Meeting booked![/green] ID {meeting_id} — {p.full_name} @ {p.company}")
    console.print(f"  Date: [cyan]{scheduled_date}[/cyan]  |  Type: {meeting_type}")
    console.print(f"\n  Monthly progress: [bold]{meetings_this_month}/{target}[/bold] meetings", end="")
    if remaining == 0:
        console.print("  [bold green]🎯 Target hit![/bold green]")
    else:
        console.print(f"  ([yellow]{remaining} to go[/yellow])")


# ─────────────────────────────────────────────
#  MARK MEETING HELD
# ─────────────────────────────────────────────

@cli.command("meeting-held")
@click.argument("meeting_id", type=int)
@click.option("--outcome", required=True, help="Meeting outcome summary")
@click.option("--next-steps", help="Agreed next steps")
@click.option("--opportunity", is_flag=True, default=False, help="Did this create an opportunity?")
@click.option("--deal-value", type=int, help="Estimated deal value in USD")
def meeting_held(meeting_id, outcome, next_steps, opportunity, deal_value):
    """Mark a meeting as held and record the outcome."""
    m = db.get_meeting(meeting_id)
    if not m:
        console.print(f"[red]Meeting {meeting_id} not found.[/red]")
        return

    db.update_meeting(
        meeting_id,
        status="held",
        held_date=date.today().isoformat(),
        outcome=outcome,
        next_steps=next_steps,
        opportunity_created=int(opportunity),
        deal_value_usd=deal_value,
    )
    db.update_prospect(m.prospect_id, status="meeting_held" if not opportunity else "opportunity")
    db.log_activity(Activity(
        prospect_id=m.prospect_id,
        activity_type="meeting_held",
        subject=f"Meeting held — {m.meeting_type}",
        outcome=outcome,
    ))

    console.print(f"[green]Meeting {meeting_id} marked as held.[/green]")
    if opportunity:
        console.print(f"  [bold green]Opportunity created![/bold green]", end="")
        if deal_value:
            console.print(f" Estimated value: ${deal_value:,}")
        else:
            console.print()


# ─────────────────────────────────────────────
#  LIST PROSPECTS
# ─────────────────────────────────────────────

@cli.command("list-prospects")
@click.option("--status", help="Filter by status")
@click.option("--tier", type=click.Choice(["A", "B", "C", "D"]), help="Filter by ICP tier")
@click.option("--limit", default=50, help="Max results to show")
def list_prospects(status, tier, limit):
    """List prospects in the pipeline."""
    prospects = db.list_prospects(status=status, tier=tier, limit=limit)
    if not prospects:
        console.print("[yellow]No prospects found.[/yellow]")
        return
    title = "Prospects"
    if status:
        title += f" [{status}]"
    if tier:
        title += f" [Tier {tier}]"
    render_prospect_table(prospects, title=title)
    console.print(f"\n[dim]Showing {len(prospects)} prospects[/dim]")


# ─────────────────────────────────────────────
#  LIST MEETINGS
# ─────────────────────────────────────────────

@cli.command("list-meetings")
@click.option("--status", type=click.Choice(["scheduled", "held", "no_show", "cancelled"]),
              help="Filter by status")
@click.option("--month", help="Filter by month (YYYY-MM)")
def list_meetings(status, month):
    """List meetings in the pipeline."""
    meetings = db.list_meetings(status=status, month=month)
    if not meetings:
        console.print("[yellow]No meetings found.[/yellow]")
        return
    render_meeting_table(meetings, title="Meetings")
    console.print(f"\n[dim]Showing {len(meetings)} meetings[/dim]")


# ─────────────────────────────────────────────
#  SHOW PROSPECT DETAIL
# ─────────────────────────────────────────────

@cli.command("show-prospect")
@click.argument("prospect_id", type=int)
def show_prospect(prospect_id):
    """Show full details for a prospect."""
    p = db.get_prospect(prospect_id)
    if not p:
        console.print(f"[red]Prospect {prospect_id} not found.[/red]")
        return

    activities = db.get_activities_for_prospect(prospect_id)

    from rich.columns import Columns
    from rich.text import Text

    # Contact card
    contact_lines = [
        f"[bold]{p.full_name}[/bold]",
        f"{p.title}",
        f"[cyan]{p.company}[/cyan] · {p.industry}",
        f"",
        f"Email:    {p.email}",
        f"Phone:    {p.phone or '—'}",
        f"LinkedIn: {p.linkedin_url or '—'}",
        f"Location: {p.hq_location or '—'}",
        f"Employees: {p.employees:,}" if p.employees else "Employees: —",
    ]
    contact_panel = Panel(
        "\n".join(contact_lines),
        title="[bold]Contact Info[/bold]",
        border_style="cyan",
        padding=(0, 2),
    )

    # ICP panel
    from analytics import _tier_color, _status_color
    tier_color = _tier_color(p.icp_tier or "D")
    status_color = _status_color(p.status)

    icp_lines = [
        f"Status:      [{status_color}]{p.status}[/{status_color}]",
        f"ICP Score:   [bold]{p.icp_score or '—'}[/bold] / 100",
        f"ICP Tier:    [{tier_color}][bold]{p.icp_tier or '—'}[/bold][/{tier_color}]",
        f"Persona:     {p.persona_type or '—'}",
        f"",
        f"Next Touch:  {p.next_touch_date or '—'}",
        f"Channel:     {p.next_touch_type or '—'}",
        f"Seq. Day:    {p.sequence_day}",
    ]
    icp_panel = Panel(
        "\n".join(icp_lines),
        title="[bold]ICP Qualification[/bold]",
        border_style="yellow",
        padding=(0, 2),
    )

    console.print()
    console.print(Columns([contact_panel, icp_panel]))

    if p.company_summary:
        console.print(Panel(p.company_summary, title="Company Summary", border_style="dim"))

    if p.pain_points_identified:
        console.print(Panel(p.pain_points_identified, title="Pain Points", border_style="dim"))

    if p.trigger_events:
        console.print(Panel(p.trigger_events, title="Trigger Events", border_style="dim"))

    if activities:
        act_table = Table(title="Activity History", box=box.SIMPLE,
                          show_header=True, header_style="bold cyan")
        act_table.add_column("Date", style="dim", min_width=19)
        act_table.add_column("Type", min_width=22)
        act_table.add_column("Subject", min_width=30)
        act_table.add_column("Outcome", min_width=20)
        for a in activities:
            act_table.add_row(
                a.created_at[:19],
                a.activity_type,
                (a.subject or "")[:30],
                (a.outcome or "")[:20],
            )
        console.print(act_table)

    console.print()


# ─────────────────────────────────────────────
#  SHOW DUE TOUCHES
# ─────────────────────────────────────────────

@cli.command("due-today")
def due_today():
    """Show prospects due for outreach today."""
    prospects = db.get_sequence_due_prospects()
    if not prospects:
        console.print("[green]No prospects due for outreach today.[/green]")
        return
    render_prospect_table(prospects, title=f"Due for Outreach — {len(prospects)} prospects")


# ─────────────────────────────────────────────
#  SEED DEMO DATA
# ─────────────────────────────────────────────

@cli.command("seed-demo")
def seed_demo():
    """Seed the database with demo prospects for testing."""
    demo_prospects = [
        {
            "first_name": "Sarah", "last_name": "Chen",
            "title": "Chief Privacy Officer", "email": "schen@jpmorgan-example.com",
            "company": "JPMorgan Chase", "industry": "Financial Services",
            "employees": 280000, "hq_location": "New York, USA",
            "persona_type": "CPO", "icp_score": 94, "icp_tier": "A",
        },
        {
            "first_name": "Marcus", "last_name": "Webb",
            "title": "Chief Information Security Officer", "email": "mwebb@unitedhealth-example.com",
            "company": "UnitedHealth Group", "industry": "Healthcare",
            "employees": 350000, "hq_location": "Minneapolis, USA",
            "persona_type": "CISO", "icp_score": 91, "icp_tier": "A",
        },
        {
            "first_name": "Priya", "last_name": "Nair",
            "title": "VP of Data Governance", "email": "pnair@walmart-example.com",
            "company": "Walmart", "industry": "Retail / eCommerce",
            "employees": 2300000, "hq_location": "Bentonville, USA",
            "persona_type": "CDO", "icp_score": 85, "icp_tier": "A",
        },
        {
            "first_name": "David", "last_name": "Kowalski",
            "title": "Data Protection Officer", "email": "dkowalski@allianz-example.com",
            "company": "Allianz SE", "industry": "Insurance",
            "employees": 150000, "hq_location": "Munich, Germany",
            "persona_type": "DPO", "icp_score": 88, "icp_tier": "A",
        },
        {
            "first_name": "Jennifer", "last_name": "Park",
            "title": "Head of Privacy & Compliance", "email": "jpark@netflix-example.com",
            "company": "Netflix", "industry": "Technology / SaaS",
            "employees": 13000, "hq_location": "Los Gatos, USA",
            "persona_type": "CPO", "icp_score": 79, "icp_tier": "B",
        },
        {
            "first_name": "Ahmed", "last_name": "Al-Rashid",
            "title": "Chief Data Officer", "email": "aalrashid@aramco-example.com",
            "company": "Saudi Aramco", "industry": "Energy & Utilities",
            "employees": 70000, "hq_location": "Dhahran, Saudi Arabia",
            "persona_type": "CDO", "icp_score": 72, "icp_tier": "B",
        },
        {
            "first_name": "Claire", "last_name": "Fontaine",
            "title": "VP Legal & Privacy", "email": "cfontaine@lvmh-example.com",
            "company": "LVMH", "industry": "Retail / eCommerce",
            "employees": 180000, "hq_location": "Paris, France",
            "persona_type": "GC", "icp_score": 76, "icp_tier": "B",
        },
        {
            "first_name": "Tom", "last_name": "Bergstrom",
            "title": "CTO", "email": "tbergstrom@stripe-example.com",
            "company": "Stripe", "industry": "Financial Services",
            "employees": 8000, "hq_location": "San Francisco, USA",
            "persona_type": "VP_ENG", "icp_score": 81, "icp_tier": "A",
        },
    ]

    scheduler = SequenceScheduler()
    added = 0
    for data in demo_prospects:
        next_date, next_channel, _ = scheduler.get_next_touch(date.today(), 0)
        p = Prospect(
            **data,
            status="qualified",
            next_touch_date=next_date.isoformat() if next_date else None,
            next_touch_type=next_channel,
        )
        try:
            pid = db.create_prospect(p)
            console.print(f"  [green]+[/green] {p.full_name} @ {p.company} (Tier {p.icp_tier})")
            added += 1
        except Exception:
            console.print(f"  [dim]Skip {p.email} (already exists)[/dim]")

    console.print(f"\n[green]Seeded {added} demo prospects.[/green]")
    console.print("Run [cyan]python main.py dashboard[/cyan] to see your pipeline.")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _detect_persona(title: str) -> str:
    title_lower = title.lower()
    for persona_key, persona_data in PERSONAS.items():
        for variant in persona_data.get("title_variants", []):
            if variant.lower() in title_lower:
                return persona_key
    # Fallback keyword matching
    if any(k in title_lower for k in ["privacy", "dpo", "data protection"]):
        return "CPO"
    if any(k in title_lower for k in ["security", "ciso", "infosec"]):
        return "CISO"
    if any(k in title_lower for k in ["data officer", "data governance", "cdo"]):
        return "CDO"
    if any(k in title_lower for k in ["legal", "counsel", "compliance"]):
        return "GC"
    if any(k in title_lower for k in ["engineering", "technology", "cto", "product"]):
        return "VP_ENG"
    return "CPO"


def _run_qualification(prospect_id: int):
    p = db.get_prospect(prospect_id)
    if not p:
        return

    console.print(f"\n[cyan]Running qualification for {p.full_name}...[/cyan]")
    from bdr_agents import QualificationAgent, ResearchAgent
    try:
        research = ResearchAgent().run(p.company, p.industry, p.employees, p.title)
        qual = QualificationAgent().run(p, research)
        scheduler = SequenceScheduler()
        next_date, next_channel, _ = scheduler.get_next_touch(date.today(), 0)
        db.update_prospect(
            prospect_id,
            icp_score=qual.total_score,
            icp_tier=qual.tier,
            persona_type=qual.recommended_persona,
            company_summary=research.business_summary,
            pain_points_identified=", ".join(qual.top_pain_points),
            trigger_events=", ".join(research.recent_trigger_events),
            status="qualified" if qual.tier in ("A", "B") else "unqualified",
            next_touch_date=next_date.isoformat() if next_date else None,
            next_touch_type=next_channel,
        )
        from analytics import _tier_color
        color = _tier_color(qual.tier)
        console.print(f"  ICP Score: [{color}][bold]{qual.total_score}/100 (Tier {qual.tier})[/bold][/{color}]")
        console.print(f"  Persona:   {qual.recommended_persona}")
        console.print(f"  Summary:   {qual.qualification_summary[:120]}...")
    except EnvironmentError as e:
        console.print(f"[red]{e}[/red]")


def _display_pipeline_results(prospect, research, qualification, messages):
    from analytics import _tier_color
    tier_color = _tier_color(qualification.tier)

    console.print(Panel(
        f"[bold]Company:[/bold] {research.business_summary}\n\n"
        f"[bold]Privacy Posture:[/bold] {research.data_privacy_posture}\n\n"
        f"[bold]Regulatory Exposure:[/bold] {', '.join(research.regulatory_exposure)}\n\n"
        f"[bold]Trigger Events:[/bold] {', '.join(research.recent_trigger_events[:3]) or 'None identified'}\n\n"
        f"[bold]Recommended Angle:[/bold] [cyan]{research.recommended_angle}[/cyan]",
        title="Research Intelligence",
        border_style="cyan",
    ))

    console.print(Panel(
        f"[bold]Score:[/bold] [{tier_color}][bold]{qualification.total_score}/100 (Tier {qualification.tier})[/bold][/{tier_color}]\n\n"
        f"[bold]Summary:[/bold] {qualification.qualification_summary}\n\n"
        f"[bold]Recommended Persona:[/bold] {qualification.recommended_persona}\n\n"
        f"[bold]Top Pain Points:[/bold]\n" +
        "\n".join(f"  • {pp}" for pp in qualification.top_pain_points) + "\n\n"
        f"[bold]Recommended Sequence:[/bold] {qualification.recommended_sequence}",
        title="ICP Qualification",
        border_style="yellow",
    ))

    console.print("\n[bold]Generated Outreach Messages:[/bold]\n")
    for channel, msgs in messages.items():
        for msg in msgs:
            _display_message(msg, prospect, compact=True)


def _display_message(msg, prospect, compact: bool = False):
    channel_colors = {"email": "cyan", "linkedin": "blue", "phone": "green"}
    color = channel_colors.get(msg.channel, "white")

    header = f"[{color}][bold]{msg.channel.upper()} — Touch {msg.touch_number}[/bold][/{color}]"
    if msg.subject:
        header += f"\n[bold]Subject:[/bold] {msg.subject}"

    content = msg.body
    if not compact:
        content += f"\n\n[dim]CTA: {msg.cta}[/dim]"
        content += f"\n[dim]Pain addressed: {msg.pain_point_addressed}[/dim]"

    console.print(Panel(
        f"{header}\n\n{content}",
        border_style=color,
        padding=(0, 2),
    ))


def _save_messages_to_file(filename, prospect, research, qualification, messages):
    output = {
        "prospect": {
            "name": prospect.full_name,
            "title": prospect.title,
            "company": prospect.company,
            "email": prospect.email,
        },
        "research": research.model_dump(),
        "qualification": qualification.model_dump(),
        "messages": {
            channel: [m.model_dump() for m in msgs]
            for channel, msgs in messages.items()
        },
    }
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    cli()
