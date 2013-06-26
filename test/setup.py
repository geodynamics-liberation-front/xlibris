import atexit
import sys
import os

source= os.path.abspath("../src")

def remove_pyc():
	for d,child_dir,files in os.walk(source):
		for f in [f for f in files if f.endswith("pyc")]:
			os.unlink(os.path.join(d,f))

atexit.register(remove_pyc)
remove_pyc()

sys.path=[source]+sys.path
import xlibris as xl
import xlibris.settings as xlsettings
import xlibris.xlibris_db as xldb
import xlibris.xlibris_store as xls

xl.debug_on()

rcfile=os.path.expanduser(os.path.join('~','.xlibrisrc.py'))
settings=xlsettings.get_settings(rcfile)

db=xldb.XLibrisDB(settings.db)
store=xls.XLibrisStore(db)
authors=store.get_all_author()
berco=authors[3]
berco_articles=berco.articles
a=berco_articles[0]



