#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import fuse

import stat # for file properties
import os     # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives
from xlibris_store import Tag
from . import LOG

fuse.fuse_python_api = (0, 2)

def get_path_parts(path):
    return [ p for p in path.split("/") if p!='']

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
    def __init__(self, paths, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.paths = paths
        self.root = ['.', '..'] + sorted( self.paths.keys() ) 
        self.uid = os.getuid()
        self.gid = os.getgid()

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
        LOG.debug("getattr: %s", path)
        #TODO: revisit this last replacement
        path=unicode(path,"utf-8").replace("\ ", " ").replace('\\\\', '\\')
        parts=get_path_parts(path)
        depth=len(parts)

        st = MyStat()
        st.st_uid = self.uid
        st.st_gid = self.gid

        if depth==0:
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
        elif depth==1 and parts[0] in self.paths:
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
        elif depth>1 and parts[0] in self.paths:
            LOG.debug("Delegated FS object: %s",self.paths[parts[0]])
            try:
                if not self.paths[parts[0]].getattr(path,parts,depth,st):
                    return -errno.ENOENT
            except:
                LOG.exception("getattr(%s)",path)
                return -errno.ENOENT
        else:
            return -errno.ENOENT
        return st

    def readdir(self,path,offset):
        LOG.debug("readdir: %s (%d)",path,offset)
        #TODO: revisit this last replacement
        path=unicode(path,"utf-8").replace("\ "," ").replace('\\\\','\\')
        parts=get_path_parts(path)
        depth=len(parts)
        # The root directory
        if depth==0:
            dirlist=self.root
        # The directories just under root
        elif parts[0] in self.paths:
            dirlist=[u'.',u'..']
            try:
                self.paths[parts[0]].readdir(path,parts,depth,dirlist)
            except:
                LOG.exception("readdir(%s)",path)

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
                try:
                    return self.paths[parts[0]].read(path,parts,depth,length,offset)
                except:
                    LOG.exception("read(%s, length: %d, offset: %d)",path,length,offset)

    def mkdir ( self, path, mode ):
        path=unicode(path,"utf-8").replace("\ "," ").replace('\\\\','\\')
        parts=get_path_parts(path)
        depth=len(parts)
        LOG.debug("mkdir: %s %s", path, oct(mode))
        if depth==0:
            return -errno.ENOSYS
        elif parts[0] in self.paths:
            try:
                if self.paths[parts[0]].mkdir(path,parts,depth,mode):
                    return 0
            except:
                LOG.exception("mkdir(%s)",path)
                return -errno.ENOENT
        return -errno.ENOSYS

    def open ( self, path, flags ):
        LOG.debug("unhandled open: %s",path)
        return 0

class XLDelegateFS(object):
    def __init__(self,store,settings):
        self.store=store
        self.doc_dir=settings.doc_dir

    def _article_to_file(self,article):
        return article.filename

    def _file_to_article(self,filename):
        article = self.store.get_article_by_filename(filename)
        return article

    def _read(self,filename,length,offset):
        filename=os.path.join(self.doc_dir,filename)
        with open(filename) as f:
            f.seek(offset)
            return f.read(length)

    def mkdir(self, path, parts, depth, mode):
        print '*** mkdir', path, oct(mode)
        return -errno.ENOSYS

#
# Author FS
#
class AuthorFS(XLDelegateFS):
    def _author_to_dir(self,author):
        return u'%s, %s'%(author.surname, author.given_name)

    def _dir_to_author(self,dirname):
        surname,given_name=[ n.strip() for n in dirname.split(',') ]
        return self.store.get_author_by_name(given_name,surname)

    def getattr(self, path, parts, depth, st):
        if depth==2:
            # /author/[author]
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
            author=self._dir_to_author(parts[1])
            if author==None:
                return False
        elif depth==3:
            # /author/[author]/[title.pdf]
            a=self._file_to_article(parts[2])
            if a==None:
                return False
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
        return self._read(parts[2],length,offset)

#
# All Articles FS
#
class AllArticleFS(XLDelegateFS):

    def getattr(self, path, parts, depth, st):
        if depth==2:
            # /all/[article.filename]
            a=self._file_to_article(parts[1])
            if a==None:
                return False
            filename=os.path.join(self.doc_dir,a.filename)
            file_st=os.stat(filename)

            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1 
            st.st_size = file_st.st_size
            st.st_atime = st.st_stime = st.st_mtime = a.get_earliest_publication().time()
            LOG.debug("st : %s",st)
        else:
            return False
        return True

    def readdir(self,path,parts,depth,dirlist):
        if depth==1:
            # /all
            articles=sorted([ self._article_to_file(a) for a in self.store.get_all_article() ])
            dirlist.extend(articles)

    def read(self,path,parts,depth,length,offset):
        return self._read(parts[1],length,offset)

#
# Journal FS
#
class JournalFS(XLDelegateFS):
    def _journal_to_dir(self,journal):
        return journal.title

    def _dir_to_journal(self,dirname):
        return self.store.get_journal_by_title(dirname)

    def getattr(self, path,parts,depth,st):
        if depth==2:
            # /journal/[journal.title]
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
            journal=self._dir_to_journal(parts[1])
            if journal==None:
                return False
        elif depth==3:
            # /journal/[journal]/[article.filename]
            a=self._file_to_article(parts[2])
            if a==None:
                return False
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
        return self._read(parts[2],length,offset)

#
# Publication Year FS
#
class PubYearFS(XLDelegateFS):
    def getattr(self, path,parts,depth,st):
        if depth==2:
            # /publication_year/[year]
            if int(parts[1]) not in self.store.get_publication_years():
                return False
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
        elif depth==3:
            # /publication_year/[year]/[article.filename]
            a=self._file_to_article(parts[2])
            if a==None:
                return False
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
            articles=sorted([self._article_to_file(a) for a in self.store.get_article_from_year(parts[1])])
            dirlist.extend(articles) 

    def read(self,path,parts,depth,length,offset):
        return self._read(parts[2],length,offset)

#
# Title FS
#
class TitleFS(XLDelegateFS):
    def getattr(self, path,parts,depth,st):
        if depth==1:
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
        return True

    def readdir(self,path,parts,depth,dirlist):
        pass

    def read(self,path,parts,depth,length,offset):
        return self._read(parts[2],length,offset)

#
# Tag FS
#
class TagFS(XLDelegateFS):
    def _tag_to_dir(self,tag):
        return tag.name

    def _dir_to_tag(self,dirname):
        return self.store.get_tag_by_name(dirname)

    def getattr(self, path,parts,depth,st):
        if depth==2:
            # /tag/[tag.name]
            st.st_mode = stat.S_IFDIR | 0555
            st.st_nlink = 2 
            tag=self._dir_to_tag(parts[1])
            if tag==None:
                return False
        elif depth==3:
            # /tag/[tag.name]/[article.filename]
            a=self._file_to_article(parts[2])
            LOG.debug(a)
            if a==None:
                return False
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
            # /tag
            dirlist.extend(sorted([t.name for t in self.store.get_all_tag()])) 
        elif depth==2:
            # /tag/[tag.name]
            t=self._dir_to_tag(parts[1])
            if t != None:
                    dirlist.extend( sorted([self._article_to_file(a) for a in t.articles]) )

    def read(self,path,parts,depth,length,offset):
        return self._read(parts[2],length,offset)

    def mkdir(self, path, parts, depth, mode):
        if depth==2:
            t=Tag(parts[1])
            self.store.store_tag(t)
            return True
        return False

class XLibrisFS(DelegatedFS):
    def __init__(self, store, settings, *args, **kw):
        paths={
        "all":AllArticleFS(store,settings),
        "author":AuthorFS(store,settings),
        "journal":JournalFS(store,settings),
        "tag":TagFS(store,settings),
        "publication_year":PubYearFS(store,settings),
#        "title":TitleFS(store,settings)
        }
        DelegatedFS.__init__(self, paths,*args, **kw)
        LOG.debug("Init complete.")


##   def getxattr(self, *args,**kwargs):
##       LOG.debug("getxattr: %s",args)
##       LOG.debug("getxattr: %s",kwargs)
##       return -errno.ENOENT
##
##   def listxattr(self,*args,**kwargs):
##       LOG.debug("listxattr: %s",args)
##       LOG.debug("listxattr: %s",kwargs)
##       return ['doi']
#
#   def getxattr(self, path, name, size):
#       LOG.debug("getxattr path: %s",path)
#       LOG.debug("getxattr name: %s",name)
#       LOG.debug("getxattr size: %d",size)
#       val = name.swapcase() + '@' + path
#       if size == 0:
#           # We are asked for size of the value.
#           return len(val)
#       return val
#
#
#   def listxattr(self, path, size):
#       LOG.debug("listxattr path: %s",path)
#       LOG.debug("listxattr size: %d",size)
#       # We use the "user" namespace to please XFS utils
#       aa = ["user." + a for a in ("foo", "bar")]
#       if size == 0:
#           # We are asked for size of the attr list, ie. joint size of attrs
#           # plus null separators.
#           return len("".join(aa)) + len(aa)
#       return aa
#
#   def getattr(self, path):
#       """
#       - st_mode (protection bits)
#       - st_ino (inode number)
#       - st_dev (device)
#       - st_nlink (number of hard links)
#       - st_uid (user ID of owner)
#       - st_gid (group ID of owner)
#       - st_size (size of file, in bytes)
#       - st_atime (time of most recent access)
#       - st_mtime (time of most recent content modification)
#       - st_ctime (platform dependent; time of most recent metadata change on Unix,
#                   or the time of creation on Windows).
#       """
#       LOG.debug("getattr: %s",path)
#       parts=get_path_parts(path)
#       depth=len(parts)
#
#       st = MyStat()
#       st.st_uid = self.uid
#       st.st_gid = self.gid
#
#       if path == '/' or path in ROOT:
#           st.st_mode = stat.S_IFDIR | 0755
#           st.st_nlink = 2 
#       elif depth==2 and parts[0]=="author":
#           d=parts[1]
#           surname,given_name=[ unicode(n.strip(),"utf-8") for n in d.split(',') ]
#           author=self.store.find_author(given_name,surname)
#           if not author:
#               return -errno.ENOENT
#           st.st_mode = stat.S_IFDIR | 0755
#           st.st_nlink = 2 
#           st.st_mode = stat.S_IFREG | 0444
#           st.st_nlink = 1 
#           st.st_size = 42
#       else:
#           return -errno.ENOENT
#       return st
#
#   def readdir(self,path,offset):
#       LOG.debug("readattr: %s (%d)",path,offset)
#       dirlist=['.','..']
#       # The root directory
#       if path=='/':
#           dirlist.extend( [d[1:] for d in ROOT])
#       # The directories just under root
#       if path in ROOT:
#           if path=="/author":
#               dirlist.extend( [(a['surname']+', '+a['given_name']).encode("utf-8") for a in self.store.search_author()] )
#
#       LOG.debug(dirlist)
#       for r in dirlist:
#           yield fuse.Direntry(r)

#    def open ( self, path, flags ):
#        LOG.debug("unhandled open: %s",path)
#        return 0

#   def read ( self, path, length, offset ):
#       LOG.debug("read: %s (%d,%d)"%(path, length, offset))
#       return "hello world"

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

#    def mkdir ( self, path, mode ):
#        print '*** mkdir', path, oct(mode)
#        return -errno.ENOSYS

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
