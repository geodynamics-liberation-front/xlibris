# vim: set fileencoding=utf-8 :
import sqlite3
import time
from lazy_collections import LazyMap,LazyList
from . import LOG

"""
Class Diagram : http://yuml.me/edit/173cefd2


[Article|doi;title;url;filename]
[Issue|volume;issue]
[Publication|media_type;year;month;day]
[Issue_Publication]
[Article_Publication]
[Journal|title;abbreviation]
[ISSN|media_type;number]
[Tag|name]
[Issue_publication]->[Publication]
[Article_publication]->[Publication]
[Author|given_name;surname]
[Article]issues-issue[Issue]
[Article]tags-articles[Tag]
[Article]authors-articles[Author]
[Article]publications-[Article_publication]
[Issue]journal-issues[Journal]
[Issue]publications-[Issue_publication]
[Journal]issn-[ISSN]
"""

class ISSNDict(dict):
    def __init__(self, *args, **kw):
        d=dict(*args, **kw)
        for k,v in d.iteritems():
            self[k]=v

    def __setitem__(self,key,value):
            try:
                value=value.replace('-','')
            except: 
                pass
            dict.__setitem__(self,key,value)

class Journal(object):
    def __init__(self,title,abbreviation,id=None,store=None):
        self.id=id
        self._store=store
        self.title=title
        self.abbreviation=abbreviation
        self._issn=None
        self._issues=None

    def __getattr__(self,name):
        if name=='issn':
            if not self._issn:
                if self._store:
                    self._issn=self._store.get_issn_from_journal(self)
                else:
                    self._issn=ISSNDict()
            return self._issn
        elif name=='issues':
            if not self._issues:
                if self._store:
                    self._issues=self._store.get_issue_from_journal(self)
                else:
                    self._issues=[]
            return self._issues
        raise AttributeError(name)

    def __setattr__(self,name,value):
        if name=='issues':
            self._issues=value
        else: 
            object.__setattr__(self,name,value)

    def __str__(self):
        return "XLibrisJournal(%s)" % self.title

class Issue(object):
    def __init__(self,volume,issue,id=None,store=None):
        self.id=id
        self._store=store
        self.volume=volume
        self.issue=issue
        self._journal=None
        self._articles=None
        self._publications=None

    def add_publication(self,pub):
        if not self._publications:
            self._load_publications()
        self._publications[pub.media_type]=pub

    def _load_publications(self):
        if not self._publications:
            if self._store:
                self._publications=self._store.get_publications_from_issue(self)
            else:
                self._publications={}

    def __getattr__(self,name):
        if name=='publications':
            if not self._publications:
                self._load_publications()
            return self._publications
        elif name=='journal':
            if not self._journal:
                self._journal=self._store.get_journal_from_issue(self)
            return self._journal
        elif name=='articles':
            if not self._articles:
                self._articles=self._store.get_article_from_issue(self)
            return self._articles
        raise AttributeError(name)

    def __setattr__(self,name,value):
        if name=='journal':
            self._journal=value
        else: 
            object.__setattr__(self,name,value)

    def __str__(self):
        return "XLibrisIssue(vol %s, issue %s)" % (self.volume, self.issue)

class Article(object):
    def __init__(self,doi,title,url,filename,first_page,last_page,id=None,store=None):
        self.id=id
        self._store=store
        self.doi=doi
        self.title=title
        self.url=url
        self.filename=filename
        self.first_page=first_page
        self.last_page=last_page
        self._tags=None
        self._authors=None
        self._issue=None
        self._publications=None

    def add_publication(self,pub):
        if not self._publications:
            self._load_publications()
        self._publications[pub.media_type]=pub

    def get_publication_year(self):
        if 'print' in self.publications:
            year=self.publications['print'].year
        elif 'print' in self.issue.publications:
            year=self.issue.publications['print'].year
        else:
            year=sorted([p.year for p in self.issue.publications.values()]+
                        [p.year for p in self.publications.values()])[0]
        return year

    def get_earliest_publication(self):
        if not self._publications:
            self._load_publications()
        sorted_pub=sorted(self._publications.values(),key=lambda p: p.time())
        return sorted_pub[0]

    def _load_publications(self):
        if not self._publications:
            if self._store:
                self._publications=self._store.get_article_publication_from_article(self)
            else:
                self._publications={}

    def __getattr__(self,name):
        if name=='publications':
            if not self._publications:
                self._load_publications()
            return self._publications
        elif name=='authors':
            if not self._authors:
                if self._store:
                    self._authors=self._store.get_author_from_article(self)
                else:
                    self._authors=[]
            return self._authors
        elif name=='tags':
            if not self._tags:
                self._tags=self._store.get_tag_from_article(self)
            return self._tags
        elif name=='issue':
            if not self._issue:
                self._issue=self._store.get_issue_from_article(self)
            return self._issue
        elif name=='earliest_publication':
            return self.get_earliest_publication()
        raise AttributeError(name)

    def __setattr__(self,name,value):
        if name=='issue':
            self._issue=value
        else: 
            object.__setattr__(self,name,value)

    def __str__(self):
        return "XLibrisArticle('%s', doi:%s)" % (self.title, self.doi)

