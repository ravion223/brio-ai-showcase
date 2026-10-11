import concurrent.futures
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from openai import OpenAI
from django.conf import settings

# Note: This is an isolated snippet from the Brio AI backend demonstrating 
# OpenAI Structured Outputs for categorization fallback, parallel dual-prompt AI insights
# (UI Assistant Insights + Formal PDF Auditor Summary), and predictive forecasting.

UK_MONTHS = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


class AIFallbackResponse(BaseModel):
    class MerchantMapping(BaseModel):
        merchant_name: str
        category_name: str
    mapping: List[MerchantMapping]


class AIAssistantInsightsResponse(BaseModel):
    assistant_insights: List[str]


class AIFormalSummaryResponse(BaseModel):
    formal_summary: str


class BrioDataService:
    @staticmethod
    def _fetch_assistant_insights(client: OpenAI, system_prompt: str, user_content: str) -> List[str]:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.7,  # Higher temperature for creative, empathetic insights
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=AIAssistantInsightsResponse
        )
        return completion.choices[0].message.parsed.assistant_insights

    @staticmethod
    def _fetch_formal_summary(client: OpenAI, system_prompt: str, user_content: str) -> str:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for factual, concise synthesis
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=AIFormalSummaryResponse
        )
        return completion.choices[0].message.parsed.formal_summary

    @classmethod
    def generate_ai_analysis(
        cls,
        transactions: list,
        user_goal: str,
        total_spent: float,
        unknown_merchants: Optional[Set[str]] = None,
        category_sums: Optional[List[Dict[str, Any]]] = None,
        target_language: str = "Ukrainian",
        currency_code: str = "UAH"
    ):
        """
        Sends cleaned transactions and user's goal to OpenAI and returns 
        strictly structured JSON for the frontend, executing dual-prompt 
        generation (Assistant Insights & Formal Auditor Summary) in parallel.
        """
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        ai_category_map = {}
        assistant_insights = []
        formal_summary = ""
        is_ukrainian = (target_language == "Ukrainian")
        category_sums = category_sums or []

        try:
            # 1. Micro-Request to AI for uncategorized merchants (AI-Generated Fallback)
            if unknown_merchants:
                fallback_system_prompt = (
                    "You are a financial categorizer. Map the following merchant names to strictly "
                    "one of the standard categories. Extract the clean core brand name or keyword."
                )
                fallback_user_content = "\n".join(unknown_merchants)
                
                fallback_completion = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    temperature=0.1,  # Low temperature for deterministic mapping
                    messages=[
                        {"role": "system", "content": fallback_system_prompt},
                        {"role": "user", "content": fallback_user_content}
                    ],
                    response_format=AIFallbackResponse
                )
                ai_data = fallback_completion.choices[0].message.parsed
                ai_category_map = {m.merchant_name.strip().lower(): m.category_name for m in ai_data.mapping}

            # 2. Parallel Dual-Prompt Generation: UI Assistant Insights & Formal Auditor Summary
            if user_goal and user_goal.strip():
                goal_context = f"User financial goal: {user_goal}"
                goal_rule = (
                    "CRITICAL GOAL RULE: If the user's goal mentions a specific currency, preserve it. "
                    f"DO NOT blindly apply {currency_code} to their goal amount. "
                    "Frame advice around saving percentages.\n"
                )
            else:
                goal_context = "User financial goal: General budget optimization and saving money."
                goal_rule = ""

            # Prompt 1 (UI Assistant)
            assistant_system_prompt = (
                "You are Brio, an elite financial assistant and predictive analyst. "
                "Your task is to analyze the user's transaction history and provide deep, actionable insights "
                "tailored to their specific financial goal. "
                "You give EXACTLY 4 brilliant, highly direct assistant insights.\n "
                f"LANGUAGE RULE: You MUST generate your ENTIRE JSON RESPONSE strictly in {target_language}.\n"
                f"{goal_rule}\n"
                "Be pragmatic, witty, and deeply analytical.\n\n"
                "CRITICAL RULES FOR `assistant_insights` GENERATION:\n"
                "1. NO ABSOLUTE NUMBERS: NEVER use exact sums, amounts, or currency values in your insights.\n"
                "2. FOCUS ON BEHAVIOR: Analyze purchasing patterns, frequency, and habits.\n"
                "3. MENTION VENDORS: Make insights personalized by mentioning specific popular vendors from the dataset.\n"
                "4. USE RELATIVE TERMS: Use words like 'significant portion', 'frequent', 'rarely'.\n"
                "5. ACTIONABLE ADVICE: Give psychological or practical tips on how to optimize these specific habits based on the user's goal.\n"
                "6. STRICTLY DATA-DRIVEN: Your insights MUST be derived STRICTLY from the real transactions provided in this request.\n"
                "7. TONE AND EMPATHY: NEVER shame, judge, or lecture the user. Frame your insights as a supportive financial partner."
            )
            assistant_user_content = f"{goal_context}\n\nTransactions Data: {transactions}"

            # Prompt 2 (PDF Auditor)
            auditor_system_prompt = (
                "You are an objective, highly factual Financial Auditor. "
                "Your task is to provide a high-level Executive Summary of this financial period in a single, concise formal paragraph (3-4 sentences max). "
                "Do NOT just list out the category totals (the reader can already see the table). Instead, synthesize the data. "
                "CRITICAL RULES: "
                "1. NO REDUNDANCY: Do not just read off the categories and their sums. "
                "2. FOCUS ON SYNTHESIS: Identify spending concentration (e.g., 'The majority of expenditure was highly concentrated in essential categories...'), describe the overall character of the period, and specifically highlight the 1-2 largest single transactions or vendors that drove the volume. "
                "3. CURRENCY: Always format money with the provided base currency (e.g., '1,200 UAH'). Never hallucinate '$' or '€' unless explicitly instructed. "
                "4. DO NOT CALCULATE MATH: Use the provided category totals to guide your understanding, but avoid doing calculations yourself. "
                "5. TONE: 3rd-person, objective, factual, zero advice. "
                "6. NO 'USER': NEVER use the word 'user' (e.g., 'the user's spending'). Refer to it objectively as 'The spending', 'This period's expenditure', or 'The financial activity'. "
                f"LANGUAGE RULE: You MUST generate your response strictly in {target_language}."
            )
            auditor_user_content = f"Base Currency: {currency_code}\nExact Category Totals: {category_sums}\n\nRaw Transactions Data: {transactions}"

            # Run both requests concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_assistant = executor.submit(cls._fetch_assistant_insights, client, assistant_system_prompt, assistant_user_content)
                future_formal = executor.submit(cls._fetch_formal_summary, client, auditor_system_prompt, auditor_user_content)

                assistant_insights = future_assistant.result(timeout=15)
                formal_summary = future_formal.result(timeout=15)

        except Exception as e:
            # In production, this would log to Sentry or internal logger
            print(f"OpenAI API Error: {str(e)}")
            assistant_insights = ["Unable to generate insights at this time. Please try again later."]
            formal_summary = "Financial summary is currently unavailable. Please try again later."

        # 3. Formulate data for the frontend's 6-month Predictive Analytics Tree with localized months
        predictive_trend = []
        base_current = float(total_spent)
        current_date = datetime.now()
        month_names = UK_MONTHS if is_ukrainian else EN_MONTHS

        for i in range(6):
            target_date = current_date + relativedelta(months=i)
            month_label = f"{month_names[target_date.month - 1]} {target_date.year}"

            noise_current = random.uniform(-0.02, 0.02)
            month_current = base_current * (1 + noise_current)

            if i == 0:
                discount_rate = 0.015
            elif i in [1, 2]:
                discount_rate = 0.03
            elif i in [3, 4]:
                discount_rate = 0.05
            else:
                discount_rate = 0.07

            month_optimized = month_current * (1 - discount_rate)

            predictive_trend.append({
                "month": month_label,
                "current": round(month_current, 2),
                "optimized": round(month_optimized, 2)
            })

        return {
            "success": True,
            "data": {
                "assistant_insights": assistant_insights,
                "formal_summary": formal_summary,
                "predictive_trend": predictive_trend,
                "fallback_mapping": ai_category_map
            }
        }