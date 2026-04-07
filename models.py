"""
Data models for the Securiti.ai BDR System.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class Prospect(BaseModel):
    id: Optional[int] = None
    # Contact info
    first_name: str
    last_name: str
    full_name: str = ""
    title: str
    email: str
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    # Company info
    company: str
    industry: str
    employees: Optional[int] = None
    revenue_usd: Optional[int] = None
    website: Optional[str] = None
    hq_location: Optional[str] = None
    # Classification
    persona_type: Optional[str] = None        # CPO, CDO, CISO, DPO, GC, VP_ENG
    status: str = "new"
    icp_score: Optional[int] = None           # 0-100
    icp_tier: Optional[str] = None            # A, B, C
    # Research
    company_summary: Optional[str] = None
    pain_points_identified: Optional[str] = None
    trigger_events: Optional[str] = None
    tech_stack: Optional[str] = None
    notes: Optional[str] = None
    # Sequence tracking
    sequence_day: int = 0
    last_touch_date: Optional[str] = None
    next_touch_date: Optional[str] = None
    next_touch_type: Optional[str] = None     # email, linkedin, phone
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def model_post_init(self, __context):
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()


class Activity(BaseModel):
    id: Optional[int] = None
    prospect_id: int
    activity_type: str         # email_sent, call_connected, meeting_scheduled, etc.
    subject: Optional[str] = None
    body: Optional[str] = None
    outcome: Optional[str] = None
    sequence_touch: Optional[int] = None   # Which touch in the sequence (1-5)
    channel: Optional[str] = None          # email, linkedin, phone
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Meeting(BaseModel):
    id: Optional[int] = None
    prospect_id: int
    prospect_name: str
    company: str
    persona_type: Optional[str] = None
    scheduled_date: Optional[str] = None
    held_date: Optional[str] = None
    meeting_type: str = "discovery"        # discovery, demo, technical, executive
    status: str = "scheduled"              # scheduled, held, no_show, cancelled, rescheduled
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    opportunity_created: bool = False
    deal_value_usd: Optional[int] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OutreachMessage(BaseModel):
    channel: str                   # email, linkedin, phone
    touch_number: int
    subject: Optional[str] = None  # Email only
    body: str
    cta: str                       # Call to action
    persona_type: str
    pain_point_addressed: str
    personalization_notes: str


class ICPScoreResult(BaseModel):
    total_score: int               # 0-100
    tier: str                      # A (80+), B (60-79), C (40-59), D (<40)
    industry_score: int
    size_score: int
    persona_score: int
    trigger_score: int
    tech_score: int
    qualification_summary: str
    recommended_persona: str
    top_pain_points: List[str]
    recommended_sequence: str      # aggressive, standard, nurture


class ResearchResult(BaseModel):
    company: str
    industry: str
    employee_count: Optional[int] = None
    revenue_estimate: Optional[str] = None
    hq_location: Optional[str] = None
    business_summary: str
    data_privacy_posture: str      # their current privacy maturity
    regulatory_exposure: List[str] # Which regulations apply (GDPR, CCPA, etc.)
    tech_stack_signals: List[str]
    recent_trigger_events: List[str]
    key_pain_points: List[str]
    recommended_angle: str         # The best opening hook
    research_confidence: str       # high, medium, low


class PipelineStats(BaseModel):
    month: str
    prospects_added: int
    emails_sent: int
    calls_made: int
    linkedin_sent: int
    responses: int
    meetings_scheduled: int
    meetings_held: int
    no_shows: int
    opportunities_created: int
    target_meetings: int = 20
    meetings_pct_of_target: float = 0.0
    response_rate: float = 0.0
    meeting_conversion_rate: float = 0.0
