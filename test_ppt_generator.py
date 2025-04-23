from core.ppt_generator import generate_ppt

RESPONSES_PATH = "answers/pitestanswers.json"
OUTPUT_PPT_PATH = "answers/pitesteport.pptx"

generate_ppt(RESPONSES_PATH, OUTPUT_PPT_PATH)
