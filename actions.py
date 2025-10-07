from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


def _extract_amount(value: Text) -> Optional[float]:
    """Convert a user supplied string into a positive float if possible."""

    if not value:
        return None

    matches = re.findall(r"-?\d[\d,]*(?:\.\d+)?", value)
    if not matches:
        return None

    numeric_text = matches[0].replace(",", "")
    try:
        amount = float(numeric_text)
    except ValueError:
        return None

    if amount <= 0:
        return None

    return amount


class ValidateFinancialWellnessForm(FormValidationAction):
    """Validates user responses for the financial wellness form."""

    def name(self) -> Text:
        return "validate_financial_wellness_form"

    async def extract_income(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        value = tracker.latest_message.get("text")
        amount = _extract_amount(value or "")
        if amount is None:
            dispatcher.utter_message(
                text="I didn't quite catch the income amount. Could you share your average monthly take-home pay?"
            )
            return {"income": None}
        return {"income": f"{amount:.2f}"}

    async def extract_expenses(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        value = tracker.latest_message.get("text")
        amount = _extract_amount(value or "")
        if amount is None:
            dispatcher.utter_message(
                text="Thanks. About how much do you usually spend on essentials each month?"
            )
            return {"expenses": None}
        return {"expenses": f"{amount:.2f}"}

    async def extract_savings_goal(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        value = tracker.latest_message.get("text") or ""
        amount = _extract_amount(value)
        if amount is not None:
            return {"savings_goal": f"{amount:.2f}"}
        cleaned = value.strip()
        if not cleaned:
            dispatcher.utter_message(
                text="It's helpful to have a target. What amount are you aiming to save?"
            )
            return {"savings_goal": None}
        return {"savings_goal": cleaned}

    async def extract_risk_tolerance(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        value = (tracker.latest_message.get("text") or "").strip().lower()
        if not value:
            dispatcher.utter_message(
                text="No worries—how much risk are you comfortable taking with investments? Conservative, moderate, or aggressive?"
            )
            return {"risk_tolerance": None}

        aliases = {
            "low": "conservative",
            "low risk": "conservative",
            "risk averse": "conservative",
            "cautious": "conservative",
            "medium": "moderate",
            "balanced": "moderate",
            "medium risk": "moderate",
            "high": "aggressive",
            "high risk": "aggressive",
            "growth oriented": "aggressive",
        }

        normalized = aliases.get(value, value)
        allowed = {"conservative", "moderate", "aggressive"}
        if normalized not in allowed:
            dispatcher.utter_message(
                text="Please let me know if your risk tolerance is conservative, moderate, or aggressive."
            )
            return {"risk_tolerance": None}
        return {"risk_tolerance": normalized}


class ActionProvideFinancialSummary(Action):
    """Summarises the user's financial profile and suggests next steps."""

    def name(self) -> Text:
        return "action_provide_financial_summary"

    @staticmethod
    def _to_float(value: Optional[Text]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        income = self._to_float(tracker.get_slot("income"))
        expenses = self._to_float(tracker.get_slot("expenses"))
        savings_goal_slot = tracker.get_slot("savings_goal")
        risk_tolerance = tracker.get_slot("risk_tolerance")

        savings_goal = self._to_float(savings_goal_slot)

        messages: List[str] = []

        if income and expenses:
            discretionary = income - expenses
            if discretionary < 0:
                messages.append(
                    "It looks like your essential spending exceeds your income. Review your fixed costs and see where you can trim or renegotiate bills."
                )
            else:
                savings_rate = discretionary / income * 100
                messages.append(
                    f"After covering essentials you have about ${discretionary:,.2f} left over each month ({savings_rate:,.1f}% of your income). Consider sending part of that straight to savings."
                )

            emergency_target = expenses * 3
            messages.append(
                f"Aim for an emergency fund of roughly ${emergency_target:,.2f}, which represents three months of your core expenses."
            )
        else:
            messages.append(
                "Tracking your monthly income and essential expenses will show how much you can safely save or invest."
            )

        if savings_goal is not None and income and expenses and (income - expenses) > 0:
            monthly_capacity = income - expenses
            months = savings_goal / monthly_capacity
            messages.append(
                f"At your current pace, you could reach your ${savings_goal:,.2f} goal in about {months:,.1f} months."
            )
        elif isinstance(savings_goal_slot, str) and savings_goal is None:
            messages.append(
                f"Keep your \"{savings_goal_slot}\" goal visible—schedule automatic transfers so progress is steady."
            )

        if risk_tolerance:
            if risk_tolerance == "conservative":
                messages.append(
                    "Given a conservative profile, prioritise high-yield savings, certificates of deposit, and a small mix of bond index funds."
                )
            elif risk_tolerance == "moderate":
                messages.append(
                    "A moderate approach can balance stock and bond index funds—consider a 60/40 or 70/30 split depending on your time horizon."
                )
            elif risk_tolerance == "aggressive":
                messages.append(
                    "With an aggressive risk tolerance, you can focus on equity index funds and add international exposure, while keeping a small cash buffer."
                )

        dispatcher.utter_message(text="\n".join(messages))

        return [
            SlotSet("income", tracker.get_slot("income")),
            SlotSet("expenses", tracker.get_slot("expenses")),
            SlotSet("savings_goal", tracker.get_slot("savings_goal")),
            SlotSet("risk_tolerance", tracker.get_slot("risk_tolerance")),
        ]
