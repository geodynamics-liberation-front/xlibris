#! /usr/bin/env python
import os
import shutil
from . import LOG

DEFAULTS="""\
import os

# The root XLibris directory
xlibris_dir=os.path.expanduser('~/Documents/xlibris')

# The directory where documents are saved when downloaded
download_dir=os.path.join(xlibris_dir,'downloads')

# The directory where the acutal documents are housed
doc_dir=os.path.join(xlibris_dir,'.docs')

# the directory the database is stored in
db_dir=os.path.join(xlibris_dir,'db')

# location and name of the database
db=os.path.join(db_dir,'xlibris.sql3')

# the mount point for the virtual filesystem
mountpoint_dir=os.path.join(xlibris_dir,'docs')

# prompt when multiple DOI are found?
prompt_doi=False

# Delete the original file when importing?
move_file=False

# A place to dump logs and other stuff
log_dir=os.path.join(xlibris_dir,'log')

# Fuction that returns a base filename for an article.
# This function must return a unique filename or bad thing happen
def format_filename(article):
	author=article.authors[0]
	doi=article.doi.replace("/","\\\\")
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
"""

class Bunch:
	def __init__(self, *args, **kwargs):
		self.__dict__.update(kwargs)

class SettingsException(Exception):
	def __init__(self, value, problems):
		self.value = value
		self.problems = problems

	def __str__(self):
		return repr(self.value)

def write_default(dotrc):
	if os.path.exists(dotrc):
		LOG.debug("Backing up existing file")
		shutil.copy(dotrc,dotrc+".orig")
	LOG.debug("Creating default settings file at %s"%dotrc)
	rcfile=open(dotrc,'w')
	rcfile.write(DEFAULTS)
	rcfile.flush()
	rcfile.close()

def create_dirs(dotrc):
	settings=read_settings(dotrc)

	# Make sure the directories exist
	for dir_key in [k for k in settings.keys() if k.endswith('dir')]:
		d=settings[dir_key]
		if not os.path.exists(d):
			LOG.debug("Creating %s at %s"%(dir_key,d))
			os.makedirs(d)
		elif not os.path.isdir(d):
			LOG.debug("%s exists but is not a directory"%d)
			raise IOError("%s exists but is not a directory"%d)

def check(dotrc):
	problems=[]
	if not os.path.exists(dotrc):
		problems.append("Settings file '%s' not found."%dotrc)
	else:
		settings=read_settings(dotrc)
		defaults={}
		exec DEFAULTS in {},defaults
		for key in [k for k in defaults.keys() if k not in settings]:
			problems.append("Setting file missing '%s'"%key)

		# Make sure the settings are approprate exist
		for dir_key in [k for k in settings.keys() if k.endswith('dir')]:
			d=settings[dir_key]
			if not os.path.exists(d):
				problems.append("%s set to '%s' does not exist"%(dir_key,d))
			elif os.path.isfile(d):
				problems.append("%s set to '%s' is a regular file"%(dir_key,d))

	if len(problems)>0:
		raise SettingsException(dotrc,problems)

def get_settings(dotrc):
	check(dotrc)
	# Check if the dotrc file exists
	return Bunch(**read_settings(dotrc))

def read_settings(dotrc):
	rcfile=open(dotrc)
	settings={}
	exec rcfile in {},settings
	rcfile.close()
	return settings
