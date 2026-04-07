"""
Outreach sequences and templates for the Securiti.ai BDR System.

Contains:
 - BaseSequenceTemplates: fallback templates per persona (no AI needed)
 - SequenceScheduler: computes next-touch dates for a prospect
 - CadenceManager: orchestrates the full outreach cadence
"""

from datetime import date, timedelta
from typing import Optional
from config import CADENCE_CONFIG, PERSONAS, SECURITI_PRODUCT
from models import Prospect, OutreachMessage


# ─────────────────────────────────────────────
#  STATIC EMAIL TEMPLATES (fallback / reference)
# ─────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "CPO": {
        1: {
            "subject": "Quick question about DSARs at {company}",
            "body": """Hi {first_name},

Managing 50+ Data Subject Access Requests manually each month is a full-time job — before you even touch the actual privacy work.

I work with CPOs at companies like {company} who've automated 90%+ of their DSAR processing, cutting response time from weeks to hours.

Would 15 minutes this week be worth it to show you how?

Best,
[BDR Name]
Securiti.ai""",
            "cta": "15-minute call this week",
        },
        2: {
            "subject": "Re: DSARs at {company}",
            "body": """Hi {first_name},

Following up briefly — {company_name_possessive} GDPR/CCPA obligations aren't getting simpler.

A Fortune 500 financial services firm we work with reduced DSAR processing time by 85% in 90 days. Their CPO now has a real-time compliance dashboard instead of a spreadsheet.

15 minutes this week?

Best,
[BDR Name]""",
            "cta": "15-minute call",
        },
        3: {
            "subject": "How {industry} companies are handling CCPA at scale",
            "body": """Hi {first_name},

I put together a short case study on how a top-10 {industry} company automated consent management across 200M customer records.

Key result: $2.3M saved annually in manual compliance work, and zero missed regulatory deadlines in 18 months.

Worth a conversation? Happy to share the full story.

[BDR Name]""",
            "cta": "Short conversation",
        },
        4: {
            "subject": "AI governance for {company} — EU AI Act deadline approaching",
            "body": """Hi {first_name},

A different angle this time: with AI adoption accelerating at most enterprises, the EU AI Act compliance window is closing fast.

Beyond privacy, Securiti helps CPOs govern AI models and training data — so you can tell the board exactly what sensitive data your AI is touching.

Is AI governance on your radar for {company}?

[BDR Name]""",
            "cta": "Quick discovery call",
        },
        5: {
            "subject": "Last note — Securiti.ai for {company}",
            "body": """Hi {first_name},

I've reached out a few times — I clearly have bad timing.

If data privacy automation isn't a priority right now, no problem. If it is and you've just been busy, I'm happy to reconnect whenever works.

Either way, good luck with everything at {company}.

[BDR Name]""",
            "cta": "Just let me know when timing is better",
        },
    },
    "CISO": {
        1: {
            "subject": "Sensitive data exposure at {company} — quick question",
            "body": """Hi {first_name},

Most CISOs I talk to are surprised to learn how much sensitive data exists outside their security perimeter — in SaaS apps, cloud storage, and dev environments their teams don't control.

We help enterprises like {company} discover, classify, and secure sensitive data across every data store — in days, not months.

Worth 15 minutes to see what we're finding for similar companies?

[BDR Name]
Securiti.ai""",
            "cta": "15-minute risk assessment conversation",
        },
        2: {
            "subject": "Re: Sensitive data at {company}",
            "body": """Hi {first_name},

Quick follow-up: a global bank we work with discovered 3x more sensitive PII than they expected once they scanned all their cloud environments.

That kind of blind spot is a regulatory incident waiting to happen.

Do you have full visibility into where {company}'s sensitive data lives?

[BDR Name]""",
            "cta": "15-minute conversation",
        },
        3: {
            "subject": "72-hour breach notification — how ready is {company}?",
            "body": """Hi {first_name},

GDPR requires breach notification within 72 hours. The average time to identify and contain a breach is 277 days.

One of those numbers needs to change.

We automate breach detection, impact assessment, and regulatory notification — so your team isn't scrambling when it matters most.

Happy to walk you through how it works.

[BDR Name]""",
            "cta": "Quick demo",
        },
    },
    "CDO": {
        1: {
            "subject": "How long does data discovery take at {company}?",
            "body": """Hi {first_name},

Most CDOs I talk to run data discovery projects that take 3-6 months and are out of date before they're finished.

We scan and classify 100% of structured and unstructured sensitive data across 2,000+ connectors — in days.

I'd love to show you what we've found for companies similar to {company}.

15 minutes this week?

[BDR Name]
Securiti.ai""",
            "cta": "15-minute demo",
        },
        2: {
            "subject": "Re: Data discovery at {company}",
            "body": """Hi {first_name},

Following up — a healthcare CDO we work with went from 6-month manual discovery cycles to continuous, automated classification across their entire data estate.

Their data governance team went from reactive to proactive in under 90 days.

Worth a quick look?

[BDR Name]""",
            "cta": "15-minute conversation",
        },
    },
}

