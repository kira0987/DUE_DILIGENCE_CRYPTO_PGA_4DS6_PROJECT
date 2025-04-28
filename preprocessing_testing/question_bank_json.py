import re
import json
from tkinter import filedialog
import tkinter as tk

tag_pattern = r"^[IVXLCDM]+\.\s+(.+)"
subtag_pattern = r"^\d+\s*\.\s*(.+?)(:)?$"
question_pattern = r".*\?$"

tags_dict = {}

def process_file(file_path):
    current_tag = None
    current_subtag = None

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            # Match Tag
            tag_match = re.match(tag_pattern, line)
            if tag_match:
                tag_name = tag_match.group(1).strip(': ')
                if tag_name not in tags_dict:
                    tags_dict[tag_name] = {"subtags": [], "questions": []}
                current_tag = tag_name
                current_subtag = None
                continue

            # Match Subtag
            subtag_match = re.match(subtag_pattern, line)
            if subtag_match and current_tag:
                subtag_name = subtag_match.group(1).strip(': ')
                current_subtag = {"subtag": subtag_name, "questions": []}
                tags_dict[current_tag]["subtags"].append(current_subtag)
                continue

            # Match Question
            if re.match(question_pattern, line) and current_tag:
                question = re.sub(r"^\W*\s*", "", line).strip()
                if current_subtag:
                    current_subtag["questions"].append(question)
                else:
                    tags_dict[current_tag]["questions"].append(question)

def create_json():
    return {
        "tags": [
            {
                "tag": tag,
                "subtags": data["subtags"],
                "questions": data["questions"]
            }
            for tag, data in tags_dict.items()
        ]
    }

def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Text File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )

    if not file_path:
        print("No file selected.")
        return

    process_file(file_path)

    output = create_json()
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("JSON saved to output.json")

if __name__ == "__main__":
    main()