class Author(object):
    def __init__(self,given_name,surname,id=None,store=None):
        self.id=id
        self._store=store
        self.given_name=given_name
        self.surname=surname
        self._articles=None

    def __getattr__(self,name):
        if name=='articles':
            if not self._articles:
                self._articles=self._store.get_article_from_author(self)
            return self._articles
        raise AttributeError(name)

    def __hash__(self):
        return self.surname.__hash__() + self.given_name.__hash__()
    
    def __eq__(self,other):
        return self.__hash__()==other.__hash__()

    def __ne__(self,other):
        return self.__hash__()!=other.__hash__()

    def __cmp__(self,other):
        return self.__hash__()-other.__hash__()

    def __str__(self):
        return "XLibrisAuthor(%s, %s)" % (self.surname, self.given_name)

class Publication(object):
    def __init__(self,media_type,year,month,day,id=None):
        self.id=id
        self.media_type=media_type
        self.year=year
        self.month=month
        self.day=day

    def time(self):
        day=1 if self.day==None or self.day=='' else self.day
        month=1 if self.month==None or self.month=='' else self.month
        year=1 if self.year==None or self.year=='' else self.year
        return time.mktime(time.strptime("%s %s %s"%(day,month,year),"%d %m %Y"))

    def __str__(self):
        return "XLibrisPublication(%s: %s-%s-%s)" % (self.media_type, self.year, self.month, self.day)

class Tag(object):
    def __init__(self,name,id=None,store=None):
        self.id=id
        self._store=store
        self.name=name
        self._articles=None

    def __getattr__(self,name):
        if name=='articles':
            if not self._articles:
                self._articles=self._store.get_article_from_tag(self)
            return self._articles
        raise AttributeError(name)

    def __str__(self):
        return "XLibrisTag(%s)" % self.name

    
class XLibrisStore(object):
    def __init__(self,xlibris_db):
        self.db=xlibris_db

    def __str__(self):
        return "XLibrisStore(%s)" % self.db

#
# Issue methods
#
    def get_issue(self,id):
        return self.issue_from_row(self.db.get_issue(id))
    def get_issue_from_journal(self,journal):
        return LazyList(self.get_issue,[r['id'] for r in self.db.get_issue_from_journal(journal.id)])
    def get_issue_from_issue_publication(self,publication):
        return self.issue_from_row(self.db.get_issue_from_issue_publication(publication.id))
    def get_issue_from_article(self,article):
        return self.issue_from_row(self.db.get_issue_from_article(article.id))
    def issue_from_row(self,row):
        if row==None: return None
        return Issue(row['volume'], row['issue'], id=row['id'], store=self)
    def store_issue(self,issue):
        # Update the journal
        self.store_journal(issue.journal)
        # Update the issue
        if issue.id == None:
            LOG.debug('Looking for existing Issue with volume:%s and issue:%s',issue.volume,issue.issue)
            issue_row=self.db.get_issue_from_journal_by_issue_vol(issue.journal.id,issue.volume,issue.issue)
            if issue_row:
                issue.id=issue_row['id']
                issue._store=self
                LOG.debug('Found Issue with id %s'%issue.id)
        if issue.id != None:
            self.db.update_issue(issue.id,issue.journal.id,issue.volume,issue.issue)
        else:
            issue.id=self.db.add_issue(issue.journal.id,issue.volume,issue.issue)
            issue._store=self
        # Update the publications
        if issue._publications:
            for media_type,pub in issue._publications.iteritems():
                if pub.id == None:
                    LOG.debug('Looking for existing Publication (issue_id:%s,media_type:%s)',issue.id,media_type)
                    pub_row=self.db.get_issue_publication_from_issue_by_media_type(issue.id,media_type)
                    if pub_row:
                        pub.id=pub_row['id']
                if pub.id != None:
                    self.db.update_issue_publication(pub.id,pub.media_type,pub.year,pub.month,pub.day,issue.id)
                else:
                    pub.id=self.db.add_issue_publication(pub.media_type,pub.year,pub.month,pub.day,issue.id)
        return issue.id

