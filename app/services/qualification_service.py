import os
import json
from groq import Groq
from app.core.config import settings

# Initialize Groq client
client = Groq(api_key=settings.GROQ_API_KEY)

def score_lead(lead_data: dict) -> dict:
    """
    Score a lead using Groq AI based on:
    - Age (55+ preferred)
    - Monthly Income ($3000+ preferred)
    - Health Requirements (minor/none preferred)
    - Desired Country (clear preference)
    - Timeline (soon preferred)
    
    Returns: {
        "score": "Hot" | "Warm" | "Cold",
        "reasoning": "Explanation of the score"
    }
    """
    
    # Build the prompt
    prompt = f"""
You are an AI assistant for Retirees Paradise, a retirement relocation company. 
Score the following lead as Hot, Warm, or Cold based on these criteria:

CRITERIA:
1. Age: 55+ is better. Under 50 is less ideal.
2. Monthly Income: $3,000+ is better. Under $2,000 is less ideal.
3. Health Requirements: None or minor is better. Major/serious is less ideal.
4. Desired Country: If they have a specific country in mind, that's better. "Not sure" is less ideal.
5. Timeline: Sooner (0-3 months) is better. Later (1+ years) is less ideal.

LEAD DATA:
- Name: {lead_data.get('name', 'Unknown')}
- Age: {lead_data.get('age', 'Not provided')}
- Monthly Income: ${lead_data.get('monthly_income', 'Not provided')}
- Health Requirements: {lead_data.get('medical_requirements', 'None')}
- Desired Country: {lead_data.get('desired_country', 'Not sure')}
- Timeline: {lead_data.get('timeline', 'Not provided')}

Respond in this exact JSON format ONLY:
{{
    "score": "Hot" or "Warm" or "Cold",
    "reasoning": "Brief explanation of why this lead got this score. Mention the key factors."
}}

Do not include any other text. Only return the JSON.
"""
    
    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Good quality model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that scores retirement leads."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        # Parse the response
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        try:
            result = json.loads(result_text)
            return {
                "score": result.get("score", "Cold"),
                "reasoning": result.get("reasoning", "No reasoning provided")
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, extract score from text
            if "Hot" in result_text:
                score = "Hot"
            elif "Warm" in result_text:
                score = "Warm"
            else:
                score = "Cold"
            
            return {
                "score": score,
                "reasoning": result_text[:500]  # Truncate
            }
            
    except Exception as e:
        # Fallback: Rule-based scoring if AI fails
        return fallback_score(lead_data)

def fallback_score(lead_data: dict) -> dict:
    """Simple rule-based scoring fallback if AI fails"""
    points = 0
    reasoning = []
    
    # Age: 55+ = 2 points, 50-54 = 1 point
    age = lead_data.get('age')
    if age:
        if age >= 55:
            points += 2
            reasoning.append("Age 55+ (ideal)")
        elif age >= 50:
            points += 1
            reasoning.append("Age 50-54 (good)")
        else:
            reasoning.append("Age under 50 (less ideal)")
    
    # Income: $3000+ = 2 points, $2000-2999 = 1 point
    income = lead_data.get('monthly_income')
    if income:
        if income >= 3000:
            points += 2
            reasoning.append("Income $3,000+ (ideal)")
        elif income >= 2000:
            points += 1
            reasoning.append("Income $2,000-$2,999 (good)")
        else:
            reasoning.append("Income under $2,000 (less ideal)")
    
    # Health: None/minor = 2 points
    health = lead_data.get('medical_requirements', '')
    if health and len(health) > 0:
        if "none" in health.lower() or "minor" in health.lower():
            points += 2
            reasoning.append("Minor/none health requirements (ideal)")
        elif "major" in health.lower() or "serious" in health.lower():
            points += 0
            reasoning.append("Major health requirements (less ideal)")
        else:
            points += 1
            reasoning.append("Health requirements (moderate)")
    
    # Determine score based on points
    if points >= 5:
        score = "Hot"
    elif points >= 3:
        score = "Warm"
    else:
        score = "Cold"
    
    reasoning_text = "; ".join(reasoning) if reasoning else "No clear indicators"
    
    return {
        "score": score,
        "reasoning": f"{reasoning_text} (Score: {points}/6)"
    }