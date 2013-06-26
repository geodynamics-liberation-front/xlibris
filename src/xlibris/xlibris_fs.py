#!/usr/bin/env python
import fuse
import time

import stat	# for file properties
import os	  # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
			   # - note: these must be returned as negatives
from . import LOG

fuse.fuse_python_api = (0, 2)

ROOT=sorted(['/all','/author','/journal','/tag','/publication_year','/title'])

def get_path_parts(path):
	return [ p for p in path.split("/") if p!='']

def get_timestamp(day,month,year):
	return time.localtime(time.strptime("%s %s %s"%(day,month,year), "%d %m %Y"))

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0 
        self.st_ino = 0 
        self.st_dev = 0 
        self.st_nlink = 0 
        self.st_uid = 0 
        self.st_gid = 0 
        self.st_size = 0 
        self.st_atime = 0 
        self.st_mtime = 0 
        self.st_ctime = 0 

class DelegatedFS(fuse.Fuse):
	def __init__(self,paths, *args, **kw):
		fuse.Fuse.__init__(self, *args, **kw)
		self.paths=paths
		self.uid=os.getuid()
		self.gid=os.getgid()

	def getattr(self, path):
		"""
		- st_mode (protection bits)
		- st_ino (inode number)
		- st_dev (device)
		- st_nlink (number of hard links)
		- st_uid (user ID of owner)
		- st_gid (group ID of owner)
		- st_size (size of file, in bytes)
		- st_atime (time of most recent access)
		- st_mtime (time of most recent content modification)
		- st_ctime (platform dependent; time of most recent metadata change on Unix,
					or the time of creation on Windows).
		"""
		LOG.debug("getattr: %s",path)
		path=unicode(path,"utf-8").replace("\ "," ").replace('\\\\','\\')
		parts=get_path_parts(path)
		depth=len(parts)

		st = MyStat()
		st.st_uid = self.uid
		st.st_gid = self.gid

		if depth==0:
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 

		if depth>0 and parts[0] in self.paths:
			LOG.debug("Delegated FS object: %s",self.paths[parts[0]])
			try:
				if not self.paths[parts[0]].getattr(path,parts,depth,st):
					return -errno.ENOENT
			except:
				retrun -errno.ENOENT
		return st

	def readdir(self,path,offset):
		LOG.debug("readdir: %s (%d)",path,offset)
		dirlist=['.','..']
		path=unicode(path,"utf-8").replace("\ "," ").replace('\\\\','\\')
		parts=get_path_parts(path)
		depth=len(parts)
		# The root directory
		if depth==0:
			dirlist.extend( sorted( self.paths.keys() ) )
		# The directories just under root
		elif parts[0] in self.paths:
			self.paths[parts[0]].readdir(path,parts,depth,dirlist)

		LOG.debug(dirlist)
		for d in dirlist:
			yield fuse.Direntry(d.encode("utf-8"))

	def read ( self, path, length, offset ):
		LOG.debug("read: %s (%d,%d)"%(path, length, offset))
		path=unicode(path,"utf-8").replace("\ "," ").replace('\\\\','\\')
		parts=get_path_parts(path)
		depth=len(parts)
		if depth>0 and parts[0] in self.paths:
				LOG.debug("Delegated FS object: %s",self.paths[parts[0]])
				return self.paths[parts[0]].read(path,parts,depth,length,offset)