#
# Issue Publication methods
#
    def get_issue_publication(self,id):
        return self.publication_from_row(self.db.get_issue_publication(id))
    def get_issues_publication_from_issue(self,issue):
        return LazyMap(self.get_issue_publication,{r['media_type']:r['id'] for r in self.db.get_issue_publication_from_issue(issue.id)})

# 
# Journal methods
#
    def get_journal(self,id):
        return self.journal_from_row(self.db.get_journal(id))
    def get_all_journal(self):
        return [self.journal_from_row(j) for j in self.db.get_all_journal()]
    def get_journal_by_title(self,title):
        return self.journal_from_row(self.db.get_journal_by_title(title))
    def get_journal_from_issue(self,issue):
        return self.journal_from_row(self.db.get_journal_from_issue(issue.id))
    def get_journal_from_issn(self,number_seq):
        if type(number_seq)==str:
            number_seq=[number_seq]
        return self.journal_from_row(self.db.get_journal_from_issn(number_seq))
    def journal_from_row(self,row):
        if row==None: return None
        return Journal( row['title'], row['abbreviation'], id=row['id'], store=self)
    def store_journal(self,journal):
        # Update the journal
        if journal.id == None:
            if journal._issn:
                journal_row=self.db.get_journal_from_issn(journal._issn.values())
                if journal_row:
                    journal.id=journal_row['id']
                    journal._store=self
        if journal.id != None:
            self.db.update_journal(journal.id,journal.title,journal.abbreviation)
        else:
            journal.id=self.db.add_journal(journal.title,journal.abbreviation)
            journal._store=self
        # Update the issn
        if journal._issn:
            self.db.delete_issn_from_journal(journal.id)
            for media_type,number in journal._issn.iteritems():
                self.db.add_issn(number,media_type,journal.id)
        return journal.id

#
# ISSN methods
#
    def get_issn_from_journal(self,journal):
        return ISSNDict([(r['media_type'],r['number']) for r in self.db.get_issn_from_journal(journal.id)] )


#
# Article methods
#
    def get_article(self,id):
        return self.article_from_row(self.db.get_article(id))
    def get_all_article(self):
        return [self.article_from_row(r) for r in self.db.get_all_article()]
    def get_article_from_tag(self,tag):
        return LazyList(self.get_article,[r['id'] for r in self.db.get_article_from_tag(tag.id)])
    def get_article_from_issue(self,issue):
        return LazyList(self.get_article,[r['id'] for r in self.db.get_article_from_issue(issue.id)])
    def get_article_from_author(self,author):
        return LazyList(self.get_article,[r['id'] for r in self.db.get_article_from_author(author.id)])
    def get_article_from_author_by_title(self, author, title):
        return self.article_from_row(self.db.get_article_from_author_by_title(author.id, title))
    def get_article_by_filename(self,filename):
        return self.article_from_row(self.db.get_article_by_filename(filename))
    def article_from_row(self,row):
        if row==None: return None
        return Article( row['doi'], row['title'], row['url'], row['filename'], row['first_page'], row['last_page'], id=row['id'], store=self)
    def get_article_from_year(self,year):
        return [self.article_from_row(r) for r in self.db.get_article_from_year(year)]
    def store_article(self,article):
        # Update the issue
        self.store_issue(article.issue)
        # Update the article
        if article.id == None:
            article_row=self.db.get_article_by_doi(article.doi)
            if article_row:
                article.id=article_row['id']
                article._store=self
        if article.id != None:
            self.db.update_article(article.id,article.doi,article.title,article.url,article.filename,article.first_page,article.last_page)
        else:
            article.id=self.db.add_article(article.doi,article.title,article.url,article.filename,article.first_page,article.last_page,article.issue.id)
            article._store=self
        # Update the publications
        if article._publications:
            for media_type,pub in article._publications.iteritems():
                if pub.id == None:
                    LOG.debug('Looking for existing Publication (article_id:%s,media_type:%s)',article.id,media_type)
                    pub_row=self.db.get_article_publication_from_article_by_media_type(article.id,media_type)
                    if pub_row:
                        pub.id=pub_row['id']
                if pub.id !=None:
                    self.db.update_article_publication(pub.id,pub.media_type,pub.year,pub.month,pub.day,article.id)
                else:
                    pub.id=self.db.add_article_publication(pub.media_type,pub.year,pub.month,pub.day,article.id)
                    pub._store=self
        # Update the authors
        if article._authors:
            self.db.delete_author_article_from_article(article.id)
            for position,author in enumerate(article._authors):
                self.store_author(author)
                self.db.add_author_article(article.id,author.id,position)
        # Update the tags
        if article._tags:
            for tag in article._tags:
                self.store_tag(tag)
                self.db.add_article_tag(article.id,tag.id)
        return article.id

