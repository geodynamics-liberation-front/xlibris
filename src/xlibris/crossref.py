#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
import urllib
import urllib2
from . import LOG
from bs4 import BeautifulSoup
from xlibris_store import Journal,Issue,Article,Author,Publication


def get_article_from_doi(doi_number):
    article=None
    doi_xml=get_doi_xml(doi_number)
    if doi_xml != None:
        article=parse_doi_xml(doi_xml)
    return article

CROSSREF_URL="http://www.crossref.org/guestquery/?queryType=doi&restype=unixref&doi=%s"
def get_doi_xml(doi_number):
    url=CROSSREF_URL % urllib.quote_plus(doi_number) 
    LOG.debug("Fetching CrossRef data from: %s",url)
    page=urllib2.urlopen( url )
    html=page.read()
    xml_start=html.find("<?xml")
    xml_end=html.find("</doi_records>",xml_start)+14
    xml=unicode(html[xml_start:xml_end],'utf-8')
    page_tree=BeautifulSoup(xml,"xml")
    error=page_tree.find('error')
    if error!=None:
        LOG.debug('Lookup for %s resulted in error: %s',doi_number,error.string)
        return None
    doi_xml=page_tree.find("doi_records")
    if doi_xml==None:
        LOG.debug("No doi records found in :\n%s"%html)
        LOG.debug("No doi records found in :\n%s"%xml)
    return doi_xml

def parse_doi_xml(doi_xml):
    # Process the Journal
    #   <journal_metadata language="en">
    #       <full_title>Brain Cell Biology</full_title>
    #       <abbrev_title>Brain Cell Bio</abbrev_title>
    #       <issn media_type="print">1559-7105</issn>
    #       <issn media_type="electronic">1559-7113</issn>
    #   </journal_metadata>
    journal_xml=doi_xml.doi_record.crossref.journal.journal_metadata
    journal_title=tostr(journal_xml.full_title)
    journal=Journal(journal_title,'')
    for issn in journal_xml.findAll('issn'):
        media_type=''
        if 'media_type' in issn.attrs:
            media_type=issn.attrs['media_type']
        journal.issn[media_type]=tostr(issn)

    # Get the journal issue
    #   <journal_issue>
    #       <publication_date media_type="print">
    #           <month>8</month>
    #           <year>2008</year>
    #       </publication_date>
    #       <journal_volume>
    #           <volume>36</volume>
    #       </journal_volume>
    #       <issue>1-4</issue>
    #   </journal_issue>
    issue_xml=doi_xml.doi_record.crossref.journal.journal_issue

    vol_xml=issue_xml.journal_volume.volume
    if vol_xml!=None:
        volume=tostr(issue_xml.journal_volume.volume)
    else:
        volume=''

    issue_number_xml=issue_xml.issue
    if issue_number_xml!=None:
        issue_number=tostr(issue_number_xml)
    else:
        issue_number=''

    issue=Issue(volume,issue_number)
    issue.journal=journal

    for pub_date in issue_xml.findAll('publication_date'):
        media_type=''
        if 'media_type' in pub_date.attrs:
            media_type=pub_date.attrs['media_type']
        pub=Publication(media_type,
                        tostr(pub_date.year),
                        tostr(pub_date.month),
                        tostr(pub_date.day))
        issue.add_publication(pub)

    # Get the journal article
    #   <journal_article publication_type="full_text">
    #     <titles>
    #       <title>Development of microscopic systems for high-speed dual-excitation ratiometric Ca2+ imaging</title>
    #     </titles>
    #     <contributors>
    #       <person_name contributor_role="author" sequence="first">
    #         <given_name>Takashi</given_name>
    #         <surname>Fukano</surname>
    #       </person_name>
    #       <person_name contributor_role="author" sequence="additional">
    #         <given_name>Satoshi</given_name>
    #         <surname>Shimozono</surname>
    #       </person_name>
    #       <person_name contributor_role="author" sequence="additional">
    #         <given_name>Atsushi</given_name>
    #         <surname>Miyawaki</surname>
    #       </person_name>
    #     </contributors>
    #     <publication_date media_type="online">
    #       <month>10</month>
    #       <day>22</day>
    #       <year>2008</year>
    #     </publication_date>
    #     <publication_date media_type="print">
    #       <month>8</month>
    #       <year>2008</year>
    #     </publication_date>
    #     <pages>
    #       <first_page>43</first_page>
    #       <last_page>52</last_page>
    #     </pages>
    #     <publisher_item>
    #       <item_number item_number_type="sequence-number">s11068-008-9033-8</item_number>
    #       <identifier id_type="pii">9033</identifier>
    #     </publisher_item>
    #     <doi_data>
    #       <doi>10.1007/s11068-008-9033-8</doi>
    #       <timestamp>20090130044855</timestamp>
    #       <resource>http://link.springer.com/10.1007/s11068-008-9033-8</resource>
    #       <collection property="crawler-based" setbyid="springer">
    #         <item crawler="iParadigms">
    #           <resource>http://www.springerlink.com/index/pdf/10.1007/s11068-008-9033-8</resource>
    #         </item>
    #       </collection>
    #     </doi_data>
    #   </journal_article>
    document_xml=get_document_xml(doi_xml)
    doi_number=tostr(document_xml.doi_data.doi,False)
    title=tostr(document_xml.titles.title)
    url=tostr(document_xml.doi_data.resource,False)
    first_page=None
    try:
        first_page=int(tostr(document_xml.pages.first_page))
    except:
        pass
    last_page=None
    try:
        last_page=int(tostr(document_xml.pages.last_page))
    except:
        pass
    article=Article(doi_number,title,url,u'',first_page,last_page)
    article.issue=issue
    for pub_date in document_xml.findAll('publication_date'):
        media_type='' 
        if pub_date.has_attr('media_type'):
            media_type=pub_date.attrs['media_type']
        pub=Publication(media_type,
                        tostr(pub_date.year),
                        tostr(pub_date.month),
                        tostr(pub_date.day))
        article.add_publication(pub)
    for author_xml in document_xml.contributors.findAll('person_name'):
        given_name=tostr(author_xml.given_name)
        surname=tostr(author_xml.surname)
        author=Author(given_name,surname)
        article.authors.append(author)
    return article

def get_document_xml(xml):
    # Look for a journal article
    doc=xml.find('journal_article')
    # Look for book chapter
    if doc==None:
        doc=xml.find('content_item')
        # Look for a proceedings article
        if doc==None:
            doc=xml.find('conference_paper')
    return doc

def tostr(node,html=True):
    str=''
    if node!=None:
        str=' '.join([s for s in node.stripped_strings]) 
        # if the string might have some HTML formatting then we want to remove it
        if html and len(str)>1: # Fixes some issue where BeautifulSoup eats a single character
            str=BeautifulSoup(str).string
    return str

