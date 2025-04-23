from core.matcher import match_questions_to_chunks

match_questions_to_chunks(
    questions_path="questions/questions.json",
    chunks_path="data/chunkss.json",
    index_path="data/faissindex.index",
    output_path="data/matchedquestions.json",
    top_k=5
)
