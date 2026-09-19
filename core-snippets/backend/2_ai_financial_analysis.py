import random
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
from django.conf import settings

# Note: This is an isolated snippet from the Brio AI backend demonstrating 
# OpenAI Structured Outputs for categorization fallback and mentor insights.

class AIFallbackResponse(BaseModel):
    class MerchantMapping(BaseModel):
        merchant_name: str
        category_name: str
    mapping: List[MerchantMapping]

class AIMentorInsightsResponse(BaseModel):
    mentor_insights: List[str]

class BrioDataService:
    @staticmethod
    def generate_ai_analysis(transactions: list, user_goal: str, total_spent: float, unknown_merchants: set):
        """
        Sends cleaned transactions and user's goal to OpenAI
        and returns strictly structured JSON for the frontend.
        """
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        ai_category_map = {}
        mentor_insights = []
        
        try:
            # 1. Micro-Request to AI for uncategorized merchants (AI-Generated Fallback)
            if unknown_merchants:
                fallback_system_prompt = "You are a financial categorizer. Map the following merchant names to strictly one of these categories..."
                fallback_user_content = "\n".join(unknown_merchants)
                
                fallback_completion = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    temperature=0.1, # Low temperature for deterministic mapping
                    messages=[
                        {"role": "system", "content": fallback_system_prompt},
                        {"role": "user", "content": fallback_user_content}
                    ],
                    response_format=AIFallbackResponse
                )
                ai_data = fallback_completion.choices[0].message.parsed
                ai_category_map = {m.merchant_name.strip().lower(): m.category_name for m in ai_data.mapping}

            # 2. Mentor Insights Request using Structured Output
            insights_system_prompt = "You are Brio, an elite financial mentor and predictive analyst..."
            insights_user_content = f"User financial goal: {user_goal}\n\nTransactions Data: {transactions}"

            insights_completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                temperature=0.7, # Higher temperature for creative insights
                messages=[
                    {"role": "system", "content": insights_system_prompt},
                    {"role": "user", "content": insights_user_content}
                ],
                response_format=AIMentorInsightsResponse
            )
            mentor_insights = insights_completion.choices[0].message.parsed.mentor_insights

        except Exception as e:
            # In production, this would log to Sentry or internal logger
            print(f"OpenAI API Error: {str(e)}")
            mentor_insights = ["Unable to generate insights at this time. Please try again later."]

        # 3. Formulate data for the frontend's 6-month Predictive Analytics Tree
        # Note: Using a statistical approximation formula for the UI visualization baseline.
        predictive_trend = []
        base_current = float(total_spent)
        
        for i in range(6):
            noise_current = random.uniform(-0.02, 0.02)
            month_current = base_current * (1 + noise_current)

            if i == 0: discount_rate = 0.015
            elif i in [1, 2]: discount_rate = 0.03
            elif i in [3, 4]: discount_rate = 0.05
            else: discount_rate = 0.07

            month_optimized = month_current * (1 - discount_rate)

            predictive_trend.append({
                "current": round(month_current, 2),
                "optimized": round(month_optimized, 2)
            })

        return {
            "success": True,
            "data": {
                "mentor_insights": mentor_insights,
                "predictive_trend": predictive_trend,
                "fallback_mapping": ai_category_map
            }
        }