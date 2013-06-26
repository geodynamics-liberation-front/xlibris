import time
from lazy_collections import LazyMap,LazyList
from . import LOG

class Journal(object):
	def __init__(self,title=None,abbreviation=None,issn=None,id=None,store=None):
		self.id=id
		self._store=store
		self.title=title
		self.abbreviation=abbreviation
		self._issn=None
		self._issues=None
		if issn:
			self._issn={}
			self._issn.update(issn)

	def __getattr__(self,name):
		if name=='issn':
			if not self._issn:
				self._issn=self._store.get_issn_from_journal(self)
			return self._issn
		elif name=='issues':
			if not self._issues:
				self._issues=self._store.get_issue_from_journal(self)
			return self._issues
		raise AttributeError(name)

class Issue(object):
	def __init__(self,volume=None,issue=None,journal=None,publications=None,articles=None,id=None,store=None):
		self.id=id
		self._store=store
		self.volume=volume
		self.issue=issue
		self._journal=journal
		self._articles=articles
		if publications:
			self._publications={}
			self._publications.update(publications)

	def add_publication(self,pub):
		if not self._publications:
			self._load_publications()
		self._publications[pub.media_type]=pub

	def _load_publications(self):
		if not self._publications:
			self._publications=self._store.get_issue_publications(self)

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

class Article(object):
	def __init__(self,doi=None,title=None,url=None,issue=None,filename=None,publications=None,authors=None,tags=None,id=None,store=None):
		self.id=id
		self._store=store
		self.doi=doi
		self.title=title
		self.url=url
		self.filename=filename
		self._tags=tags
		self._authors=authors
		self._issue=issue
		if publications:
			self._publications={}
			self._publications.update(publications)
		else:
			self._publications=None

	def add_publication(self,pub):
		if not self._publications:
			self._load_publications()
		self._publications[pub.media_type]=pub

	def get_earliest_publication(self):
		if not self._publications:
			self._load_publications()
		sorted_pub=sorted(self._publications.values(),key=lambda p: p.time())
		return sorted_pub[0]

	def _load_publications(self):
		if not self._publications:
			self._publications=self._store.get_article_publication_from_article(self)

	def __getattr__(self,name):
		if name=='publications':
			if not self._publications:
				self._load_publications()
			return self._publications
		elif name=='authors':
			if not self._authors:
				self._authors=self._store.get_author_from_article(self)
			return self._authors
		elif name=='tags':
			if not self._tags:
				self._tags=self._store.get_tag_from_article(self)
			return self._tags
		elif name=='issue':
			if not self._issue:
				self._issue=self._store.get_issue_from_article(self)
			return self._issue
		raise AttributeError(name)

class Author(object):
	def __init__(self,given_name=None,surname=None,id=None,store=None):
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

class Publication(object):
	def __init__(self,media_type=None,year=None,month=None,day=None,id=None,store=None):
		self.id=id
		self.media_type=media_type
		self.year=year
		self.month=month
		self.day=day

	def time(self):
		day=1 if self.day==None else self.day
		month=1 if self.month==None else self.month
		year=1970 if self.year==None else self.year
		return time.mktime(time.strptime("%s %s %s"%(day,month,year),"%d %m %Y"))


class Tag(object):
	def __init__(self,name,articles=None,id=None,store=None):
		self.id=id
		self._store=store
		self.name=name
		self._articles=articles

	def __getattr__(self,name):
		if name=='articles':
			if not self._articles:
				self._articles=self._store.get_article_from_tag(self)
			return self._articles
		raise AttributeError(name)

	
class XLibrisStore(object):
	def __init__(self,xlibris_db):
		self.db=xlibris_db

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
		i=Issue()
		i._store=self
		i.id=row['id']
		i.volume=row['volume']
		i.issue=row['issue']
		return i

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
	def journal_from_row(self,row):
		j=Journal()
		j._store=self
		j.id=row['id']
		j.title=row['title']
		j.abbreviation=row['abbreviation']
		return j

#
# ISSN methods
#
	def get_issn_from_journal(self,journal):
		return { r['media_type']:r['number'] for r in self.db.get_issn_from_journal(journal.id) }


#
# Article methods
#
	def get_article(self,id):
		return self.article_from_row(self.db.get_article(id))
	def get_all_article(self):
		return [self.article_from_row(r) for r in self.db.get_all_article()]
	def get_article_from_issue(self,issue):
		return LazyList(self.get_article,[r['id'] for r in self.db.get_article_from_issue(issue.id)])
	def get_article_from_author(self,author):
		return LazyList(self.get_article,[r['id'] for r in self.db.get_article_from_author(author.id)])
	def get_article_from_author_by_title(self, author,title):
		return self.article_from_row(self.db.get_article_from_author_by_title(author.id,title))
	def get_article_by_filename(self,filename):
		return self.article_from_row(self.db.get_article_by_filename(filename))
	def article_from_row(self,row):
		a=Article()
		a._store=self
		a.id=row['id']
		a.doi=row['doi']
		a.title=row['title']
		a.url=row['url']
		a.filename=row['filename']
		return a
