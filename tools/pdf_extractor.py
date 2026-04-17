import pdfplumber
import re


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts clean text from a PDF resume.
    """
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    text = clean_text(text)
    return text


def clean_text(text: str) -> str:
    """
    Removes extra spaces and weird characters from PDF extraction.
    """
    text = re.sub(r'\s+', ' ', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.strip()
    return text
