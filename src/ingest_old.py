import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

import chromadb

from .config import (
    CHROMA_DIR,
    COURSES_DIR,
    EMBEDDING_MODEL,
    WEBSITE_DIR,
)


COLLECTION_NAME = "iitb_department"


def create_embeddings():
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )


# def create_vector_store():
#     embeddings = create_embeddings()

#     return Chroma(
#         collection_name=COLLECTION_NAME,
#         embedding_function=embeddings,
#         persist_directory=str(CHROMA_DIR),
#     )

def create_vector_store():
    embeddings = create_embeddings()

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

def reset_vector_store():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass


def load_website_documents():
    documents = []

    for path in WEBSITE_DIR.rglob("*.md"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "type": "website",
                    "source": str(path.relative_to(WEBSITE_DIR)),
                },
            )
        )

    return documents


def course_to_text(course, semester_name):
    basic = course.get("basic_info", {})
    offering = course.get("offering", {})
    details = course.get("course_details", {})

    instructors = ", ".join(
        offering.get("instructors", [])
    )

    schedule = offering.get("schedule", [])

    schedule_text = "\n".join(
        f"{item.get('day')} {item.get('start')}-{item.get('end')}"
        for item in schedule
    )

    return f"""
Course Code: {course.get("course_code")}
Course Name: {course.get("course_name")}

Semester: {semester_name}

Credits: {basic.get("total_credits")}
Course Type: {basic.get("type")}

Description:
{details.get("text_reference", "")}

Instructors:
{instructors}

Slot:
{offering.get("slot")}

Schedule:
{schedule_text}

Venue:
{offering.get("venue")}

Course Content Category:
{offering.get("course_content_category")}
""".strip()


def load_course_documents():
    documents = []

    for path in COURSES_DIR.rglob("*.json"):
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        metadata = data.get("metadata", {})

        semester_name = (
            f'{metadata.get("year")}-sem'
            f'{metadata.get("semester")}'
        )

        for course in data.get("courses", []):
            text = course_to_text(
                course,
                semester_name
            )

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "type": "course",
                        "course_code": course.get(
                            "course_code"
                        ),
                        "semester": semester_name,
                        "source": str(
                            path.relative_to(COURSES_DIR)
                        ),
                    },
                )
            )

    return documents


# def ingest():
#     vector_store = create_vector_store()

#     website_docs = load_website_documents()
#     course_docs = load_course_documents()

#     documents = website_docs + course_docs

#     print(
#         f"Found {len(website_docs)} website documents."
#     )

#     print(
#         f"Found {len(course_docs)} course documents."
#     )

#     if not documents:
#         print("No documents found.")
#         return

#     # Simple approach for now:
#     # recreate the collection from the current source files.
#     vector_store.reset_collection()

#     vector_store.add_documents(documents)

#     print(
#         f"Added {len(documents)} documents to Chroma."
#     )

def ingest():
    reset_vector_store()

    vector_store = create_vector_store()

    website_docs = load_website_documents()
    course_docs = load_course_documents()

    documents = website_docs + course_docs

    print(f"Found {len(website_docs)} website documents.")
    print(f"Found {len(course_docs)} course documents.")

    if not documents:
        print("No documents found.")
        return

    vector_store.add_documents(documents)

    print(f"Added {len(documents)} documents to Chroma.")

if __name__ == "__main__":
    ingest()