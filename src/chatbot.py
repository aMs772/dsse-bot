from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from .config import CHAT_MODEL
from .courses import load_courses, find_courses
from .rag import search


# class QueryPlan(BaseModel):
#     route: Literal[
#         "website",
#         "courses",
#         "mixed"
#     ]

#     semantic_query: str = ""

#     slot: str | None = None

#     exclude_days: list[str] = Field(
#         default_factory=list
#     )

#     include_days: list[str] = Field(
#         default_factory=list
#     )

#     semester: str | None = None


# version 2

class QueryPlan(BaseModel):
    sources: list[
        Literal["website", "courses", "documents"]
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

# version 2

planner = ChatOpenAI(
    model=CHAT_MODEL,
    # temperature=0,
)

structured_planner = planner.with_structured_output(
    QueryPlan
)


# PLANNER_PROMPT = """
# You are the query planner for IIT Bombay ENTREPRENEURSHIP department (DSSE) chatbot.

# The chatbot has:
# 1. A vector database containing department website
#    documents and course documents.
# 2. Structured course JSON data that can perform exact
#    filtering.

# Decide what information is required to answer the user's
# question.

# Use:
# - website for department/general information
# - courses for course-related questions
# - mixed when both are required

# For semantic_query, write a concise search query that
# captures the user's information need.

# For course constraints:
# - slot should contain an explicitly requested slot.
# - exclude_days should contain days the student says they
#   cannot attend.
# - include_days should contain days explicitly requested.
# - Do not invent constraints.
# - Do not assume student eligibility unless the user provides
#   it or the data explicitly supports it.

# Important:
# "busy on Tuesday" means courses with Tuesday classes should
# be excluded.

# User question:
# {question}
# """

# version 2

PLANNER_PROMPT = """
You are the query planner for an IIT Bombay IIC chatbot.

The chatbot has three knowledge sources:

1. website:
   Department website information, including DSSE academics,
   faculty, administration, and contact details.

2. courses:
   Structured course information, including course codes,
   names, slots, instructors, schedules, and semesters.

3. documents:
   PDF and DOCX documents containing information about IIC,
   innovation centres, institute initiatives, procedures,
   and other institutional information.

Select the sources needed to answer the user's question.

Rules:
- Select only the sources relevant to the question.
- Use multiple sources when the question requires them.
- Questions about IIC and innovation centres should generally
  use documents.
- Questions about DSSE department information should generally
  use website.
- Questions about course offerings should generally use courses.
- Questions combining these topics should use multiple sources.
- Do not select courses unless course information is relevant.

For semantic_query, write a concise search query that captures
the user's information need.

For course constraints:
- slot should contain an explicitly requested slot.
- exclude_days should contain days the student says they
  cannot attend.
- include_days should contain days explicitly requested.
- Do not invent constraints.
- Do not assume student eligibility.

Important:
"Busy on Tuesday" means courses with Tuesday classes should
be excluded.

User question:
{question}
"""

# version 2


def plan_query(question):
    prompt = PLANNER_PROMPT.format(
        question=question
    )

    return structured_planner.invoke(prompt)


# ANSWER_PROMPT = 
"""
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

# convo ai

ANSWER_PROMPT = """
You are the IIC (Institute Innovation Council) assistant for IIT Bombay.

Your role is to help students, faculty, researchers, and visitors
understand IIC, innovation centres, institutional initiatives,
DSSE, courses, and other relevant institute information.

PERSONALITY AND TONE:
- Be natural, friendly, intelligent, and conversational.
- Speak like a knowledgeable assistant, not a search engine
  or a document summarizer.
- Use first-person language naturally when appropriate.
- You may say "I can help you with that" or "I don't have
  enough information to answer that confidently."
- Speak on behalf of the information service, but never claim
  to be a human, an institute employee, or an official decision-maker.
- Avoid robotic, overly formal, or unnecessarily technical language.
- You were created by Mohan Satvik Adusumalli (25B1057)


HOW TO ANSWER:
- Answer the question directly and naturally.
- Present information as facts rather than describing where
  you found them.
- Do not repeatedly say "the document says", "according to
  the website", "the provided information states", or similar phrases.
- Do not describe your retrieval process, internal tools,
  vector database, or search results.
- Use simple language and explain technical terms when necessary.
- Organize longer answers with short paragraphs or bullet points.
- Answer only what the user needs; avoid unnecessary introductions
  and repetitive conclusions.
- Adapt your response length to the complexity of the question.

ACCURACY:
- Use ONLY the supplied evidence to answer factual questions.
- Never invent facts, names, contact details, deadlines,
  policies, or institutional information.
- If the evidence does not contain enough information, say so
  naturally and briefly.
- If you can answer part of a question but not all of it,
  answer the supported part and clearly identify what remains
  uncertain.
- Do not claim that a student is eligible for a course unless
  the evidence establishes eligibility.
- When discussing courses, mention the semester when relevant.
- Do not present uncertain information as established fact.

- when asked about DSSE location, the location given in evidence is wrong,
  The correct place is DSSE building besides Central Library
  The location of IIC is conferenc room 5th floor in DSSE building.

CONVERSATION:
- Answer greetings naturally.
- If the user asks what you can do, briefly explain the kinds
  of IIC, innovation-centre, departmental, and course information
  you can help with.
- If the user asks a follow-up question, use the available
  conversation context when provided.
- Do not force first-person pronouns into every answer.
  The goal is natural conversation, not constant use of "I".

CITATIONS AND SOURCES:
- When useful, identify the relevant source document or page
  so the user can verify important information.
- Do not mention sources unnecessarily in ordinary answers.
- Never fabricate a source or reference.

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


# def answer_question(question):
#     plan = plan_query(question)

#     evidence_parts = []

#     if plan.route in ("website", "mixed"):
#         documents = search(
#             plan.semantic_query,
#             k=6,
#             source_type="website",
#         )

#         if documents:
#             evidence_parts.append(
#                 format_documents(documents)
#             )

#     if plan.route in ("courses", "mixed"):
#         documents = search(
#             plan.semantic_query,
#             k=8,
#             source_type="course",
#         )

#         if documents:
#             evidence_parts.append(
#                 format_documents(documents)
#             )

#         courses = load_courses()

#         filtered_courses = find_courses(
#             courses,
#             slot=plan.slot,
#             exclude_days=plan.exclude_days,
#             include_days=plan.include_days,
#             semester=plan.semester,
#         )

#         if filtered_courses:
#             evidence_parts.append(
#                 "EXACT COURSE FILTER RESULTS:\n\n"
#                 + format_courses(filtered_courses)
#             )

#     evidence = "\n\n========\n\n".join(
#         evidence_parts
#     )

#     if not evidence:
#         evidence = "No relevant evidence was found."

#     return generate_answer(
#         question,
#         evidence,
#     )

# version 2
def answer_question(question):
    plan = plan_query(question)

    evidence_parts = []

    # Search selected knowledge sources
    if "website" in plan.sources:
        documents = search(
            plan.semantic_query,
            k=6,
            source_type="website",
        )

        if documents:
            evidence_parts.append(
                format_documents(documents)
            )

    if "documents" in plan.sources:
        documents = search(
            plan.semantic_query,
            k=8,
            source_type="document",
        )

        if documents:
            evidence_parts.append(
                format_documents(documents)
            )

    if "courses" in plan.sources:
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

# version 2
 
 
def get_response(question, history=None):
    return answer_question(question)