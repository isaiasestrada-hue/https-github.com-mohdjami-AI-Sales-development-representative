import base64
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.params import Form
from fastapi.responses import RedirectResponse
import httpx
import os
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode

import requests


from services.reply_tracker import analyze_sentiment, generate_followup_email
from services.google_service import GoogleService
from services.linkedin_service import LinkedInService
from services.prospect_discovery_service import ProspectDiscoveryService
from services.email_service import EmailService
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
from core.logger import logger
from supabase import create_client, Client
from redis import Redis
import logging

# from services.track_replies import GmailService
from datetime import datetime
from services.vector_service import VectorService
from services.meeting_analyzer import MeetingAnalyzer
from services.llm_service import LLMService
from services.email_discovery_service import EmailDiscoveryService
from services.scraper_router_service import ScraperRouterService
from services.follow_up_sequence_service import FollowUpSequenceService


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

PLACEHOLDER_CONTENT