"""
Module for rendering more complicated HTML templates using jinja2.
"""

import enum

import jinja2

import settings


def render(name, **data):
    """
    Render an HTML template using jinja2 and return the HTML as a string.
    """
    loader = jinja2.FileSystemLoader(settings.TEMPLATES_FILEPATH)
    env = jinja2.Environment(loader=loader)
    template = env.get_template(name)
    # remove newlines and tabs to clean up the HTML data
    return template.render(data).replace("\n", "").replace("\t", "")


def load_summarize_template(long_content: str, relevant_question: str) -> str:
    """
    Prompt designed for gpt-3.5 to summarize some arbitrarily long
    content into bullet-points relevant to answering the given question.
    """
    return render(
        "backend/prompts/summarize.html",
        {
            "long_content": long_content,
            "relevant_question": relevant_question,
        },
    )


def load_system_template(
    personality: str,
    knowledge: str,
) -> str:
    """
    Prompt designed for gpt-4 to generate a response in the tone of
    sambot's personality, using a summarized version of the sambot memories.
    """
    return render(
        "backend/prompts/system.html",
        {
            "personality": personality,
            "knowledge": knowledge,
        },
    )


def load_is_greeting_template(user_content: str) -> str:
    """
    Prompt designed for gpt-3.5 to generate a "yes" or "no" answer depending on
    whether the user content merits a greeting in response.
    """
    render("backend/prompts/is_greeting.html", {"user_content": user_content})


def load_is_asking_for_resume_tempalte(user_content: str) -> str:
    """
    Prompt designed for gpt-3.5 to generate a "yes" or "no" answer depending
    on whether the user is asking to be sent an email containing my resume.
    """
    render("backend/prompts/is_asking_for_resume.html", {"user_content": user_content})
