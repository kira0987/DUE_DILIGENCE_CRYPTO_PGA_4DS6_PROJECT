from core.extractor import extract_text, save_text_to_file

files_to_test = {
    "DASCPWhitePaper.pdf": "data/pitestextracted.txt"
}

if __name__ == "__main__":
    for input_file, output_file in files_to_test.items():
        print(f"\n🚀 Extraction depuis : {input_file}")
        try:
            extracted_text = extract_text(f"data/{input_file}")
            save_text_to_file(extracted_text, output_file)
            print(f"✅ Extraction réussie et sauvegardée dans : {output_file}")
        except Exception as e:
            print(f"❌ Erreur pour {input_file} : {e}")
