"""
Securiti.ai BDR Configuration
ICP definition, target personas, product positioning, and outreach strategy.
"""

# ─────────────────────────────────────────────
#  SECURITI.AI PRODUCT INTELLIGENCE
# ─────────────────────────────────────────────
SECURITI_PRODUCT = {
    "name": "Securiti.ai",
    "tagline": "The Only Unified Data Security and Privacy Platform",
    "category": "Data Security, Privacy Management, AI Governance",
    "key_products": {
        "PrivacyOps": "End-to-end privacy operations automation (DSAR, consent, assessments)",
        "Data Command Center": "AI-powered data discovery, classification, and intelligence across all data stores",
        "Consent Management": "Enterprise consent orchestration across web, mobile, and connected devices",
        "AI Governance": "Govern, audit, and secure AI models and training data",
        "Data Access Intelligence": "Automated data access controls and sensitive data protection",
        "Breach Response": "Automated breach detection, assessment, and notification workflows",
    },
    "key_differentiators": [
        "Unified platform: data security + privacy + AI governance in one pane of glass",
        "2,000+ pre-built connectors to scan structured and unstructured data",
        "AI-powered data discovery finds sensitive data 10x faster than manual processes",
        "Automates 90% of DSAR (Data Subject Access Requests) end-to-end",
        "Real-time consent management with global regulatory coverage (GDPR, CCPA, LGPD, PDPB…)",
        "Only platform with native AI governance for model inventories and training data compliance",
        "SOC 2 Type II, ISO 27001, FedRAMP ready",
    ],
    "key_competitors": ["OneTrust", "TrustArc", "BigID", "Privitar", "Varonis", "Informatica"],
    "pricing_model": "Annual SaaS subscription, enterprise licensing",
    "typical_deal_size": "$150K–$1.5M ARR",
    "sales_cycle": "3–9 months",
    "customer_proof_points": [
        "Fortune 500 financial services firm reduced DSAR processing time by 85%",
        "Global healthcare provider achieved GDPR compliance 60% faster",
        "Top-10 US retailer automated consent management across 200M customer records",
        "Major tech company reduced data privacy risk exposure by $40M annually",
    ],
}

# ─────────────────────────────────────────────
#  IDEAL CUSTOMER PROFILE (ICP)
# ─────────────────────────────────────────────
ICP = {
    "firmographic": {
        "company_size": {
            "min_employees": 500,
            "sweet_spot_employees": 2000,
            "max_employees": 100000,
        },
        "annual_revenue_usd": {
            "min": 100_000_000,   # $100M
            "sweet_spot": 1_000_000_000,  # $1B
        },
        "industries": [
            "Financial Services",
            "Banking",
            "Insurance",
            "Healthcare",
            "Life Sciences / Pharma",
            "Retail / eCommerce",
            "Technology / SaaS",
            "Telecommunications",
            "Manufacturing",
            "Media & Entertainment",
            "Energy & Utilities",
        ],
        "geographies": ["North America", "United Kingdom", "Germany", "France", "Benelux", "Nordics", "ANZ"],
        "company_types": ["Public enterprise", "Private equity-backed", "Regulated industry"],
    },
    "technographic": {
        "data_stack_signals": [
            "Snowflake", "Databricks", "AWS (S3, RDS, Redshift)", "Azure (ADLS, SQL)",
            "Google BigQuery", "Salesforce", "SAP", "Oracle", "ServiceNow",
        ],
        "current_privacy_tools": [
            "OneTrust (migration opportunity)",
            "TrustArc (migration opportunity)",
            "In-house spreadsheets (upgrade opportunity)",
            "No dedicated tool (greenfield)",
        ],
        "security_tools": ["Splunk", "CrowdStrike", "Palo Alto", "Microsoft Defender"],
    },
    "trigger_events": [
        "Regulatory fine or enforcement action (GDPR, CCPA, FTC)",
        "New privacy law in their operating region",
        "Data breach or near-miss incident",
        "Hiring a DPO, CPO, or Privacy team lead",
        "M&A activity requiring data compliance due diligence",
        "Launching AI/ML initiatives needing governance",
        "IPO preparation (data governance required)",
        "Quarterly earnings mentioning compliance risk",
        "OneTrust or TrustArc contract renewal coming up",
        "Expanding into EU/UK markets (GDPR exposure)",
    ],
    "pain_points": {
        "compliance": [
            "Drowning in manual DSAR processing (50–500+ requests/month)",
            "GDPR/CCPA fines and enforcement actions",
            "Unable to prove compliance to regulators and auditors",
            "Consent records are scattered and unverifiable",
            "Cross-border data transfer complexity (SCCs, BCRs)",
        ],
        "data_management": [
            "Don't know where all their sensitive data lives",
            "Shadow IT and uncontrolled data proliferation",
            "Manual data discovery takes months and is always outdated",
            "Data lineage is opaque — can't trace data flows",
            "Vendor/third-party data sharing is ungoverned",
        ],
        "ai_governance": [
            "Training AI on sensitive data without visibility into what's included",
            "No inventory of AI models and their data dependencies",
            "Board-level pressure on responsible AI but no tooling",
            "EU AI Act compliance deadline approaching",
        ],
        "operational": [
            "Privacy team is overwhelmed and under-resourced",
            "Legal/Privacy/IT/Engineering work in silos",
            "Privacy-by-design isn't embedded in product development",
            "Board and CEO demanding privacy metrics they can't produce",
        ],
    },
}