LINKEDIN_TEMPLATES = {
    "connection_request": {
        "CPO": "Hi {first_name} — I work with privacy leaders at {industry} companies. Would love to connect and share what I'm seeing in the space.",
        "CISO": "Hi {first_name} — connecting with security leaders working on data privacy and sensitive data governance. Would love to add you to my network.",
        "CDO": "Hi {first_name} — I work with data leaders on automated data discovery and governance. Would appreciate connecting.",
        "DPO": "Hi {first_name} — I work with privacy professionals navigating GDPR and CCPA. Would love to connect.",
        "default": "Hi {first_name} — I work with enterprise leaders on data privacy and AI governance. Would love to connect.",
    },
    "follow_up": {
        "CPO": """Thanks for connecting, {first_name}.

I work with CPOs at large enterprises to automate privacy operations — DSARs, consent, and compliance reporting.

Given {company}'s footprint, I imagine privacy operations at scale is a real challenge. Would a 15-min conversation be worth it?""",
        "CISO": """Thanks for connecting, {first_name}.

We help security teams at companies like {company} discover and protect sensitive data across their entire data estate — including shadow data they don't know exists.

Worth a quick conversation?""",
        "default": """Thanks for connecting, {first_name}.

I help enterprise privacy and data teams automate their compliance operations with Securiti.ai. Given {company}'s scale, I'd love to share what we're seeing in the market.

Would a brief call make sense?""",
    },
    "value_add": {
        "CPO": """Hi {first_name},

Sharing a resource that might be useful: we just published a guide on building a privacy program that scales without adding headcount.

Key insight: automating consent + DSAR processing frees the privacy team to focus on strategic work instead of admin.

Happy to walk you through what that looks like in practice. Let me know.""",
        "CISO": """Hi {first_name},

Thought you might find this useful: a framework for building a sensitive data exposure risk score across your full data estate.

We use it to help CISOs prioritize remediation — rather than treating every data store equally.

Happy to share the methodology if that would be helpful.""",
        "default": """Hi {first_name},

Sharing something that might be relevant — a benchmarking report on data privacy program maturity across {industry} companies.

Key finding: organizations with automated DSAR and consent management spend 60% less on compliance labor.

Happy to share the full findings if useful.""",
    },
}

CALL_SCRIPTS = {
    "opening": {
        "CPO": """Hi {first_name}, this is [Name] from Securiti.ai — we help large enterprises automate their privacy operations.

I know this is out of the blue, but I work with a lot of CPOs who are drowning in manual DSARs and consent management. I had a quick question: how is {company} currently handling DSAR processing at scale?

[PAUSE — listen]""",
        "CISO": """Hi {first_name}, this is [Name] from Securiti.ai. We help enterprise security teams get full visibility into where their sensitive data lives — across every cloud, SaaS, and on-prem store.

Quick question: how confident is {company} in knowing exactly where all your sensitive PII is right now?

[PAUSE — listen]""",
        "CDO": """Hi {first_name}, [Name] from Securiti.ai. We help CDOs automate data discovery and classification — scanning the entire data estate in days rather than months.

I'm curious: what does data discovery currently look like at {company}? Is it an ongoing process or a periodic project?

[PAUSE — listen]""",
        "default": """Hi {first_name}, [Name] from Securiti.ai. We work with enterprise data and privacy leaders to automate data governance and compliance.

I had a quick question about {company}'s data privacy program — do you have 30 seconds?

[PAUSE]""",
    },
    "voicemail": {
        "CPO": """Hi {first_name}, [Name] from Securiti.ai. Quick question on how {company} is handling DSARs and consent at scale — I've been working with a few CPOs in {industry} on automating this and thought it might be relevant. Callback number is [phone]. Thanks.""",
        "CISO": """Hi {first_name}, [Name] from Securiti.ai. I'm calling about sensitive data visibility — specifically how {company} maps and secures sensitive data across cloud and SaaS environments. Call me back at [phone] when you have a moment. Thanks.""",
        "default": """Hi {first_name}, [Name] from Securiti.ai. Reaching out about data privacy and governance automation — I've been speaking with {industry} leaders and thought {company} might find it relevant. Callback at [phone]. Thanks.""",
    },
    "discovery_questions": [
        "How is your team currently handling Data Subject Access Requests? What does that process look like?",
        "What tools do you have in place today for consent management?",
        "How do you know where all your sensitive data lives — especially in cloud and SaaS environments?",
        "What does your GDPR/CCPA compliance program look like today?",
        "How large is your privacy team, and are they able to keep up with the volume of requests?",
        "Is AI governance on your roadmap — governing training data and model inventories?",
        "Have you looked at other vendors in this space? What's been the experience?",
        "What would need to be true for you to prioritize a project like this this year?",
    ],
    "objection_handling": {
        "we_have_onetrust": """I hear that — OneTrust is a strong consent tool. Where Securiti is different is on the data intelligence side: we actually scan your full data estate to find sensitive data, not just manage consent preferences. Most OneTrust customers still have blind spots on where data lives. Is that visibility gap something you've felt?""",
        "no_budget": """Makes total sense. Most of the conversations I have right now aren't 'buy this quarter' — they're about planning ahead. When does your next budget cycle open up? And would it make sense to get a proof-of-concept together so you have numbers when it does?""",
        "not_a_priority": """Fair enough. What would need to happen to make it a priority — a regulatory fine? An audit? I'm asking genuinely, not to scare you. I want to understand what the trigger looks like for your organization.""",
        "too_complex": """I understand that concern — most enterprise tools are heavy. Our average time-to-value is 60-90 days for core use cases, not 18 months. Would it be worth seeing a proof of concept just to see what 'quick win' looks like for {company}?""",
        "send_me_info": """Happy to send something over. To make sure I send the most relevant thing — is data discovery, DSAR automation, or consent management the most pressing challenge right now? I'll tailor what I send.""",
    },
}


