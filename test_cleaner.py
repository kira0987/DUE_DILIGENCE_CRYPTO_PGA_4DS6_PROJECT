from core.cleaner import clean_text_and_detect_sections

with open("data/pitestextracted.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

cleaned_text, sections = clean_text_and_detect_sections(raw_text)

print("✅ TEXTE NETTOYÉ :")
print(cleaned_text[:500], "...\n")  # juste le début

print("📑 SECTIONS DÉTECTÉES :")
for section, content in sections.items():
    print(f"\n🔸 {section.upper()}:\n{content[:300]}...\n")
