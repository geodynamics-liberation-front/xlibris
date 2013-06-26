from database import Database
from doi import Journal,Issue,Article,Author,Publication
from . import LOG

class XLibrisDB(Database):
	def __init__(self,db):
		tables={
		'journal': [('id','INTEGER PRIMARY KEY'),
					('title','TEXT UNIQUE'), 
					('abbreviation','TEXT')],
		'issn': [('id','INTEGER PRIMARY KEY'),
				 ('journal_id','INTEGER'),
		         ('number','TEXT UNIQUE'),
				 ('media_type','TEXT')],
		'issue': [('id','INTEGER PRIMARY KEY'),
						  ('journal_id','INTEGER'),
						  ('volume','TEXT'),
						  ('issue','TEXT'),
						  ('UNIQUE','(volume,issue)')],
		'issue_publication': [('id','INTEGER PRIMARY KEY'),
								('issue_id','INTEGER'),
								('year','INTEGER'),
								('month','INTEGER'),
								('day','INTEGER'),
								('media_type','TEXT'),
								('UNIQUE','(issue_id,media_type)')],
		'author': [('id','INTEGER PRIMARY KEY'),
				   ('given_name','TEXT'),
				   ('surname','TEXT'),
				   ('UNIQUE','(given_name,surname)')],
		'author_article': [('article_id','INTEGER'),
						   ('author_id','INTEGER'),
						   ('author_position','INTEGER')],
		'article': [('id','INTEGER PRIMARY KEY'),
					('doi','TEXT UNIQUE'),
					('title','TEXT'),
					('url','TEXT'),
					('filename','TEXT'),
					('issue_id','INTEGER')],
		'article_publication': [('id','INTEGER PRIMARY KEY'),
								('article_id','INTEGER'),
								('year','INTEGER'),
								('month','INTEGER'),
								('day','INTEGER'),
								('media_type','TEXT'),
								('UNIQUE','(article_id,media_type)')],
		'tag': [('id','INTEGER PRIMARY KEY'),
				('name','TEXT UNIQUE')],
		'article_tag': [('article_id','INTEGER'),
						('tag_id','INTEGER')],
		}
		super(XLibrisDB,self).__init__(db,tables)

	def import_article(self,article):
		issue=article.issue
		journal=issue.journal

		#
		# Import journal (if necessary)
		# 
		issn_row=self.find_issn(journal.issn.values()[0])
		if issn_row==None:
			journal_id=self.add_journal(journal)
			for media_type,issn in journal.issn.iteritems():
				self.add_issn(issn,media_type,journal_id)
		else:
			journal_id=issn_row['journal_id']
			LOG.debug("Journal '%s' found with id %d"%(journal.title,journal_id))

		#
		# Import Issue (if necessary)
		#
		issue_row=self.find_journal_issue_vol(journal_id,issue.issue,issue.volume)
		if issue_row==None:
			issue_id=self.add_issue(issue,journal_id)
			for media_type,pub in issue.publications.iteritems():
				self.add_issue_publication(media_type,pub,issue_id)
		else:
			issue_id=issue_row['id']
			LOG.debug("Issue issue: %s, vol: %s with id %d"%(issue.issue,issue.volume,issue_id))

		#
		# Import Article if necessary
		#
		article_row=self.find_article(article.doi)
		if article_row==None:
			article_id=self.add_article(article,issue_id)
			for media_type,pub in article.publications.iteritems():
				self.add_article_publication(media_type,pub,issue_id)
			#
			# Add authors as necessary
			#
			for position,author in enumerate(article.authors):
				author_row=self.find_author(author.given_name,author.surname)
				if author_row==None:
					author_id=self.add_author(author)
				else:
					author_id=author_row['id']
				self.add_author_article(article_id,author_id,position)
			for tag in article.tags:
				tag_row=self.find_tag(tag)
				if tag_row==None:
					tag_id=self.add_tag(tag)
				else:
					tag_id=tag_row['id']
				self.add_article_tag(article_id,tag_id)
		else:
			article_id=article_row['id']
			LOG.debug("Found article '%s' doi:%s with id %d"%(article.title,article.doi,article_id))
		return article_id

	def get_article_info(self,doi):
		article=None
		ar=self.find_article(doi)
		if ar!=None:
			article=Article(ar['doi'],ar['title'],ar['url'],None,ar['filename'],id=ar['id'])
			# Get the publication dates
			for p in self.get_article_publications(ar['id']):
				article.publications[p['media_type']]=Publication(p['media_type'],p['year'],p['month'],p['day'],p['id'])
			# Get the author(s)
			for author_row in self.get_article_authors(ar['id']):
				author=Author(author_row['given_name'],author_row['surname'],author_row['id'])
				article.authors.append(author)
			# Get the Issue
			i_row=self.get_issue(ar['issue_id'])
			article.issue=Issue(i_row['volume'],i_row['issue'],id=i_row['id'])
			# Get the issue publication dates
			for p in self.get_issue_publications(i_row['id']):
				article.issue.publications[p['media_type']]=Publication(p['media_type'],p['year'],p['month'],p['day'],p['id'])
			# Get the journal
			j=self.get_journal(i_row['journal_id'])
			article.issue.journal=Journal(j['title'],j['abbreviation'],id=j['id'])
			# Get the journal issn
			for issn_row in self.find_journal_issn(j['id']):
				article.issue.journal.issn[issn_row['media_type']]=issn_row['number']
		return article

