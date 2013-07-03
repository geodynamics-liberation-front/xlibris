import atexit
import sys
import os

source=os.path.abspath("../src")

def remove_pyc():
	for d,child_dir,files in os.walk(source):
		for f in [f for f in files if f.endswith("pyc")]:
			os.unlink(os.path.join(d,f))

atexit.register(remove_pyc)
remove_pyc()

sys.path=[source]+sys.path
import xlibris as xl
import xlibris.doi as doi
import xlibris.settings as xlsettings
import xlibris.xlibris_db as xldb
import xlibris.xlibris_store as xls

xl.debug_on()

rcfile=os.path.expanduser(os.path.join('~','.xlibrisrc.py'))
rcfile="./settings.py"
settings=xlsettings.get_settings(rcfile)

db=xldb.XLibrisDB(settings.db_file)
store=xls.XLibrisStore(db)

def get_test_article():
    global dois,doi_number,doi_xml,article
    pdf="pdf/10.1007_s11068-008-9033-8.pdf"
    dois=doi.get_doi_from_pdf(pdf)
    doi_number=dois[0]
    doi_xml=doi.get_doi_xml(doi_number)
    article=doi.parse_doi_xml(doi_xml)

