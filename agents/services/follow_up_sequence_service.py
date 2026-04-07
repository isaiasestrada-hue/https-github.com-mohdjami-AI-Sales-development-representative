from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from typing import TypedDict
import json
from langchain_core.messages import SystemMessage, HumanMessage

from .llm_service import LLMService
from core.logger import logger


# ---------------------------------------------------------------------------
# State & type definitions
# ---------------------------------------------------------------------------

TOUCH_ANGLES = {
    1: "Value Reinforcement",
    2: "Social Proof / Case Study",
    3: "New Insight or Resource",
    4: "Direct Ask",
    5: "Breakup Email",
}


class SequenceState(TypedDict):
    prospect: Dict
    initial_email: Optional[Dict]
    reply_received: Optional[str]
    deal_stage: str
    num_touches: int
    product_context: str
    current_touch: int
    emails: List[Dict]
    strategy: str
    completed: bool


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class FollowUpSequenceService:
    """
    Generates a personalised multi-touch follow-up email sequence using a
    LangGraph workflow.

    Workflow nodes:
      plan_strategy  → generate_touch → [loop back or finish]

    Each touch targets a different angle (value, proof, insight, ask, breakup).
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.workflow = self._build_workflow()

    # ------------------------------------------------------------------ #
    # Workflow construction                                                #
    # ------------------------------------------------------------------ #

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(SequenceState)

        workflow.add_node("plan_strategy", self._plan_strategy_node)
        workflow.add_node("generate_touch", self._generate_touch_node)

        workflow.set_entry_point("plan_strategy")
        workflow.add_edge("plan_strategy", "generate_touch")

        workflow.add_conditional_edges(
            "generate_touch",
            self._should_continue,
            {
                "continue": "generate_touch",
                "done": END,
            },
        )

        return workflow.compile()

    # ------------------------------------------------------------------ #
    # Routing helper                                                       #
    # ------------------------------------------------------------------ #

    def _should_continue(self, state: SequenceState) -> str:
        if state["current_touch"] < state["num_touches"]:
            return "continue"
        return "done"

    # ------------------------------------------------------------------ #
    # Nodes                                                                #
    # ------------------------------------------------------------------ #

    async def _plan_strategy_node(self, state: SequenceState) -> SequenceState:
        """Analyse the prospect context and decide the overall sequence strategy."""
        try:
            prospect = state["prospect"]
            messages = [
                SystemMessage(content=(
                    "You are an expert B2B sales strategist. "
                    "Given the prospect context, write a one-paragraph strategy "
                    "for a follow-up email sequence. Focus on the key angle, "
                    "tone, and unique value hook. "
                    "Respond ONLY with the strategy text — no JSON, no headers."
                )),
                HumanMessage(content=(
                    f"Prospect: {prospect.get('author') or prospect.get('name', 'Unknown')}\n"
                    f"Role: {prospect.get('role', 'Unknown')}\n"
                    f"Company: {prospect.get('company', 'Unknown')}\n"
                    f"Industry: {prospect.get('industry', '')}\n"
                    f"Pain points: {', '.join(prospect.get('pain_points', []))}\n"
                    f"Solution fit: {prospect.get('solution_fit', '')}\n"
                    f"Deal stage: {state['deal_stage']}\n"
                    f"Reply received: {state['reply_received'] or 'None'}\n"
                    f"Touches planned: {state['num_touches']}\n"
                    f"Product context: {state['product_context']}\n"
                )),
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            state["strategy"] = response.content.strip()
            logger.info("Sequence strategy planned.")
        except Exception as e:
            logger.error(f"Error planning strategy: {e}")
            state["strategy"] = "Focus on demonstrating value and driving a meeting."
        return state

    async def _generate_touch_node(self, state: SequenceState) -> SequenceState:
        """Generate the next touch email in the sequence."""
        touch_number = state["current_touch"] + 1
        angle = TOUCH_ANGLES.get(touch_number, "Value Reinforcement")
        prospect = state["prospect"]

        try:
            previous_emails_summary = ""
            if state["emails"]:
                subjects = [e["subject"] for e in state["emails"]]
                previous_emails_summary = (
                    f"Previous subjects sent: {'; '.join(subjects)}"
                )

            messages = [
                SystemMessage(content=(
                    "You are an expert B2B sales email writer. "
                    f"Write touch #{touch_number} of a {state['num_touches']}-part follow-up sequence. "
                    f"This email's angle is: **{angle}**.\n\n"
                    "Rules:\n"
                    "- Keep it under 120 words\n"
                    "- Sound human, not templated\n"
                    "- Reference the prospect's specific pain points\n"
                    "- Include one clear call-to-action\n"
                    "- Do NOT repeat the same angle as prior emails\n\n"
                    "Respond ONLY with valid JSON:\n"
                    '{"subject": "...", "content": "..."}'
                )),
                HumanMessage(content=(
                    f"Overall strategy: {state['strategy']}\n\n"
                    f"Prospect: {prospect.get('author') or prospect.get('name', 'Unknown')}\n"
                    f"Role: {prospect.get('role', 'Unknown')}\n"
                    f"Company: {prospect.get('company', 'Unknown')}\n"
                    f"Industry: {prospect.get('industry', '')}\n"
                    f"Pain points: {', '.join(prospect.get('pain_points', []))}\n"
                    f"Solution fit: {prospect.get('solution_fit', '')}\n"
                    f"Deal stage: {state['deal_stage']}\n"
                    f"Reply received: {state['reply_received'] or 'None'}\n"
                    f"{previous_emails_summary}\n"
                    f"Product context: {state['product_context']}\n"
                )),
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            raw = response.content.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            email = json.loads(raw)
            email["touch_number"] = touch_number
            email["angle"] = angle
            state["emails"].append(email)
            logger.info(f"Generated touch #{touch_number}: {email['subject']}")

        except Exception as e:
            logger.error(f"Error generating touch #{touch_number}: {e}")
            state["emails"].append({
                "touch_number": touch_number,
                "angle": angle,
                "subject": f"Following up — touch {touch_number}",
                "content": (
                    f"Hi {prospect.get('author') or prospect.get('name', 'there')},\n\n"
                    "I wanted to follow up on my previous note. "
                    "Would you be open to a quick call to explore how we can help?\n\n"
                    "Best,\n[Your Name]"
                ),
            })

        state["current_touch"] = touch_number
        return state

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def generate_sequence(
        self,
        prospect: Dict,
        initial_email: Optional[Dict] = None,
        reply_received: Optional[str] = None,
        deal_stage: str = "new",
        num_touches: int = 3,
        product_context: str = "",
    ) -> Dict[str, Any]:
        """
        Run the LangGraph workflow and return the full sequence.

        Returns:
            {
                "strategy": str,
                "emails": [
                    {
                        "touch_number": int,
                        "angle": str,
                        "subject": str,
                        "content": str
                    },
                    ...
                ]
            }
        """
        initial_state: SequenceState = {
            "prospect": prospect,
            "initial_email": initial_email,
            "reply_received": reply_received,
            "deal_stage": deal_stage,
            "num_touches": num_touches,
            "product_context": product_context,
            "current_touch": 0,
            "emails": [],
            "strategy": "",
            "completed": False,
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)
            return {
                "strategy": final_state["strategy"],
                "emails": final_state["emails"],
            }
        except Exception as e:
            logger.error(f"Workflow error in FollowUpSequenceService: {e}")
            raise
