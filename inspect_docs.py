from pypdf import PdfReader
from docx import Document
import os

pdf_path = r'C:\Users\kirik\Multi-Modal-Agent\inf\1.pdf'
docx_path = r'C:\Users\kirik\Multi-Modal-Agent\inf\2.docx'
output_path = r'C:\Users\kirik\Multi-Modal-Agent\extracted_text.txt'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("--- 1.pdf ---\n")
    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            f.write(f"Page {i+1}:\n")
            f.write(page.extract_text() + "\n")
    else:
        f.write("1.pdf not found\n")

    f.write("\n--- 2.docx ---\n")
    if os.path.exists(docx_path):
        doc = Document(docx_path)
        for i, para in enumerate(doc.paragraphs):
            f.write(f"Para {i+1}: {para.text}\n")
    else:
        f.write("2.docx not found\n")

print(f"Extracted text saved to {output_path}")
