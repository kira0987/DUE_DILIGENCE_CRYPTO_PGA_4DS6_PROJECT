from core.cleaner import clean_text_and_detect_sections
from core.chunker import chunk_sections, embed_chunks

with open("data/pitestextracted.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

cleaned, sections = clean_text_and_detect_sections(raw_text)
chunks = chunk_sections(sections)

print(f"\n🔹 {len(chunks)} chunks générés.")

for c in chunks[:2]:
    print(f"\n📌 {c['chunk_id']}:\n{c['content'][:250]}...\n")

print("🔗 Génération des embeddings...")
embeddings = embed_chunks(chunks)
print(f"✅ Embeddings générés : {embeddings.shape}")
