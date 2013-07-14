import doi
import os
import subprocess

# Function that converts a PDF to text using pdfttext
pdf_to_text=None

def set_pdf_to_text(f):
    global pdf_to_text
    pdf_to_text=f

def pdf_to_text_pdftotext(pdf):
    with open(os.devnull) as nul:
        return subprocess.check_output(["pdftotext",pdf,'-'],stderr=nul)

def pdf_to_text_ps2ascii(pdf):
    with open(os.devnull) as nul:
        return subprocess.check_output(["ps2ascii",pdf],stderr=nul)

def get_doi_from_pdf(pdf):
    doi_numbers=[]
#    for line in subprocess.check_output(["pdftotext",pdf,'-'],stderr=open(os.devnull)).splitlines():
    for line in pdf_to_text(pdf).splitlines():
        doi_numbers.extend(doi.doi_from_text(line))
    return doi_numbers