#
# Article Publication methods
#
    def get_article_publication(self,id):
        return self.publication_from_row(self.db.get_article_publication(id))
    def get_article_publication_from_article(self,article):
        return LazyMap(self.get_article_publication,{r['media_type']:r['id'] for r in self.db.get_article_publication_from_article(article.id)})
    

#
# Publication methods
#
    def get_publication_years(self):
        return [r['year'] for r in self.db._select("SELECT DISTINCT year FROM article_publication",['year'],())]
    def publication_from_row(self,row):
        if row==None: return None
        return Publication(row['media_type'], row['year'], row['month'], row['day'], id=row['id'])

#
# Author methods
#
    def get_author(self,id):
        return self.author_from_row(self.db.get_author(id))
    def get_all_author(self):
        return set([self.author_from_row(r) for r in self.db.get_all_author()])
    def search_author(self,given_name=None,surname=None):
        return set([self.author_from_row(r) for r in self.db.search_author(given_name,surname)])
    def get_author_from_article(self,article):
        return LazyList(self.get_author,[r['id'] for r in self.db.get_author_from_article(article.id)])
    def get_author_by_name(self,given_name,surname):
        return self.author_from_row(self.db.get_author_by_name(given_name,surname))
    def alias_author(self,source,dest):
        self.db.alias_author(source.id, dest.id)
    def author_from_row(self,row):
        if row==None: return None
        # Resolve alaias
        if row['alias_to']!=None and row['alias_to']!='':
            row=self.db.get_author(row['alias_to'])
        return Author(row['given_name'],row['surname'],id=row['id'],store=self)
    def store_author(self,author):
        # Update the journal
        if author.id == None:
            author_row=self.db.get_author_by_name(author.given_name,author.surname)
            if author_row != None:
                author.id=author_row['id']
                author._store=self
        if author.id != None:
            self.db.update_author(author.id,author.given_name,author.surname)
        else:
            author.id=self.db.add_author(author.given_name,author.surname)
            author._store=self
        return author.id

#
# Tag methods
#
    def get_tag(self,id):
        return self.tag_from_row(self.db.get_tag(id))
    def get_tag_by_name(self,name):
        return self.tag_from_row(self.db.get_tag_by_name(name))
    def get_all_tag(self):
        return [self.tag_from_row(r) for r in self.db.get_all_tag()]
    def get_tag_from_article(self,article):
        return LazyList(self.get_tag,[r['id'] for r in self.db.get_tag_from_article(article.id)])
    def tag_from_row(self,row):
        if row==None: return None
        return Tag(row['name'],id=row['id'],store=self)
    def store_tag(self,tag):
        # Update the tag
        if tag.id == None:
            tag_row=self.db.get_tag_by_name(tag.name)
            if tag_row:
                tag.id=tag_row['id']
                tag._store=self
        if tag.id != None:
            self.db.update_tag(tag.id,tag.name)
        else:
            tag.id=self.db.add_tag(tag.name)
            tag._store=self
        return tag.id
    def tag_article(self,article,tag):
        self.store_tag(tag)
        try:
            self.db.add_article_tag(article.id,tag.id)
        except sqlite3.IntegrityError:
            pass