#
# Author FS
#
class AuthorFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def _author_to_dir(self,author):
		return author.surname+', '+author.given_name

	def _dir_to_author(self,dirname):
		surname,given_name=[ n.strip() for n in dirname.split(',') ]
		return self.store.get_author_by_name(given_name,surname)

	def _article_to_file(self,article):
		# [title].[filename extension]
		return "%s%s"%(article.title, os.path.splitext(article.filename)[1])

	def _file_to_article(self,author,filename):
		title,ext=os.path.splitext(filename)
		return self.store.get_article_from_author_by_title(author,title)

	def getattr(self, path,parts,depth,st):
		if depth==1:
			# /author
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		elif depth==2:
			# /author/[author]
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
			author=self._dir_to_author(parts[1])
			if not author:
				return False
		elif depth==3:
			# /author/[author]/title.pdf
			a=self._file_to_article(self._dir_to_author(parts[1]),parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			file_st=os.stat(filename)

			st.st_mode = stat.S_IFREG | 0444
			st.st_nlink = 1 
			st.st_size = file_st.st_size
			st.st_atime = st.st_stime = st.st_mtime = a.get_earliest_publication().time()
		else:
			return False
		return True

	def readdir(self,path,parts,depth,dirlist):
		if depth==1:
			# /author
			authors=sorted( [self._author_to_dir(a) for a in self.store.get_all_author()] )
			dirlist.extend(authors)
		elif depth==2:
			# /author/[author]
			a=self._dir_to_author(parts[1])
			if a!=None:
				articles=sorted([self._article_to_file(article) for article in a.articles])
				dirlist.extend(articles)

	def read(self,path,parts,depth,length,offset):
		if depth==3:
			# /author/[author]/title.pdf
			a=self._file_to_article(self._dir_to_author(parts[1]),parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			with open(filename) as f:
				f.seek(offset)
				return f.read(length)

#
# All Articles FS
#
class AllArticleFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def _article_to_file(self,article):
		return article.filename

	def _file_to_article(self,filename):
		return self.store.get_article_by_filename(filename)

	def getattr(self,path,parts,depth,st):
		if depth==1:
			# /all
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		elif depth==2:
			# /all/[article.filename]
			a=self._file_to_article(parts[1])
			filename=os.path.join(self.doc_dir,a.filename)
			file_st=os.stat(filename)

			st.st_mode = stat.S_IFREG | 0444
			st.st_nlink = 1 
			st.st_size = file_st.st_size
			st.st_atime = st.st_stime = st.st_mtime = a.get_earliest_publication().time()
		else:
			return False
		return True

	def readdir(self,path,parts,depth,dirlist):
		if depth==1:
			# /all
			articles=sorted([ self._article_to_file(a) for a in self.store.get_all_article() ])
			dirlist.extend(articles)

	def read(self,path,parts,depth,length,offset):
		if depth==2:
			# /all/[article].pdf
			a=self._file_to_article(parts[1])
			filename=os.path.join(self.doc_dir,a.filename)
			with open(filename) as f:
				f.seek(offset)
				return f.read(length)

#
# Journal FS
#

class JournalFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def _journal_to_dir(self,journal):
		return journal.title

	def _dir_to_journal(self,dirname):
		return self.store.get_journal_by_title(dirname)

	def _article_to_file(self,article):
		return article.filename

	def _file_to_article(self,filename):
		return self.store.get_article_by_filename(filename)

	def getattr(self, path,parts,depth,st):
		if depth==1:
			# /journal
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		elif depth==2:
			# /journal/[journal.title]
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
			journal=self._dir_to_journal(parts[1])
			if not journal:
				return False
		elif depth==3:
			# /journal/[journal]/[article.filename]
			a=self._file_to_article(parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			file_st=os.stat(filename)

			st.st_mode = stat.S_IFREG | 0444
			st.st_nlink = 1 
			st.st_size = file_st.st_size
			st.st_atime = st.st_stime = st.st_mtime = a.get_earliest_publication().time()
		else:
			return False
		return True

	def readdir(self,path,parts,depth,dirlist):
		if depth==1:
			# /journal
			journals=sorted([self._journal_to_dir(j) for j in self.store.get_all_journal()])
			dirlist.extend(journals) 
		elif depth==2:
			# /journal/[journal.title]
			j=self._dir_to_journal(parts[1])
			if j!=None:
				for i in j.issues:
					articles = sorted([self._article_to_file(a) for a in i.articles])
					dirlist.extend(articles)

	def read(self,path,parts,depth,length,offset):
		if depth==3:
			# /journal/[journal.title]/[article.filename]
			a=self._file_to_article(parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			with open(filename) as f:
				f.seek(offset)
				return f.read(length)
	

class PubYearFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def _pub_to_dir(self,publication):
		return str(publication.year)

	def _dir_to_journal(self,dirname):
		return self.store.get__by_title(dirname)

	def _article_to_file(self,article):
		return article.filename

	def _file_to_article(self,filename):
		return self.store.get_article_by_filename(filename)

	def getattr(self, path,parts,depth,st):
		if depth==1:
			# /publication_yea
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		elif depth==2:
			# /publication_year/[year]
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		elif depth==3:
			# /publication_year/[year]/[article.filename]
			a=self._file_to_article(parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			file_st=os.stat(filename)
			st.st_mode = stat.S_IFREG | 0444
			st.st_nlink = 1 
			st.st_size = file_st.st_size
			st.st_atime = st.st_stime = st.st_mtime = a.get_earliest_publication().time()
		else:
			return False
		return True

	def readdir(self,path,parts,depth,dirlist):
		if depth==1:
			# /publication_year
			years=[str(y) for y in sorted(self.store.get_publication_years())]
			dirlist.extend(years) 
		elif depth==2:
			# /publication_year/[year]
			articles=sorted([self._article_to_file(a) for a in self.store.get_articles_from_year(parts[1])])
			dirlist.extend(articles) 

	def read(self,path,parts,depth,length,offset):
		if depth==3:
			# /publication_year/[year]/[article.filename]
			a=self._file_to_article(parts[2])
			filename=os.path.join(self.doc_dir,a.filename)
			with open(filename) as f:
				f.seek(offset)
				return f.read(length)

class TitleFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def getattr(self, path,parts,depth,st):
		if depth==1:
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		return True
	def readdir(self,path,parts,depth,dirlist):
		pass

class TagFS(object):
	def __init__(self,store,settings):
		self.store=store
		self.doc_dir=settings.doc_dir

	def getattr(self, path,parts,depth,st):
		if depth==1:
			st.st_mode = stat.S_IFDIR | 0555
			st.st_nlink = 2 
		return True
	def readdir(self,path,parts,depth,dirlist):
		pass



class XLibrisFS(DelegatedFS):
	def __init__(self, store, settings, *args, **kw):
		paths={
		"all":AllArticleFS(store,settings),
		"author":AuthorFS(store,settings),
		"journal":JournalFS(store,settings),
		"tag":TagFS(store,settings),
		"publication_year":PubYearFS(store,settings),
		"title":TitleFS(store,settings)}
		DelegatedFS.__init__(self, paths,*args, **kw)
		LOG.debug("Init complete.")


#	def getxattr(self, *args,**kwargs):
#		LOG.debug("getxattr: %s",args)
#		LOG.debug("getxattr: %s",kwargs)
#		return -errno.ENOENT
#
#	def listxattr(self,*args,**kwargs):
#		LOG.debug("listxattr: %s",args)
#		LOG.debug("listxattr: %s",kwargs)
#		return ['doi']
#
#	def getxattr(self, path, name, size):
#		LOG.debug("getxattr path: %s",path)
#		LOG.debug("getxattr name: %s",name)
#		LOG.debug("getxattr size: %d",size)
#		val = name.swapcase() + '@' + path
#		if size == 0:
#			# We are asked for size of the value.
#			return len(val)
#		return val
#
#
#	def listxattr(self, path, size):
#		LOG.debug("listxattr path: %s",path)
#		LOG.debug("listxattr size: %d",size)
#		# We use the "user" namespace to please XFS utils
#		aa = ["user." + a for a in ("foo", "bar")]
#		if size == 0:
#			# We are asked for size of the attr list, ie. joint size of attrs
#			# plus null separators.
#			return len("".join(aa)) + len(aa)
#		return aa
#
#	def getattr(self, path):
#		"""
#		- st_mode (protection bits)
#		- st_ino (inode number)
#		- st_dev (device)
#		- st_nlink (number of hard links)
#		- st_uid (user ID of owner)
#		- st_gid (group ID of owner)
#		- st_size (size of file, in bytes)
#		- st_atime (time of most recent access)
#		- st_mtime (time of most recent content modification)
#		- st_ctime (platform dependent; time of most recent metadata change on Unix,
#					or the time of creation on Windows).
#		"""
#		LOG.debug("getattr: %s",path)
#		parts=get_path_parts(path)
#		depth=len(parts)
#
#		st = MyStat()
#		st.st_uid = self.uid
#		st.st_gid = self.gid
#
#		if path == '/' or path in ROOT:
#			st.st_mode = stat.S_IFDIR | 0755
#			st.st_nlink = 2 
#		elif depth==2 and parts[0]=="author":
#			d=parts[1]
#			surname,given_name=[ unicode(n.strip(),"utf-8") for n in d.split(',') ]
#			author=self.store.find_author(given_name,surname)
#			if not author:
#				return -errno.ENOENT
#			st.st_mode = stat.S_IFDIR | 0755
#			st.st_nlink = 2 
#			st.st_mode = stat.S_IFREG | 0444
#			st.st_nlink = 1 
#			st.st_size = 42
#		else:
#			return -errno.ENOENT
#		return st
#
#	def readdir(self,path,offset):
#		LOG.debug("readattr: %s (%d)",path,offset)
#		dirlist=['.','..']
#		# The root directory
#		if path=='/':
#			dirlist.extend( [d[1:] for d in ROOT])
#		# The directories just under root
#		if path in ROOT:
#			if path=="/author":
#				dirlist.extend( [(a['surname']+', '+a['given_name']).encode("utf-8") for a in self.store.search_author()] )
#
#		LOG.debug(dirlist)
#		for r in dirlist:
#			yield fuse.Direntry(r)

	def open ( self, path, flags ):
		LOG.debug("unhandled open: %s",path)
		return 0

#	def read ( self, path, length, offset ):
#		LOG.debug("read: %s (%d,%d)"%(path, length, offset))
#		return "hello world"

	def getdir(self, path):
		"""
		return: [[('file1', 0), ('file2', 0), ... ]]
		"""
		print('*** getdir : %s'%path)
		return [('file1', 0), ('file2', 0)]
		#return -errno.ENOSYS

	def mythread ( self ):
		print '*** mythread'
		return -errno.ENOSYS

	def chmod ( self, path, mode ):
		print '*** chmod', path, oct(mode)
		return -errno.ENOSYS

	def chown ( self, path, uid, gid ):
		print '*** chown', path, uid, gid
		return -errno.ENOSYS

	def fsync ( self, path, isFsyncFile ):
		print '*** fsync', path, isFsyncFile
		return -errno.ENOSYS

	def link ( self, targetPath, linkPath ):
		print '*** link', targetPath, linkPath
		return -errno.ENOSYS

	def mkdir ( self, path, mode ):
		print '*** mkdir', path, oct(mode)
		return -errno.ENOSYS

	def mknod ( self, path, mode, dev ):
		print '*** mknod', path, oct(mode), dev
		return -errno.ENOSYS

	def readlink ( self, path ):
		print '*** readlink', path
		return -errno.ENOSYS

	def release ( self, path, flags ):
		print '*** release', path, flags
		return -errno.ENOSYS

	def rename ( self, oldPath, newPath ):
		print '*** rename', oldPath, newPath
		return -errno.ENOSYS

	def rmdir ( self, path ):
		print '*** rmdir', path
		return -errno.ENOSYS

	def statfs ( self ):
		print '*** statfs'
		return -errno.ENOSYS

	def symlink ( self, targetPath, linkPath ):
		print '*** symlink', targetPath, linkPath
		return -errno.ENOSYS

	def truncate ( self, path, size ):
		print '*** truncate', path, size
		return -errno.ENOSYS

	def unlink ( self, path ):
		print '*** unlink', path
		return -errno.ENOSYS

	def utime ( self, path, times ):
		print '*** utime', path, times
		return -errno.ENOSYS

	def write ( self, path, buf, offset ):
		print '*** write', path, buf, offset
		return -errno.ENOSYS
