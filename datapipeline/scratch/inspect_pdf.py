import fitz
from pathlib import Path

pdf_path = Path("C:/CODES/VQP/datapipeline/data/NCERT-Class-12-Physics-Part-1.pdf")
doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

# Let's inspect the first 25 pages and find where chapters begin
for i in range(min(50, len(doc))):
    text = doc[i].get_text()
    first_lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
    print(f"Page {i+1} first lines: {first_lines}")

# Search for chapter names in the entire doc to see where they appear
chapter_names = [
    "ELECTRIC CHARGES AND FIELDS",
    "ELECTROSTATIC POTENTIAL AND CAPACITANCE",
    "CURRENT ELECTRICITY",
    "MOVING CHARGES AND MAGNETISM",
    "MAGNETISM AND MATTER",
    "ELECTROMAGNETIC INDUCTION",
    "ALTERNATING CURRENT",
    "ELECTROMAGNETIC WAVES"
]

print("\n--- Searching for Chapter Headers ---")
for i, page in enumerate(doc):
    text = page.get_text()
    for name in chapter_names:
        if name in text:
            print(f"Found '{name}' on page {i+1}")
