#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
import imp
import os
import shutil
import pdf as xpdf
from . import LOG

class Bunch:
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

class SettingsException(Exception):
    def __init__(self, value, problems):
        self.value = value
        self.problems = problems

    def __str__(self):
        return repr(self.value)

def get_default():
    import pkg_resources
    return pkg_resources.resource_string(__name__,"default_settings.py")

def write_default(dotrc):
    if os.path.exists(dotrc):
        LOG.debug("Backing up existing file")
        shutil.copy(dotrc,dotrc+".orig")
    LOG.debug("Creating default settings file at %s"%dotrc)
    rcfile=open(dotrc,'w')
    rcfile.write(get_default())
    rcfile.flush()
    rcfile.close()

def create_dirs(settings):
    if type(settings) == str:
        settings=read_settings(settings)
    elif isinstance(settings, Bunch):
        settings = settings.__dict__
    elif type(settings) != dict:
        raise ValueError("Argument must be a str, xlibris.settings.Bunch or dict")

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
    import pkg_resources
    import tempfile
    import traceback
    problems=[]
    LOG.debug('Checking if setup file %s exists', dotrc)
    if not os.path.exists(dotrc):
        problems.append("Settings file '%s' not found." % dotrc)
    else:
        # Check that the current settings file has at lease the same 
        # variables as the default
        defaults={}
        exec get_default() in {},defaults
        settings=read_settings(dotrc)
        LOG.debug('Checking if setup file has the necessary variables set')
        for key in [k for k in defaults.keys() if k not in settings]:
            problems.append("Setting file missing '%s'"%key)

        # Make sure the directories exist and are not regular file
        LOG.debug('Checking if the directories exist as directories')
        for dir_key in [k for k in settings.keys() if k.endswith('dir')]:
            d=settings[dir_key]
            if not os.path.exists(d):
                problems.append("%s set to '%s' does not exist"%(dir_key,d))
            elif os.path.isfile(d):
                problems.append("%s set to '%s' is a regular file"%(dir_key,d))

        # Check the pdf to text function
        LOG.debug('Checking the pdf to text')
        with tempfile.NamedTemporaryFile(mode='w+b',delete=False,suffix='.pdf') as tmp_file:
            tmp_name=tmp_file.name
            LOG.debug('Created temporary file %s',tmp_name)
            tmp_file.write(pkg_resources.resource_string(__name__,"hello_world.pdf"))
        try:
            contents=xpdf.pdf_to_text(tmp_name)
            if contents.strip() != 'hello world':
                problems.append("pdf_to_text function ran but did not result in the expected output")
        except:
            problems.append("pdf_to_text function failed to run correctly:\n%s" % traceback.format_exc())
        if os.path.exists(tmp_name): os.unlink(tmp_name)

    # Check that we can import the necessary modules
    modules=['bs4','fuse','unidecode'] 
    LOG.debug('Checking installed modules %s' % modules)
    for module in modules:
        try:
            imp.find_module(module)
        except ImportError:
            problems.append("Required module '%s' is not installed"%module)

    if len(problems)>0:
        raise SettingsException(dotrc,problems)

settings = None
def get_settings(dotrc=None):
    global settings
    if dotrc != None:
        settings = Bunch(**read_settings(dotrc))
    #check(dotrc)
    # Check if the dotrc file exists
    return settings

def read_settings(dotrc):
    rcfile=open(dotrc)
    settings={}
    exec rcfile in {},settings
    rcfile.close()
    return settings
