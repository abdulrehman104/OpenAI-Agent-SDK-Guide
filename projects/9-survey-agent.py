import os
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")


client = AsyncOpenAI(api_key=GEMINI_API_KEY,
                     base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash", openai_client=client)
set_tracing_disabled(True)


class Satisfaction(str, Enum):
    very_satisfied = "very_satisfied"
    satisfied = "satisfied"
    neutral = "neutral"
    dissatisfied = "dissatisfied"


class QuestionResponse(BaseModel):
    question_id: str
    answer: Optional[str]
    rating: Optional[Satisfaction]


class SurveyResult(BaseModel):
    respondent_id: str
    responses: List[QuestionResponse]


agent = Agent(
    name="SurveyAgent",
    instructions=(
        "Convert the following chat transcript into a SurveyResult JSON: "
        "extract respondent_id, each question_id, the free-form answer, or the selected rating."
    ),
    model=model,
    output_type=SurveyResult
)

transcript = """
User: My ID is user_789.
Answer: Question 1: How do you rate our service? (very_satisfied/satisfied/neutral/dissatisfied)
User: I would say very_satisfied.
Answer: Question 2: Any further comments?
User: No, everything was great.
"""

result = Runner.run_sync(agent, transcript)
survey: SurveyResult = result.final_output

print("Survey Result:")
print(survey)

# Display the survey resultz
print("\nResponses:")
print(f"Respondent: {survey.respondent_id}")

print("Question Responses:")
for resp in survey.responses:
    print(f"{resp.question_id} → rating={resp.rating}, answer={resp.answer}")
