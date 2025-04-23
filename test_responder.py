from core.responder import answer_all_questions, save_answers

PDF_PATH = "data/pitest.pdf"
QUESTIONS_PATH = "questions/questions.json"
OUTPUT_PATH = "answers/pitestanswers.json"

all_answers = answer_all_questions(PDF_PATH, QUESTIONS_PATH)
save_answers(all_answers, OUTPUT_PATH)
