from core.indexer import create_index_pipeline

create_index_pipeline(
    txt_path="data/pitestextracted.txt",
    output_chunks_path="data/chunkss.json",
    output_index_path="data/faissindex.index"
)
