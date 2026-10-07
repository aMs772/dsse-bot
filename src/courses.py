import json
from pathlib import Path

from .config import COURSES_DIR


def load_courses():
    courses = []

    for path in COURSES_DIR.rglob("*.json"):
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        metadata = data.get("metadata", {})

        semester = (
            f'{metadata.get("year")}-sem'
            f'{metadata.get("semester")}'
        )

        for course in data.get("courses", []):
            course["_semester"] = semester
            courses.append(course)

    return courses


def find_courses(
    courses,
    slot=None,
    exclude_days=None,
    include_days=None,
    semester=None,
):
    exclude_days = {
        day.lower()
        for day in (exclude_days or [])
    }

    include_days = {
        day.lower()
        for day in (include_days or [])
    }

    results = []

    for course in courses:
        offering = course.get("offering", {})

        if semester:
            if course["_semester"] != semester:
                continue

        if slot:
            if offering.get("slot", "").lower() != slot.lower():
                continue

        schedule = offering.get("schedule", [])

        course_days = {
            item.get("day", "").lower()
            for item in schedule
        }

        # Example:
        # "I'm busy Tuesday"
        # means courses having Tuesday classes are removed.
        if exclude_days & course_days:
            continue

        if include_days:
            if not include_days.issubset(course_days):
                continue

        results.append(course)

    return results