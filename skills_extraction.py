from docx import Document

# Load the resume file
doc_path = "Hitesh_CV (1) (2) (1).docx"  # Change this to the correct file path
doc = Document(doc_path)

# Extract text from the document
text = "\n".join([para.text for para in doc.paragraphs])

# Find the "SKILLS" section and extract skills
import re

match = re.search(r"SKILLS\s*\n([\s\S]+?)\n\n", text)  # Look for skills between "SKILLS" and next empty line
if match:
    skills = match.group(1).strip().replace("\n", ", ")  # Formatting skills as a comma-separated list
    print("Extracted Skills:", skills)
else:
    print("Skills section not found!")