# ─────────────────────────────────────────────
#  SEQUENCE SCHEDULER
# ─────────────────────────────────────────────

class SequenceScheduler:
    """Computes next touch dates based on cadence config."""

    CHANNEL_SCHEDULE = CADENCE_CONFIG["sequence_touches"]

    def get_next_touch(self, start_date: date, sequence_day: int) -> tuple:
        """Returns (next_touch_date, channel, touch_number) or None if sequence complete."""
        all_touches = []
        for channel, days in self.CHANNEL_SCHEDULE.items():
            for i, d in enumerate(days, start=1):
                touch_date = start_date + timedelta(days=d)
                all_touches.append((touch_date, channel, i, d))

        all_touches.sort(key=lambda x: x[0])

        for touch_date, channel, touch_num, day_offset in all_touches:
            if day_offset > sequence_day:
                return touch_date, channel, touch_num

        return None, None, None  # Sequence complete

    def days_until_next_touch(self, prospect: Prospect) -> int:
        if not prospect.next_touch_date:
            return 0
        delta = date.fromisoformat(prospect.next_touch_date) - date.today()
        return max(0, delta.days)


# ─────────────────────────────────────────────
#  TEMPLATE RENDERER
# ─────────────────────────────────────────────

class TemplateRenderer:
    """Renders static templates with prospect data as fallback when AI is unavailable."""

    def render_email(
        self, persona_type: str, touch_number: int, prospect: Prospect
    ) -> Optional[OutreachMessage]:
        templates = EMAIL_TEMPLATES.get(persona_type, EMAIL_TEMPLATES.get("CPO", {}))
        template = templates.get(touch_number)
        if not template:
            return None

        vars = {
            "first_name": prospect.first_name,
            "company": prospect.company,
            "company_name_possessive": f"{prospect.company}'s",
            "industry": prospect.industry,
            "title": prospect.title,
        }

        subject = template["subject"].format(**vars)
        body = template["body"].format(**vars)

        return OutreachMessage(
            channel="email",
            touch_number=touch_number,
            subject=subject,
            body=body,
            cta=template["cta"],
            persona_type=persona_type,
            pain_point_addressed="General ICP pain point",
            personalization_notes="Static template — consider AI personalization for better results",
        )

    def render_linkedin(
        self, persona_type: str, touch_number: int, prospect: Prospect
    ) -> Optional[OutreachMessage]:
        vars = {
            "first_name": prospect.first_name,
            "company": prospect.company,
            "industry": prospect.industry,
        }

        if touch_number == 1:
            msg = LINKEDIN_TEMPLATES["connection_request"].get(
                persona_type,
                LINKEDIN_TEMPLATES["connection_request"]["default"]
            ).format(**vars)
            cta = "Connect on LinkedIn"
        elif touch_number == 2:
            msg = LINKEDIN_TEMPLATES["follow_up"].get(
                persona_type,
                LINKEDIN_TEMPLATES["follow_up"]["default"]
            ).format(**vars)
            cta = "15-minute call"
        else:
            msg = LINKEDIN_TEMPLATES["value_add"].get(
                persona_type,
                LINKEDIN_TEMPLATES["value_add"]["default"]
            ).format(**vars)
            cta = "Let me know if useful"

        return OutreachMessage(
            channel="linkedin",
            touch_number=touch_number,
            body=msg,
            cta=cta,
            persona_type=persona_type,
            pain_point_addressed="Role-specific pain",
            personalization_notes="Static template",
        )

    def render_call_script(
        self, persona_type: str, touch_number: int, prospect: Prospect
    ) -> Optional[OutreachMessage]:
        vars = {
            "first_name": prospect.first_name,
            "company": prospect.company,
            "industry": prospect.industry,
        }

        if touch_number == 1:
            script = CALL_SCRIPTS["opening"].get(
                persona_type, CALL_SCRIPTS["opening"]["default"]
            ).format(**vars)
            cta = "30-second conversation"
        else:
            script = CALL_SCRIPTS["voicemail"].get(
                persona_type, CALL_SCRIPTS["voicemail"]["default"]
            ).format(**vars)
            cta = "Callback"

        return OutreachMessage(
            channel="phone",
            touch_number=touch_number,
            body=script,
            cta=cta,
            persona_type=persona_type,
            pain_point_addressed="Opening hook",
            personalization_notes="Static template",
        )