#TODO:move to db
	def get_articles_from_year(self,year):
		table_col=self.db._get_columns("article")
		sql="""SELECT DISTINCT %s
			   FROM article 
			   JOIN article_publication ON article.id=article_publication.article_id 
			   WHERE article_publication.year=?"""%','.join(['article.'+c for c in table_col])
		return [self.article_from_row(r) for r in self.db._select(sql,table_col,(year,))]

#
# Article Publication methods
#
	def get_article_publication(self,id):
		return self.publication_from_row(self.db.get_article_publication(id))
#TODO:move to db
	def get_article_publication_from_article(self,article):
		return LazyMap(self.get_article_publication,{r['media_type']:r['id'] for r in self.db.get_article_publication_from_article(article.id)})
	

#
# Publication methods
#
	def get_publication_years(self):
		return [r['year'] for r in self.db._select("SELECT DISTINCT year FROM article_publication",['year'],())]
	def publication_from_row(self,row):
		pub=Publication()
		pub.id=row['id']
		pub.media_type=row['media_type']
		pub.year=row['year']
		pub.month=row['month']
		pub.day=row['day']
		return pub

#
# Author methods
#
	def get_author(self,id):
		return self.author_from_row(self.db.get_author(id))
	def get_all_author(self):
		return [self.author_from_row(r) for r in self.db.get_all_author()]
	def search_author(self,given_name=None,surname=None):
		return [self.author_from_row(r) for r in self.db.search_author(given_name,surname)]
	def get_author_from_article(self,article):
		return LazyList(self.get_author,[r['id'] for r in self.db.get_author_from_article(article.id)])
	def get_author_by_name(self,given_name,surname):
		return self.author_from_row(self.db.get_author_by_name(given_name,surname))
	def author_from_row(self,row):
		a=Author()
		a._store=self
		a.id=row['id']
		a.given_name=row['given_name']
		a.surname=row['surname']
		return a

#
# Tag methods
#
	def get_tag(self,id):
		return self.tag_from_row(self.db.get_tag(id))
	def get_tag_from_article(self,article):
		return LazyList(self.get_tag,[r['id'] for r in self.db.get_tag_from_article(article.id)])
	def tag_from_row(self,row):
		t=Tag()
		t._store=self
		t.name=row['name']
		return t

#
#  Update methods
#
	def add_article(self,article):
		issue=article.issue
		journal=issue.journal
		#
		# Import journal (if necessary)
		# 
		issn_row=self.db.find_issn(journal.issn.values()[0])
		if issn_row==None:
			journal_id=self.db.add_journal(journal)
			for media_type,issn in journal.issn.iteritems():
				self.db.add_issn(issn,media_type,journal_id)
		else:
			journal_id=issn_row['journal_id']
			LOG.debug("Journal '%s' found with id %d"%(journal.title,journal_id))

		#
		# Import Issue (if necessary)
		#
		issue_row=self.db.find_journal_issue_vol(journal_id,issue.issue,issue.volume)
		if issue_row==None:
			issue_id=self.db.add_issue(issue,journal_id)
			for media_type,pub in issue.publications.iteritems():
				self.db.add_issue_publication(media_type,pub,issue_id)
		else:
			issue_id=issue_row['id']
			LOG.debug("Issue issue: %s, vol: %s with id %d"%(issue.issue,issue.volume,issue_id))

		#
		# Import Article if necessary
		#
		article_row=self.db.find_article(article.doi)
		if article_row==None:
			article_id=self.db.add_article(article,issue_id)
			for media_type,pub in article.publications.iteritems():
				self.db.add_article_publication(media_type,pub,issue_id)
			#
			# Add authors as necessary
			#
			for position,author in enumerate(article.authors):
				author_row=self.db.find_author(author.given_name,author.surname)
				if author_row==None:
					author_id=self.db.add_author(author)
				else:
					author_id=author_row['id']
				self.add_author_article(article_id,author_id,position)
			for tag in article.tags:
				tag_row=self.db.find_tag(tag)
				if tag_row==None:
					tag_id=self.db.add_tag(tag)
				else:
					tag_id=tag_row['id']
				self.db.add_article_tag(article_id,tag_id)
		else:
			article_id=article_row['id']
			LOG.debug("Found article '%s' doi:%s with id %d"%(article.title,article.doi,article_id))
		return article_id

