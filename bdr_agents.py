"""
Claude-powered BDR Agents for Securiti.ai.

Three specialized agents orchestrated by the BDROrchestrator:
  1. ResearchAgent     – builds intelligence on a prospect's company
  2. QualificationAgent – scores the lead against Securiti.ai ICP criteria
  3. PersonalizationAgent – generates channel-specific, persona-aware messages
  4. BDROrchestrator   – runs the full pipeline end-to-end
"""

import json
import os
from typing import Optional
import anthropic

from config import SECURITI_PRODUCT, ICP, PERSONAS, ICP_SCORING, CADENCE_CONFIG
from models import Prospect, ResearchResult, ICPScoreResult, OutreachMessage


# ─────────────────────────────────────────────
#  SHARED CLIENT
# ─────────────────────────────────────────────

def _client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")
    return anthropic.Anthropic(api_key=api_key)


MODEL = "claude-opus-4-6"


def _chat(system: str, user: str, use_thinking: bool = False) -> str:
    """Single-turn Claude call with optional adaptive thinking."""
    client = _client()
    kwargs = dict(
        model=MODEL,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    with client.messages.stream(**kwargs) as stream:
        return stream.get_final_message().content[0].text


# ─────────────────────────────────────────────
#  AGENT 1: RESEARCH AGENT
# ─────────────────────────────────────────────

RESEARCH_SYSTEM = """You are an elite B2B sales intelligence analyst specializing in enterprise data privacy and security markets.

Your job is to analyze a company and produce actionable sales intelligence for Securiti.ai BDRs.

Securiti.ai sells unified data security, privacy management, and AI governance platform to enterprises.
Target buyers: CPO, CDO, CISO, DPO, General Counsel, CTO.

Always produce a JSON object matching this exact schema (no markdown fences, just raw JSON):
{
  "company": "string",
  "industry": "string",
  "employee_count": number_or_null,
  "revenue_estimate": "string_or_null",
  "hq_location": "string_or_null",
  "business_summary": "2-3 sentence description of what the company does",
  "data_privacy_posture": "Assessment of their current privacy maturity and exposure (1-2 sentences)",
  "regulatory_exposure": ["list", "of", "applicable", "regulations"],
  "tech_stack_signals": ["list", "of", "known", "or", "likely", "technologies"],
  "recent_trigger_events": ["list", "of", "recent", "events", "suggesting", "buying", "intent"],
  "key_pain_points": ["list", "of", "3-5", "specific", "pain", "points"],
  "recommended_angle": "The single most compelling opening hook for this prospect",
  "research_confidence": "high|medium|low"
}
"""


class ResearchAgent:
    """Researches a prospect's company and returns structured intelligence."""

    def run(self, company: str, industry: str,
            employees: Optional[int] = None,
            persona_title: Optional[str] = None,
            additional_context: Optional[str] = None) -> ResearchResult:

        user_msg = f"""Research this company for Securiti.ai sales outreach:

Company: {company}
Industry: {industry}
Employees: {employees or 'unknown'}
Contact Title: {persona_title or 'unknown'}
Additional Context: {additional_context or 'none'}

Produce the JSON intelligence report. Use your knowledge of this company and industry.
If you don't have specific knowledge, make well-reasoned inferences based on the industry and company size.
Focus on data privacy, compliance, and AI governance angles that make Securiti.ai relevant."""

        raw = _chat(RESEARCH_SYSTEM, user_msg, use_thinking=True)

        # Strip any accidental markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return ResearchResult(**data)


# ─────────────────────────────────────────────
#  AGENT 2: QUALIFICATION AGENT
# ─────────────────────────────────────────────

QUALIFICATION_SYSTEM = """You are a senior BDR manager at Securiti.ai scoring inbound and outbound leads.

Score each prospect against the ICP criteria below and return a JSON object.
Be rigorous — only A-tier prospects should get scores above 80.

Securiti.ai ICP scoring criteria (total 100 points):
- Industry fit (25 pts): Tier 1 = Financial/Healthcare/Insurance (22-25), Tier 2 = Retail/Tech/Telecom (14-18), Tier 3 = other (8-12)
- Company size (20 pts): 1000-20000 employees = 18-20, 500-999 = 12-15, 20001+ = 14-16, <500 = 5-8
- Persona seniority (20 pts): C-suite = 18-20, VP/Head = 14-16, Director/DPO = 10-12, Manager = 6-8
- Trigger events (20 pts): 0-20 based on number and strength of buying triggers
- Tech stack fit (15 pts): 0-15 based on data/cloud tool overlap

Always produce raw JSON (no markdown fences):
{
  "total_score": integer_0_to_100,
  "tier": "A|B|C|D",
  "industry_score": integer,
  "size_score": integer,
  "persona_score": integer,
  "trigger_score": integer,
  "tech_score": integer,
  "qualification_summary": "2-3 sentence summary of why this is or isn't a good fit",
  "recommended_persona": "CPO|CDO|CISO|DPO|GC|VP_ENG",
  "top_pain_points": ["pain1", "pain2", "pain3"],
  "recommended_sequence": "aggressive|standard|nurture"
}

Tier guide: A = 80-100 (top priority), B = 60-79, C = 40-59, D = <40 (do not work)
Sequence guide: aggressive = A-tier with trigger events, standard = B/C-tier, nurture = no immediate trigger
"""


class QualificationAgent:
    """Scores a prospect against Securiti.ai ICP and returns qualification details."""

    def run(self, prospect: Prospect, research: Optional[ResearchResult] = None) -> ICPScoreResult:
        research_context = ""
        if research:
            research_context = f"""
Research Intelligence:
- Business: {research.business_summary}
- Privacy posture: {research.data_privacy_posture}
- Regulatory exposure: {', '.join(research.regulatory_exposure)}
- Tech stack signals: {', '.join(research.tech_stack_signals)}
- Trigger events: {', '.join(research.recent_trigger_events)}
- Key pain points: {', '.join(research.key_pain_points)}
"""

        user_msg = f"""Score this prospect for Securiti.ai:

Contact: {prospect.full_name}, {prospect.title}
Company: {prospect.company}
Industry: {prospect.industry}
Employees: {prospect.employees or 'unknown'}
Revenue: ${prospect.revenue_usd:,} if {prospect.revenue_usd} else 'unknown'
{research_context}

Return the qualification score JSON."""

        raw = _chat(QUALIFICATION_SYSTEM, user_msg, use_thinking=True)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return ICPScoreResult(**data)


# ─────────────────────────────────────────────
#  AGENT 3: PERSONALIZATION AGENT
# ─────────────────────────────────────────────

PERSONALIZATION_SYSTEM = """You are a world-class B2B sales copywriter for Securiti.ai, an enterprise data privacy and AI governance platform.

Your outreach is:
- Hyper-personalized to the individual's role, company, and pain points
- Concise (emails under 150 words, LinkedIn under 100 words)
- Pain-led, not product-led — lead with their problem, not our features
- Compelling CTA focused on a low-friction next step (15-min call)
- Never generic, never spammy, never over-selling

Securiti.ai key value props by persona:
- CPO/DPO: Automate 90% of DSARs; real-time compliance dashboard; GDPR/CCPA automation
- CDO: Discover 100% of sensitive data in days; AI-powered classification; data lineage
- CISO: Reduce sensitive data exposure; breach notification < 72 hrs; access intelligence
- GC: Reduce legal liability; defensible consent records; regulatory evidence automation
- VP Eng/CTO: AI governance; EU AI Act readiness; privacy-by-design tooling

Always return raw JSON (no markdown fences) with this schema:
{
  "channel": "email|linkedin|phone",
  "touch_number": integer,
  "subject": "string_or_null",
  "body": "the message text",
  "cta": "the specific call to action",
  "persona_type": "string",
  "pain_point_addressed": "the specific pain point this targets",
  "personalization_notes": "brief note on personalization hooks used"
}
"""


TOUCH_PROMPTS = {
    "email": {
        1: "Day 1 cold intro email. Pain-led opener referencing their specific situation. No product pitch yet. CTA: 15-min call this week.",
        2: "Day 3 follow-up. Add one concrete social proof (customer stat or outcome). Short. CTA: 15-min call.",
        3: "Day 7 email. Different angle — share a relevant case study or ROI stat. Soft CTA: 'Worth a conversation?'",
        4: "Day 14 email. New angle: AI governance / EU AI Act angle if relevant, else DSAR automation. CTA: short demo.",
        5: "Day 21 break-up email. Honest, direct, give them an easy way to say 'not now'. CTA: 'Just let me know.'",
    },
    "linkedin": {
        1: "LinkedIn connection request (under 300 characters). Professional, specific to their role. No ask yet.",
        2: "LinkedIn follow-up after connection (under 100 words). Value-first message. Soft CTA.",
        3: "LinkedIn final message. Share a resource or insight. Easy opt-out.",
    },
    "phone": {
        1: "Cold call opening script (30-second pitch). Hook + pain + CTA for brief call.",
        2: "Call voicemail script (under 25 seconds). Specific, intriguing. Leave callback number.",
        3: "Final call attempt. Reference prior outreach. Give them an easy way to tell you to stop.",
    },
}


class PersonalizationAgent:
    """Generates personalized outreach messages for a specific channel and touch."""

    def run(
        self,
        prospect: Prospect,
        channel: str,        # email, linkedin, phone
        touch_number: int,
        research: Optional[ResearchResult] = None,
        qualification: Optional[ICPScoreResult] = None,
    ) -> OutreachMessage:

        persona = PERSONAS.get(prospect.persona_type or "CPO", PERSONAS["CPO"])
        touch_instruction = TOUCH_PROMPTS.get(channel, {}).get(touch_number, "Standard outreach message.")

        pain_context = ""
        if qualification and qualification.top_pain_points:
            pain_context = f"Identified pain points: {', '.join(qualification.top_pain_points)}"
        elif research and research.key_pain_points:
            pain_context = f"Identified pain points: {', '.join(research.key_pain_points)}"

        trigger_context = ""
        if research and research.recent_trigger_events:
            triggers = [t for t in research.recent_trigger_events if t]
            if triggers:
                trigger_context = f"Recent trigger events: {', '.join(triggers[:3])}"

        user_msg = f"""Write a {channel} outreach message for this Securiti.ai prospect:

Contact: {prospect.full_name}
Title: {prospect.title}
Company: {prospect.company}
Industry: {prospect.industry}
Employees: {prospect.employees or 'unknown'}
Persona type: {prospect.persona_type or 'CPO'}
Primary pain: {persona.get('primary_pain', '')}
Hook: {persona.get('hook', '')}
{pain_context}
{trigger_context}

Touch type: {touch_instruction}
Channel: {channel}
Touch number: {touch_number}

Write the message now. Be specific to {prospect.company} and {prospect.title}. Return JSON."""

        raw = _chat(PERSONALIZATION_SYSTEM, user_msg)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return OutreachMessage(**data)


# ─────────────────────────────────────────────
#  ORCHESTRATOR: FULL BDR PIPELINE
# ─────────────────────────────────────────────

class BDROrchestrator:
    """
    Runs the full BDR pipeline for a prospect:
    1. Research the company
    2. Qualify against ICP
    3. Generate all sequence messages
    Returns a dict with research, qualification, and outreach messages.
    """

    def __init__(self):
        self.research_agent = ResearchAgent()
        self.qualification_agent = QualificationAgent()
        self.personalization_agent = PersonalizationAgent()

    def run_full_pipeline(self, prospect: Prospect) -> dict:
        print(f"  [1/3] Researching {prospect.company}...")
        research = self.research_agent.run(
            company=prospect.company,
            industry=prospect.industry,
            employees=prospect.employees,
            persona_title=prospect.title,
        )

        print(f"  [2/3] Qualifying {prospect.full_name} ({prospect.title})...")
        qualification = self.qualification_agent.run(prospect, research)

        print(f"  [3/3] Generating personalized outreach sequences...")
        messages = self._generate_full_sequence(prospect, research, qualification)

        return {
            "research": research,
            "qualification": qualification,
            "messages": messages,
        }

    def _generate_full_sequence(
        self,
        prospect: Prospect,
        research: ResearchResult,
        qualification: ICPScoreResult,
    ) -> dict:
        sequence = {"email": [], "linkedin": [], "phone": []}

        for touch in range(1, 6):
            msg = self.personalization_agent.run(
                prospect, "email", touch, research, qualification
            )
            sequence["email"].append(msg)

        for touch in range(1, 4):
            msg = self.personalization_agent.run(
                prospect, "linkedin", touch, research, qualification
            )
            sequence["linkedin"].append(msg)

        for touch in range(1, 4):
            msg = self.personalization_agent.run(
                prospect, "phone", touch, research, qualification
            )
            sequence["phone"].append(msg)

        return sequence

    def run_single_touch(
        self,
        prospect: Prospect,
        channel: str,
        touch_number: int,
        research: Optional[ResearchResult] = None,
        qualification: Optional[ICPScoreResult] = None,
    ) -> OutreachMessage:
        """Generate a single outreach message for an existing prospect."""
        if not research:
            research = self.research_agent.run(
                company=prospect.company,
                industry=prospect.industry,
                employees=prospect.employees,
                persona_title=prospect.title,
            )
        if not qualification:
            qualification = self.qualification_agent.run(prospect, research)

        return self.personalization_agent.run(
            prospect, channel, touch_number, research, qualification
        )