# ─────────────────────────────────────────────
#  TARGET PERSONAS
# ─────────────────────────────────────────────
PERSONAS = {
    "CPO": {
        "title_variants": [
            "Chief Privacy Officer", "CPO", "VP of Privacy",
            "Head of Privacy", "Global Head of Privacy",
        ],
        "primary_pain": "Board-level accountability for privacy compliance and risk reduction",
        "key_metrics": ["DSAR response time", "Consent rates", "Regulatory fine exposure", "Privacy program maturity"],
        "hook": "automate 90% of DSARs and get a real-time privacy compliance dashboard",
        "objections": ["We already have OneTrust", "Budget is frozen", "We're doing fine with our current process"],
    },
    "CDO": {
        "title_variants": [
            "Chief Data Officer", "CDO", "VP of Data",
            "Head of Data Governance", "VP Data Management",
        ],
        "primary_pain": "Data proliferation, ungoverned sensitive data, and inability to trust data quality",
        "key_metrics": ["Data catalog coverage", "Sensitive data discovery speed", "Data access policy coverage"],
        "hook": "discover and classify 100% of sensitive data across all data stores in days, not months",
        "objections": ["We have Collibra/Alation already", "Data governance is a 2-year initiative"],
    },
    "CISO": {
        "title_variants": [
            "Chief Information Security Officer", "CISO", "VP of Security",
            "Head of Information Security", "VP Cybersecurity",
        ],
        "primary_pain": "Sensitive data exposure risk, insider threats, and breach liability",
        "key_metrics": ["Sensitive data exposure surface", "Access policy violations", "Breach notification readiness"],
        "hook": "reduce sensitive data exposure risk and automate breach notification in under 72 hours",
        "objections": ["This is a privacy problem, not security", "We have Varonis/BigID"],
    },
    "DPO": {
        "title_variants": [
            "Data Protection Officer", "DPO", "Privacy Manager",
            "Data Privacy Manager", "Privacy Counsel",
        ],
        "primary_pain": "GDPR compliance obligations with limited resources and manual processes",
        "key_metrics": ["DSAR completion rate", "Records of processing activities", "DPIA completion time"],
        "hook": "automate your GDPR compliance obligations and cut DSAR processing from weeks to hours",
        "objections": ["We're a small privacy team, can't take on a big implementation", "Cost justification is hard"],
    },
    "GC": {
        "title_variants": [
            "General Counsel", "VP Legal", "Chief Legal Officer",
            "Deputy General Counsel", "VP Compliance",
        ],
        "primary_pain": "Legal liability from privacy violations, regulatory penalties, and class-action risk",
        "key_metrics": ["Regulatory fine exposure", "Litigation risk", "Compliance attestation coverage"],
        "hook": "reduce legal liability with automated compliance evidence and defensible consent records",
        "objections": ["Privacy is handled by the privacy team", "We need board approval for this spend"],
    },
    "VP_ENG": {
        "title_variants": [
            "VP Engineering", "CTO", "VP Product",
            "Chief Technology Officer", "Head of AI/ML",
        ],
        "primary_pain": "AI governance, privacy-by-design in product, and EU AI Act compliance",
        "key_metrics": ["AI model inventory", "Training data governance", "Privacy-by-design adoption"],
        "hook": "govern your AI models and training data to stay ahead of EU AI Act requirements",
        "objections": ["We build privacy features in-house", "This isn't an engineering priority right now"],
    },
}

