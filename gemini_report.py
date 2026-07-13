from google import genai
from google.genai import types


def generate_opportunity_report(company_name: str, aggregated_feedback: str, api_key: str) -> str:
    """
    Sends aggregated employee feedback to Gemini to generate a structured AI opportunity report.
    """
    client = genai.Client(api_key=api_key)

    system_instruction = """
    You are a senior Enterprise AI Strategist. 
    Your objective is to analyze raw employee feedback regarding operational bottlenecks 
    and synthesize it into a strategic, actionable report.
    
    You MUST output the report in valid Markdown format.
    The report MUST begin exactly with the title: '# Custom AI Opportunity Analysis'.
    
    The report MUST include the following sections:
    1. **Executive Summary**: A brief paragraph summarizing the core operational bottlenecks across departments based on the provided feedback.
    2. **High-Impact AI Use Cases**: A bulleted list of EXACTLY 3 high-impact AI use cases customized to solve the specific bottlenecks mentioned by the departments.
    3. **Implementation Matrix**: For each of the 3 use cases, provide a brief estimate of 'Impact (High/Med/Low)' and 'Effort (High/Med/Low)'.
    
    Base all your recommendations ONLY on the provided employee feedback. Be professional, concise, and highly analytical.
    """

    prompt = f"Company: {company_name}\n\nEmployee Bottleneck Feedback:\n{aggregated_feedback}"

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
        )
    )

    return response.text
