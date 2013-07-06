import os
import re
import subprocess

# DOI regular expressions
doiurl_re=re.compile("doi:\s?(10\.[a-z0-9\-._:;()/<>]+)")   # Matches doi:(10. ... )
doispace_re=re.compile("doi\s?(10\.[a-z0-9\-._:;()/<>]+)")   # Matches doi (10. ... )
dx_re=re.compile("dx.doi.org/(10\.[a-z0-9\-._:;()/<>]+)") # Matches dx.doi.org/(10. ...)
doi_re=re.compile("(?:\s|^)(10\.[0-9.]+/[a-z0-9\-._:;()/<>]+)") # Mathces (10. ... )

# Function that converts a PDF to text using pdfttext
pdf_to_text_func=None

def set_pdf_to_text(f):
    global pdf_to_text_func
    pdf_to_text_func=f

def pdf_to_text_pdftotext(pdf):
    with open(os.devnull) as nul:
        return subprocess.check_output(["pdftotext",pdf,'-'],stderr=nul)

def pdf_to_text_ps2ascii(pdf):
    with open(os.devnull) as nul:
        return subprocess.check_output(["ps2ascii",pdf],stderr=nul)


def clean_doi(d):
    """
    Cleans the DOI of extranious but valid characters at the end.  If my regex fu were
    better I bet I wouldn't need this method.
    Removes a trailing '.' and removes a trailing ')' if '(' and ')' counts don't match
    """
    if d[-1]=='.': d=d[:-1]
    if d[-1]==')' and d.count('(')!=d.count(')'): d=d[:-1]
    if d[-1]==';': d=d[:-1]
    return d

def get_doi_from_pdf(pdf):
    doi=[]
#    for line in subprocess.check_output(["pdftotext",pdf,'-'],stderr=open(os.devnull)).splitlines():
    for line in pdf_to_text_func(pdf).splitlines():
        line=line.lower()
        if 'doi' in line:
            for d in doiurl_re.findall(line):
                doi.append(clean_doi(d))
            for d in doispace_re.findall(line):
                doi.append(clean_doi(d))
            for d in dx_re.findall(line):
                doi.append(clean_doi(d))
        elif "10." in line:
            for d in doi_re.findall(line):
                doi.append(clean_doi(d))
    return doi
