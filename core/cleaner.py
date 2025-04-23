import re
from typing import Tuple, Dict

# Liste personnalisable de titres qu’on veut détecter
SECTION_HEADERS = [
    "introduction", "about", "overview", "background",
    "tokenomics", "token distribution", "economics",
    "technology", "technical architecture", "platform",
    "compliance", "legal", "regulations", "governance",
    "roadmap", "team", "partners", "conclusion"
]

def clean_text(raw_text: str) -> str:
    """
    Clean raw text: remove extra spaces, normalize line breaks, etc.
    Also removes page headers like '--- Page 1 ---'.
    """
    text = raw_text.replace('\r', '')
    text = re.sub(r'^--- Page \d+ ---\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def detect_sections(cleaned_text: str) -> Dict[str, str]:
    """
    Detect high-level sections in the cleaned text based on known section headers.

    Returns:
        dict: {section_name: section_content}
    """
    lines = cleaned_text.splitlines()
    sections = {}
    current_section = "undefined"
    buffer = []

    def is_section_header(line: str) -> bool:
        return any(h in line.lower() for h in SECTION_HEADERS)

    for line in lines:
        if is_section_header(line):
            if buffer and current_section != "undefined":
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []
            current_section = line.strip()
        else:
            buffer.append(line)

    if buffer and current_section != "undefined":
        sections[current_section] = "\n".join(buffer).strip()

    return sections

def clean_text_and_detect_sections(raw_text: str) -> Tuple[str, Dict[str, str]]:
    """
    Full cleaning pipeline: clean text and detect sections.

    Returns:
        Tuple of (cleaned_text, detected_sections)
    """
    cleaned = clean_text(raw_text)
    sections = detect_sections(cleaned)
    return cleaned, sections
