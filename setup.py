import os
import stat
from datetime import datetime
from setuptools import setup
import py_compile

orig_py_compile = py_compile.compile

def doraise_py_compile(file, cfile=None, dfile=None, doraise=False):
	orig_py_compile(file, cfile=cfile, dfile=dfile, doraise=True)

py_compile.compile = doraise_py_compile

def read(fname):
	    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def most_recent_mod(directory):
	mod=0;
	for dirpath, dirnames, filenames in os.walk(directory): 
		for filename in filenames:
			fname=os.path.join(dirpath,filename)
			stats=os.stat(fname)
			mod=max(mod,stats[stat.ST_MTIME])
	return mod

ver=datetime.fromtimestamp(most_recent_mod('src')).strftime('%Y.%m.%d.%H.%M')

setup(
	name='xlibris',
	description='A DOI based PDF management system.',
	author='Robert I. Petersen',
	author_email='rpetersen@ucsd.edu', 
	version=ver,
	scripts=['src/bin/xlibris'],
	packages=['xlibris'],
	package_dir={'xlibris': 'src/xlibris'},
	license='GPL 2.0', 
	classifiers=[
'Development Status :: 4 - Beta',
'Intended Audience :: Developers',
'License :: OSI Approved :: GNU General Public License (GPL)',
'Programming Language :: Python'
	],
	long_description=read('README.md')
)
