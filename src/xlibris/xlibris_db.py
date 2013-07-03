# vim: set fileencoding=utf-8 :
from database import Database
#from . import LOG

"""
Database Diagram : http://yuml.me/edit/f64b6ce7

[article|⚷ id : INTEGER;doi : TEXT UNIQUE;title : TEXT;url : TEXT;filename : TEXT; issue_id : INTEGER]
[article_publication|⚷ id : INTEGER;article_ID : INTEGER;year : INTEGER;month : INTEGER;day : INTEGER;media_type : TEXT] 
[author_article|author_id : INTEGER;article_id : INTEGER] 
[author|⚷ id : INTEGER;given_name : TEXT;surname : TEXT] 
[article_tag|article_id : INTEGER;tag_id : INTEGER] 
[tag|⚷ id : INTEGER;name : TEXT UNIQUE] 
[issue|⚷ id : INTEGER ;journal_id : INTEGER;volume : TEXT; issue : TEXT]
[issue_publication|⚷ id : INTEGER;issue_ID : INTEGER;year : INTEGER;month : INTEGER;day : INTEGER;media_type : TEXT] 
[journal|⚷ id : INTEGER;title : TEXT UNIQUE;abbreviation : TEXT]
[issn|⚷ id : INTEGER;journal_id : INTEGER;number : TEXT UNIQUE; media_type : TEXT]
[journal]1 id-∞ journal_id[issn]
[journal]1 id-∞ journal_id[issue]
[issue]1 id-∞ issue_id[issue_publication]
[issue]1 id-∞ issue_id[article]
[article]1 id-∞ article_id[article_publication]
[article]1 id-∞ article_id[article_tag]
[article]1 id-∞ article_id[author_article]
[author]1 id-∞ author_id[author_article]
[tag]1 id-∞ tag_id[article_tag]

"""

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
                   ('alias_to','INTEGER'),
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
                        ('tag_id','INTEGER'),
                        ('UNIQUE','(article_id,tag_id)')],
        }
        super(XLibrisDB,self).__init__(db,tables)


# 
# Journal Methods
#
    def add_journal(self,title,abbreviation):
        return self._insert('journal',[title,abbreviation])
    def get_journal(self,id):
        return self._get_row('journal',equal={'id':id})
    def get_all_journal(self):
        return self._get_rows('journal',{},{})
    def get_journal_by_title(self,title):
        return self._get_row('journal',equal={'title':title})
    def get_journal_from_issue(self,issue_id):
        return self._one_from_many("journal","issue",issue_id)
    def get_journal_from_issn(self,numbers):
        journal_cols=self._get_columns('journal')
        select= ','.join(['journal.'+c for c in journal_cols])
        in_clause= '(' + ( ','.join(['?']*len(numbers)) ) + ')'
        sql="""SELECT DISTINCT %s 
               FROM journal 
               JOIN issn ON journal.id=issn.journal_id 
               WHERE issn.number IN %s"""%(select,in_clause) 
        rows=self._select(sql,journal_cols,tuple(numbers))
        return None if len(rows)==0 else rows[0]
    def search_journal_by_title(self,title):
        return self._get_rows('journal',like={'title':title},equal={})
    def update_journal(self,id,title,abbreviation):
        return self._update('journal',{'title':title,'abbreviation':abbreviation},{'id':id})

# 
# ISSN Methods
#
    def add_issn(self,number,media_type,journal_id):
        return self._insert('issn',[journal_id,number,media_type])
    def get_issn(self,id):
        return self._get_row('issn',equal={'id':id})
    def get_issn_by_number(self,number):
        return self._get_row('issn',equal={'number':number})
    def get_issn_from_journal(self,journal_id):
        return self._get_rows('issn',like={},equal={'journal_id':journal_id})
    def delete_issn_from_journal(self,journal_id):
        self._delete('issn',{'journal_id':journal_id})

#
# Issue Methods
#
#[issue|⚷ id : INTEGER ;journal_id : INTEGER;volume : TEXT; issue : TEXT]
    def add_issue(self,journal_id,volume,issue):
        return self._insert('issue',[journal_id,volume,issue])
    def get_issue(self,id):
        return self._get_row('issue',equal={'id':id})
    def get_issue_from_journal(self,journal_id):
        return self._get_rows('issue',like={},equal={'journal_id':journal_id})
    def get_issue_from_article(self,article_id):
        return self._one_from_many('issue','article',article_id)
    def get_issue_from_issue_publication(self,pub_id):
        return self._one_from_many("issue","issue_publication",pub_id)
    def get_issue_from_journal_by_issue_vol(self,journal_id,volume,issue):
        return self._get_row('issue',equal={'journal_id':journal_id,'volume':volume,'issue':issue})
    def update_issue(self,id,journal_id,volume,issue):
        return self._update('issue',{'journal_id':journal_id,'issue':issue,'volume':volume},{'id':id})

