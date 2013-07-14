import os
import xlibris.pdf as xpdf

# The root XLibris directory
xlibris_dir=os.path.expanduser('~/Documents/xlibris')

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
prompt_doi=True

# Delete the original file when importing?
move_file=False

# A place to dump logs and other stuff
log_dir=os.path.join(xlibris_dir,'log')

# Set the PDF to Text function
xpdf.set_pdf_to_text(xpdf.pdf_to_text_pdftotext)

# Proxy information.  This can be used to access
# journal websites behind a paywall when off
# of a campus network.
# username/password if the proxy requires authentication
#www.proxy_user = 'your_user_name'
#www.proxy_password = 'youSee5d'
# proxy hostname and port
#www.proxy_address = 'proxy.example.com'
#www.proxy_port = 8080

# Fuction that returns a base filename for an article.
# This function must return a unique filename or bad thing happen
def format_filename(article):
    author=article.authors[0]
    doi=article.doi.replace("/","\\")
    abbrev=article.issue.journal.abbreviation
    sn=author.surname.replace(' ','_')
    year=article.get_publication_year()

    if len(article.authors)==1:
        filename="%s-%s-%s-%s"%(sn,abbrev,year,doi)
    elif (article.authors)==2:
        author2=article.authors[1]
        sn2=author2.surname.replace(' ','_')
        filename="%s,%s-%s-%s-%s"%(sn,sn2,abbrev,year,doi)
    else:
        filename="%s,etal-%s-%s-%s"%(sn,abbrev,year,doi)
    return filename

if __name__=='__main__':
    import sys
    print(locals()[sys.argv[1]])
