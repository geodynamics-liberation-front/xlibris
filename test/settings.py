import os

# The root XLibris directory
xlibris_dir=os.path.expanduser('./xlibris')

# The directory where documents are saved when downloaded
download_dir=os.path.join(xlibris_dir,'downloads')

# The directory where the acutal documents are housed
doc_dir=os.path.join(xlibris_dir,'.docs')

# the directory the database is stored in
db_dir=os.path.join(xlibris_dir,'db')

# location and name of the database
db_file=os.path.join(db_dir,'xlibris.sql3')

# the mount point for the virtual filesystem
mountpoint_dir=os.path.join(xlibris_dir,'docs')

# prompt when multiple DOI are found?
prompt_doi=False

# Delete the original file when importing?
move_file=False

# A place to dump logs and other stuff
log_dir=os.path.join(xlibris_dir,'log')

# Function that converts a PDF to text using pdfttext
def pdf_to_text_pdftotext(pdf):
    import os
    import subprocess
    with open(os.devnull) as nul:
        return subprocess.check_output(["pdftotext",pdf,'-'],stderr=nul)

def pdf_to_text_ps2ascii(pdf):
    import os
    import subprocess
    with open(os.devnull) as nul:
        return subprocess.check_output(["ps2ascii",pdf],stderr=nul)

pdf_to_text=pdf_to_text_pdftotext

# Fuction that returns a base filename for an article.
# This function must return a unique filename or bad thing happen
def format_filename(article):
	author=article.authors[0]
	doi=article.doi.replace("/","\\")
	abbrev=article.issue.journal.abbreviation
	sn=author.surname.replace(' ','_')

	if 'print' in article.issue.publications:
		year=article.issue.publications['print'].year
	else:
		year=article.issue.publications.values()[0].year

	if len(article.authors)==1:
		filename="%s-%s-%s-%s"%(sn,abbrev,year,doi)
	elif (article.authors)==2:
		author2=article.authors[1]
		sn2=author2.surname.replace(' ','_')
		filename="%s,%s-%s-%s-%s"%(sn,sn2,abbrev,year,doi)
	else:
		filename="%s,etal-%s-%s-%s"%(sn,abbrev,year,doi)
	return filename