#
# Issue Publication Methods
#
    def add_issue_publication(self,media_type,year,month,day,issue_id):
        return self._insert('issue_publication',[issue_id,year,month,day,media_type])
    def get_issue_publication(self,id):
        return self._get_row('issue_publication',equal={'id':id})
    def get_issue_publication_from_issue(self,issue_id):
        return self._get_rows('issue_publication',like={},equal={'issue_id':issue_id})
    def get_issue_publication_from_issue_by_media_type(self,issue_id,media_type):
        return self._get_row('issue_publication',equal={'issue_id':issue_id,'media_type':media_type})
    def update_issue_publication(self,id,media_type,year,month,day,issue_id):
        return self._update('issue_publication',{'issue_id':issue_id,
                                                  'media_type':media_type,
                                                  'year':year,
                                                  'month':month,
                                                  'day':day},{'id':id})

#
# Author Methods
#
    def add_author(self,given_name,surname,alias_to=None):
        return self._insert('author',[given_name,surname,alias_to])
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
    def update_author(self,id,given_name,surname):
        return self._update('author',{'given_name':given_name,'surname':surname},{'id':id})

#
# Author Article Methods
#
    def add_author_article(self,article_id,author_id,position):
        return self._insert('author_article',[article_id,author_id,position])
    def get_author_article(self,id):
        return self._get_row('author_article',equal={'id':id})
    def get_article_from_year(self,year):
        return self._simple_join('article','article_publication',year,t2id='year')
    def delete_author_article_from_author(self,author_id):
        self._delete('author_article',{'author_id':author_id})
    def delete_author_article_from_article(self,article_id):
        self._delete('author_article',{'article_id':article_id})

#
# Tag Methods
#
    def add_tag(self,tag):
        return self._insert('tag',[tag])
    def get_tag(self,id):
        return self._get_row('tag',equal={'id':id})
    def get_all_tag(self):
        return self._get_rows('tag',{},{})
    def get_tag_by_name(self,name):
        return self._get_row('tag',equal={'name':name})
    def get_tag_from_article(self,article_id):
        return self._simple_join("tag","article_tag",article_id,"article_id")
    def search_tag(self,tag):
        return self._get_rows('tag',like={'tag':tag},equal={})
    def update_tag(self,id,name):
        return self._update('tag',{'name':name},{'id':id})

# 
# Article Tag Methods
# 
    def add_article_tag(self,article_id,tag_id):
        return self._insert('article_tag',[article_id,tag_id])
    def get_article_tag(self,id):
        return self._get_row('article_tag',equal={'id':id})

#
# Article Methods
#
    def add_article(self,doi,title,url,filename,issue_id):
        return self._insert('article',[doi,title,url,filename,issue_id])
    def get_article(self,id):
        return self._get_row('article',equal={'id':id})
    def get_all_article(self):
        return self._get_rows('article',{},{})
    def get_article_by_doi(self,doi):
        return self._get_row('article',equal={'doi':doi})
    def get_article_by_filename(self,filename):
        return self._get_row('article',equal={'filename':filename})
    def get_article_from_tag(self,tag_id):
        return self._simple_join("article","article_tag",tag_id,"tag_id")
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
    def update_article(self,id,doi,title,url,filename):
        return self._update('article',{'doi':doi,'title':title,'url':url,'filename':filename},{'id':id})

#
# Article Publication Methods
#
    def add_article_publication(self,media_type,year,month,day,article_id):
        return self._insert('article_publication',[article_id,year,month,day,media_type])
    def get_article_publication(self,id):
        return self._get_row('article_publication',equal={'id':id})
    def get_article_publication_from_article(self,article_id):
        return self._get_rows('article_publication',like={},equal={'article_id':article_id})
    def get_article_publication_from_article_by_media_type(self,issue_id,media_type):
        return self._get_row('article_publication',equal={'article_id':issue_id,'media_type':media_type})
    def update_article_publication(self,id,media_type,year,month,day,article_id):
        return self._update('article_publication',{'article_id':article_id,
                                                  'media_type':media_type,
                                                  'year':year,
                                                  'month':month,
                                                  'day':day},{'id':id})
