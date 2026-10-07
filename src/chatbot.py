from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from .config import CHAT_MODEL
from .courses import load_courses, find_courses
from .rag import search


class QueryPlan(BaseModel):
    route: Literal[
        "website",
        "courses",
        "mixed"
    ]

    semantic_query: str = ""

    slot: str | None = None

    exclude_days: list[str] = Field(
        default_factory=list
    )

    include_days: list[str] = Field(
        default_factory=list
    )

    semester: str | None = None


planner = ChatOpenAI(
    model=CHAT_MODEL,
    # temperature=0,
)

structured_planner = planner.with_structured_output(
    QueryPlan
)


PLANNER_PROMPT = """
You are the query planner for IIT Bombay ENTREPRENEURSHIP department (DSSE) chatbot.

The chatbot has:
1. A vector database containing department website
   documents and course documents.
2. Structured course JSON data that can perform exact
   filtering.

Decide what information is required to answer the user's
question.

Use:
- website for department/general information
- courses for course-related questions
- mixed when both are required

For semantic_query, write a concise search query that
captures the user's information need.

For course constraints:
- slot should contain an explicitly requested slot.
- exclude_days should contain days the student says they
  cannot attend.
- include_days should contain days explicitly requested.
- Do not invent constraints.
- Do not assume student eligibility unless the user provides
  it or the data explicitly supports it.

Important:
"busy on Tuesday" means courses with Tuesday classes should
be excluded.

User question:
{question}
"""


def plan_query(question):
    prompt = PLANNER_PROMPT.format(
        question=question
    )

    return structured_planner.invoke(prompt)


ANSWER_PROMPT = """
You are an IIT Bombay ENTREPRENEURSHIP department (DSSE) information assistant.

Answer the user's question using ONLY the supplied evidence.

Rules:
- Do not invent information.
- If the evidence is insufficient, say so.
- For course results, clearly mention the semester when
  relevant.
- Do not claim that a student is eligible for a course unless
  the evidence establishes eligibility.
- If exact course filtering was performed, explain the
  important filters briefly.
- Give a direct answer rather than discussing the internal
  retrieval process.

User question:
{question}

Evidence:
{evidence}
"""


answer_llm = ChatOpenAI(
    model=CHAT_MODEL,
    # temperature=0,
)


def generate_answer(question, evidence):
    prompt = ANSWER_PROMPT.format(
        question=question,
        evidence=evidence,
    )

    response = answer_llm.invoke(prompt)

    return response.content


def format_documents(documents):
    parts = []

    for document in documents:
        parts.append(
            f"""
SOURCE TYPE: {document.metadata.get("type")}
SOURCE: {document.metadata.get("source")}

{document.page_content}
""".strip()
        )

    return "\n\n---\n\n".join(parts)


def format_courses(courses):
    parts = []

    for course in courses:
        offering = course.get("offering", {})
        basic = course.get("basic_info", {})

        schedule = ", ".join(
            f'{item.get("day")} '
            f'{item.get("start")}-{item.get("end")}'
            for item in offering.get("schedule", [])
        )

        parts.append(
            f"""
Course: {course.get("course_code")} -
{course.get("course_name")}

Semester: {course.get("_semester")}
Credits: {basic.get("total_credits")}
Type: {basic.get("type")}
Slot: {offering.get("slot")}
Instructor(s): {", ".join(offering.get("instructors", []))}
Schedule: {schedule}
Description:
{course.get("course_details", {}).get("text_reference", "")}
""".strip()
        )

    return "\n\n---\n\n".join(parts)


def answer_question(question):
    plan = plan_query(question)

    evidence_parts = []

    if plan.route in ("website", "mixed"):
        documents = search(
            plan.semantic_query,
            k=6,
            source_type="website",
        )

        if documents:
            evidence_parts.append(
                format_documents(documents)
            )

    if plan.route in ("courses", "mixed"):
        documents = search(
            plan.semantic_query,
            k=8,
            source_type="course",
        )

        if documents:
            evidence_parts.append(
                format_documents(documents)
            )

        courses = load_courses()

        filtered_courses = find_courses(
            courses,
            slot=plan.slot,
            exclude_days=plan.exclude_days,
            include_days=plan.include_days,
            semester=plan.semester,
        )

        if filtered_courses:
            evidence_parts.append(
                "EXACT COURSE FILTER RESULTS:\n\n"
                + format_courses(filtered_courses)
            )

    evidence = "\n\n========\n\n".join(
        evidence_parts
    )

    if not evidence:
        evidence = "No relevant evidence was found."

    return generate_answer(
        question,
        evidence,
    )

def get_response(question, history=None):
    return answer_question(question)