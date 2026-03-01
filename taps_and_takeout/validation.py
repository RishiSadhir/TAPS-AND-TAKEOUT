from datetime import datetime


EVENT_TITLE_MAX = 80
EVENT_DESCRIPTION_MAX = 400
SECTION_NAME_MAX = 60
ITEM_NAME_MAX = 80
ITEM_DESCRIPTION_MAX = 400


def sanitize_text(value, allow_newlines=False):
    value = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = []
    for char in value:
        if char == "\n" and allow_newlines:
            cleaned.append(char)
        elif char == "\t":
            cleaned.append(" ")
        elif ord(char) >= 32:
            cleaned.append(char)
    return "".join(cleaned).strip()


def validate_event_form(title, date_str, description, pinned):
    title = sanitize_text(title)
    description = sanitize_text(description, allow_newlines=True)
    errors = {}

    if not title:
        errors["title"] = "Title is required."
    elif len(title) > EVENT_TITLE_MAX:
        errors["title"] = f"Title must be {EVENT_TITLE_MAX} characters or fewer."

    if len(description) > EVENT_DESCRIPTION_MAX:
        errors["description"] = f"Description must be {EVENT_DESCRIPTION_MAX} characters or fewer."

    if not pinned:
        try:
            datetime.strptime(date_str or "", "%Y-%m-%d")
        except ValueError:
            errors["date"] = "Enter a valid date."

    return {
        "title": title,
        "date": date_str or "",
        "description": description,
        "pinned": pinned,
    }, errors


def validate_section_form(section_name):
    section_name = sanitize_text(section_name)
    errors = {}
    if not section_name:
        errors["section_name"] = "Section name is required."
    elif len(section_name) > SECTION_NAME_MAX:
        errors["section_name"] = f"Section name must be {SECTION_NAME_MAX} characters or fewer."
    return {"section_name": section_name}, errors


def validate_item_form(item_name, item_description):
    item_name = sanitize_text(item_name)
    item_description = sanitize_text(item_description, allow_newlines=True)
    errors = {}
    if not item_name:
        errors["item_name"] = "Item name is required."
    elif len(item_name) > ITEM_NAME_MAX:
        errors["item_name"] = f"Item name must be {ITEM_NAME_MAX} characters or fewer."

    if len(item_description) > ITEM_DESCRIPTION_MAX:
        errors["item_description"] = f"Description must be {ITEM_DESCRIPTION_MAX} characters or fewer."

    return {
        "item_name": item_name,
        "item_description": item_description,
    }, errors