# 
# Journal Methods
#
	def add_journal(self,journal):
		LOG.debug("Adding journal '%s'"%(journal.title))
		return self._add('journal',[journal.title,journal.abbreviation])
	def get_journal(self,id):
		return self._get_row('journal',equal={'id':id})
	def get_all_journal(self):
		return self._get_rows('journal',{},{})
	def get_journal_by_title(self,title):
		return self._get_row('journal',equal={'title':title})
	def get_journal_from_issue(self,issue_id):
		return self._one_from_many("journal","issue",issue_id)
	def search_journal_from_title(self,title):
		return self._get_rows('journal',like={'title':title},equal={})

# 
# ISSN Methods
#
	def add_issn(self,issn,media_type,journal_id):
		LOG.debug("Adding ISSN: %s %s"%(media_type,issn))
		return self._add('issn',[journal_id,issn,media_type])
	def get_issn(self,id):
		return self._get_row('issn',equal={'id':id})
	def get_issn_from_number(self,number):
		return self._get_row('issn',equal={'number':number})
	def get_issn_from_journal(self,journal_id):
		return self._get_rows('issn',like={},equal={'journal_id':journal_id})

#
# Issue Methods
#
	def add_issue(self,issue,journal_id):
		return self._add('issue',[journal_id,issue.volume,issue.issue])
	def get_issue(self,id):
		return self._get_row('issue',equal={'id':id})
	def get_issue_from_journal(self,journal_id):
		return self._get_rows('issue',like={},equal={'journal_id':journal_id})
	def get_issue_from_article(self,article_id):
		return self._one_from_many('issue','article',article_id)
	def get_issue_from_issue_publication(self,pub_id):
		return self._one_from_many("issue","issue_publication",pub_id)
	def get_issue_from_issue_vol(self,journal_id,issue,volume):
		return self._get_row('issue',equal={'journal_id':journal_id,'volume':volume,'issue':issue})

#
# Issue Publication Methods
#
	def add_issue_publication(self,media_type,pub,issue_id):
		return self._add('issue_publication',[issue_id,pub.year,pub.month,pub.day,media_type])
	def get_issue_publication(self,id):
		return self._get_row('issue_publication',equal={'id':id})
	def get_issue_publication_from_issue(self,issue_id):
		return self._get_rows('issue_publication',like={},equal={'issue_id':issue_id})

#
# Author Methods
#
	def add_author(self,author):
		LOG.debug("Adding author %s, %s"%(author.surname,author.given_name))
		return self._add('author',[author.given_name,author.surname])
	def get_author(self,id):
		return self._get_row('author',equal={'id':id})
	def get_all_author(self):
		return self._get_rows('author',{},{})
	def get_author_from_article(self,article_id):
		select_tables=['author']
		join_tables=['author_article']
		joins= [('author.id','author_article.author_id')]
		equal={'author_article.article_id':article_id}
		orderby=['author_article.author_position']
		return self._join_rows(select_tables,join_tables,joins,equal=equal,orderby=orderby)
	def get_author_by_name(self,given_name=None,surname=None):
		equal={}
		if given_name!=None: equal['given_name']=given_name
		if surname!=None: equal['surname']=surname
		return self._get_row('author',equal=equal)
	def search_author(self,given_name=None,surname=None):
		like={}
		if given_name!=None: like['given_name']=given_name
		if surname!=None: like['surname']=surname
		return self._get_rows('author',like=like,equal={})

#
# Author Article Methods
#
	def add_author_article(self,article_id,author_id,position):
		return self._add('author_article',[article_id,author_id,position])
	def get_author_article(self,id):
		return self._get_row('author_article',equal={'id':id})

#
# Tag Methods
#
	def add_tag(self,tag):
		return self._add('tag',[tag])
	def get_tag(self,id):
		return self._get_row('tag',equal={'id':id})
	def get_tag_by_name(self,name):
		return self._get_row('tag',equal={'name':name})
	def get_tag_from_article(self,article_id):
		return self._simple_join("tag","article_tag",article_id,"article_id")
	def search_tag(self,tag):
		return self._get_rows('tag',like={'tag':tag},equal={})

# 
# Article Tag Methods
# 
	def add_article_tag(self,article_id,tag_id):
		return self._add('article_tag',[article_id,tag_id])
	def get_article_tag(self,id):
		return self._get_row('article_tag',equal={'id':id})

#
# Article Methods
#
	def add_article(self,article,issue_id):
		LOG.debug("Adding article '%s' doi:%s"%(article.title,article.doi))
		return self._add('article',[article.doi,article.title,article.url,article.filename,issue_id])
	def get_article(self,id):
		return self._get_row('article',equal={'id':id})
	def get_all_article(self):
		return self._get_rows('article',{},{})
	def get_article_by_doi(self,doi):
		return self._get_row('article',equal={'doi':doi})
	def get_article_by_filename(self,filename):
		return self._get_row('article',equal={'filename':filename})
	def get_article_from_author(self,author_id):
		return self._simple_join("article","author_article",author_id,"author_id")
	def get_article_from_author_by_title(self,author_id,title):
		select_tables=['article']
		join_tables=['author_article']
		joins=[('article.id','author_article.article_id')]
		equal={'author_article.author_id':author_id,'article.title':title}
		rows=self._join_rows(select_tables,join_tables,joins,equal=equal)
		return  None if len(rows)==0 else rows[0]
	def get_article_from_issue(self,issue_id):
		return self._get_rows("article",{},{"issue_id":issue_id})

#
# Article Publication Methods
#
	def add_article_publication(self,media_type,pub,article_id):
		return self._add('article_publication',[article_id,pub.year,pub.month,pub.day,media_type])
	def get_article_publication(self,id):
		return self._get_row('article_publication',equal={'id':id})
	def get_article_publication_from_article(self,article_id):
		return self._get_rows('article_publication',like={},equal={'article_id':article_id})
