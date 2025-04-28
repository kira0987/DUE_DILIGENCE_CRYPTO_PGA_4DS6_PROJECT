import os
import json
import re
import tkinter as tk
from tkinter import filedialog
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_roman_section(line):
    """Detect if a line is a Roman numeral section (e.g., I., II.)."""
    return bool(re.match(r'^[IVXLCDM]+\.\s+[A-Za-z]', line.strip()))

def is_numbered_subsection(line):
    """Detect if a line is a numbered subsection (e.g., 1., 2.)."""
    return bool(re.match(r'^\d+\.\s+[A-Za-z]', line.strip()))

def is_subheading(line):
    """Detect if a line is a subheading (starts with ● or **)."""
    return bool(re.match(r'^●\s+|^[*]{2}.+[*]{2}:?$', line.strip()))

def extract_questions_from_txt(txt_path):
    """Extract questions from the text file and organize by Roman numeral sections."""
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    structured_data = {}
    current_roman_section = "Uncategorized"
    current_numbered_subsection = None
    current_subheading = None
    question_buffer = ""

    for line in lines:
        line = line.strip()
        if not line or line.isdigit() or line.startswith('<DOCUMENT>') or line.startswith('</DOCUMENT>'):
            continue

        # Detect Roman numeral sections
        if is_roman_section(line):
            if question_buffer:  # Process any buffered question
                if question_buffer.endswith('?'):
                    target = structured_data.setdefault(current_roman_section, {})
                    if current_numbered_subsection:
                        target = target.setdefault(current_numbered_subsection, {})
                    if current_subheading:
                        target = target.setdefault(current_subheading, [])
                    else:
                        target = target.setdefault("Questions", [])
                    target.append(question_buffer.strip())
                question_buffer = ""
            current_roman_section = re.sub(r'^[IVXLCDM]+\.\s+', '', line).strip()
            current_numbered_subsection = None
            current_subheading = None
            structured_data.setdefault(current_roman_section, {})
            logging.info(f"New Roman section: {current_roman_section}")
            continue

        # Detect numbered subsections
        if is_numbered_subsection(line):
            if question_buffer:  # Process any buffered question
                if question_buffer.endswith('?'):
                    target = structured_data.setdefault(current_roman_section, {})
                    if current_numbered_subsection:
                        target = target.setdefault(current_numbered_subsection, {})
                    if current_subheading:
                        target = target.setdefault(current_subheading, [])
                    else:
                        target = target.setdefault("Questions", [])
                    target.append(question_buffer.strip())
                question_buffer = ""
            current_numbered_subsection = re.sub(r'^\d+\.\s+', '', line).strip()
            current_subheading = None
            structured_data[current_roman_section].setdefault(current_numbered_subsection, {})
            logging.info(f"New numbered subsection: {current_numbered_subsection}")
            continue

        # Detect subheadings
        if is_subheading(line):
            if question_buffer:  # Process any buffered question
                if question_buffer.endswith('?'):
                    target = structured_data.setdefault(current_roman_section, {})
                    if current_numbered_subsection:
                        target = target.setdefault(current_numbered_subsection, {})
                    if current_subheading:
                        target = target.setdefault(current_subheading, [])
                    else:
                        target = target.setdefault("Questions", [])
                    target.append(question_buffer.strip())
                question_buffer = ""
            current_subheading = re.sub(r'^●\s+|^[*]{2}|[*]{2}:?$', '', line).strip()
            target = structured_data[current_roman_section]
            if current_numbered_subsection:
                target = target.setdefault(current_numbered_subsection, {})
            target.setdefault(current_subheading, [])
            logging.info(f"New subheading: {current_subheading}")
            continue

        # Handle questions (merge lines if split)
        cleaned_line = re.sub(r'^○\s+|^-\s+', '', line).strip()
        if cleaned_line:
            question_buffer += " " + cleaned_line
            if cleaned_line.endswith('?'):
                target = structured_data.setdefault(current_roman_section, {})
                if current_numbered_subsection:
                    target = target.setdefault(current_numbered_subsection, {})
                if current_subheading:
                    target = target.setdefault(current_subheading, [])
                else:
                    target = target.setdefault("Questions", [])
                target.append(question_buffer.strip())
                logging.info(f"Added question: {question_buffer.strip()}")
                question_buffer = ""

    # Process any remaining buffer
    if question_buffer and question_buffer.endswith('?'):
        target = structured_data.setdefault(current_roman_section, {})
        if current_numbered_subsection:
            target = target.setdefault(current_numbered_subsection, {})
        if current_subheading:
            target = target.setdefault(current_subheading, [])
        else:
            target = target.setdefault("Questions", [])
        target.append(question_buffer.strip())
        logging.info(f"Added final question: {question_buffer.strip()}")

    # Clean up empty sections
    def clean_empty(d):
        return {k: v for k, v in d.items() if v and (isinstance(v, dict) and clean_empty(v) or isinstance(v, list) and v)}

    structured_data = clean_empty(structured_data)
    return structured_data

def save_to_json(data, output_path):
    """Save the structured data to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logging.info(f"Questions saved to: {output_path}")

def main():
    root = tk.Tk()
    root.withdraw()

    # Select TXT file
    txt_path = filedialog.askopenfilename(
        title="Select the Questions Bank TXT File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not txt_path:
        logging.error("No file selected. Exiting.")
        return

    # Select output directory
    output_dir = filedialog.askdirectory(title="Select Output Directory")
    if not output_dir:
        logging.error("No output directory selected. Exiting.")
        return
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Extract questions
        structured_data = extract_questions_from_txt(txt_path)
        
        # Save to JSON
        output_json = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(txt_path))[0]}_questions.json")
        save_to_json(structured_data, output_json)

        # Log summary
        total_questions = sum(
            len(questions) if isinstance(questions, list) else sum(len(q) for q in questions.values())
            for section in structured_data.values()
            for questions in (section.values() if isinstance(section, dict) else [section])
        )
        logging.info(f"Total questions extracted: {total_questions}")
        for section, content in structured_data.items():
            section_questions = sum(
                len(questions) if isinstance(questions, list) else sum(len(q) for q in questions.values())
                for questions in content.values()
            )
            logging.info(f"{section}: {section_questions} questions")
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        raise

if __name__ == "__main__":
    main()