import re
from collections import OrderedDict

# DOI regular expressions
doiurl_re=re.compile("doi:\s?(10\.[a-z0-9\-._:;()/<>]+)",re.U)   # Matches doi:(10. ... )
doispace_re=re.compile("doi\s?(10\.[a-z0-9\-._:;()/<>]+)",re.U)   # Matches doi (10. ... )
dx_re=re.compile("dx.doi.org/(10\.[a-z0-9\-._:;()/<>]+)",re.U) # Matches dx.doi.org/(10. ...)
doi_re=re.compile("(?:\s|^)(10\.[0-9.]+/[a-z0-9\-._:;()/<>]+)",re.U) # Mathces (10. ... )

def doi_from_text(text):
    doi_numbers=[]
    for line in text.splitlines():
        line=line.lower()
        if 'doi' in line:
            for d in doiurl_re.findall(line):
                doi_numbers.append(clean_doi(d))
            for d in doispace_re.findall(line):
                doi_numbers.append(clean_doi(d))
            for d in dx_re.findall(line):
                doi_numbers.append(clean_doi(d))
        elif "10." in line:
            for d in doi_re.findall(line):
                doi_numbers.append(clean_doi(d))

    doi_numbers=list(OrderedDict.fromkeys(doi_numbers))
    return doi_numbers

def clean_doi(d):
    """
    Cleans the DOI of extranious but valid characters at the end.  If my regex fu were
    better I bet I wouldn't need this method.
    Removes a trailing '.' and removes a trailing ')' if '(' and ')' counts don't match
    """
    if d[-1]=='.': d=d[:-1] # end of a sentence
    if d[-1]==')' and d.count('(')!=d.count(')'): d=d[:-1] # in () not seperated by a space
    if d[-1]==';': d=d[:-1] # poorly formated list
    if d[-4:]=='</a>': d=d[:-4] # an anchor tag
    return d