# ─────────────────────────────────────────────
#  OUTREACH STRATEGY & CADENCE SETTINGS
# ─────────────────────────────────────────────
CADENCE_CONFIG = {
    "monthly_meeting_target": 20,
    "weekly_meeting_target": 5,
    "pipeline_multiplier": 50,  # prospects needed per meeting (at ~2% conversion)
    "monthly_prospect_target": 1000,  # to hit 20 meetings
    "sequence_touches": {
        "email": [1, 3, 7, 14, 21],    # days from day 0
        "linkedin": [2, 8, 16],          # days from day 0
        "phone": [4, 10, 18],            # days from day 0
    },
    "follow_up_days_after_meeting": 1,
    "prospect_statuses": [
        "new",
        "researched",
        "qualified",
        "in_sequence",
        "responded",
        "meeting_scheduled",
        "meeting_held",
        "opportunity",
        "closed_won",
        "closed_lost",
        "unqualified",
        "do_not_contact",
    ],
    "activity_types": [
        "email_sent",
        "email_opened",
        "email_clicked",
        "email_replied",
        "linkedin_connection_sent",
        "linkedin_connection_accepted",
        "linkedin_message_sent",
        "linkedin_message_replied",
        "call_attempted",
        "call_connected",
        "call_voicemail",
        "meeting_scheduled",
        "meeting_held",
        "meeting_no_show",
        "note_added",
    ],
}

# ─────────────────────────────────────────────
#  ICP SCORING WEIGHTS
# ─────────────────────────────────────────────
ICP_SCORING = {
    "max_score": 100,
    "criteria": {
        "industry_fit": {
            "weight": 25,
            "tier_1": ["Financial Services", "Banking", "Insurance", "Healthcare", "Life Sciences / Pharma"],
            "tier_2": ["Retail / eCommerce", "Technology / SaaS", "Telecommunications"],
            "tier_3": ["Manufacturing", "Media & Entertainment", "Energy & Utilities"],
        },
        "company_size": {
            "weight": 20,
            "sweet_spot_min": 1000,
            "sweet_spot_max": 20000,
        },
        "persona_seniority": {
            "weight": 20,
            "c_suite": ["CPO", "CDO", "CISO", "CTO", "GC", "CLO"],
            "vp_level": ["VP", "Vice President", "Head of"],
            "director_level": ["Director", "DPO", "Manager"],
        },
        "trigger_event": {
            "weight": 20,
            "high_value": [
                "regulatory fine", "data breach", "hiring dpo", "hiring cpo",
                "gdpr enforcement", "ccpa violation", "ipo preparation",
            ],
            "medium_value": [
                "tool renewal", "m&a", "expansion", "ai initiative",
                "new privacy law", "compliance audit",
            ],
        },
        "tech_stack_fit": {
            "weight": 15,
            "high_signal": ["Snowflake", "Databricks", "OneTrust", "TrustArc"],
            "medium_signal": ["Salesforce", "SAP", "Oracle", "AWS", "Azure"],
        },
    },
}
