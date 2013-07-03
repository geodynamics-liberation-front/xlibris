#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
import os
import re
import subprocess
import urllib
import urllib2
from bs4 import BeautifulSoup
from xlibris_store import Journal,Issue,Article,Author,Publication

ORDINAL=['first','second','third','forth','fifth','sixth','seventh','eighth','ninth','tenth']

doiurl_re=re.compile("doi:\s?([a-z0-9\-._;()/]+)")   # Matches doi:(10. ... )
dx_re=re.compile("dx.doi.org/(10[a-z0-9\-._;()/]+)") # Matches dx.doi.org/(10. ...)
doi_re=re.compile("(?:\s|^)(10.[0-9.]+/[a-z0-9\-._;()/]+)") # Mathces (10. ... )

def get_doi_from_pdf(pdf):
    doi=[]
    for line in subprocess.check_output(["pdftotext",pdf,'-'],stderr=open(os.devnull)).splitlines():
        line=line.lower()
        if 'doi' in line:
            for d in doiurl_re.findall(line):
                if d[-1]=='.': d=d[:-1]
                doi.append(d)
            for d in dx_re.findall(line):
                if d[-1]=='.': d=d[:-1]
                doi.append(d)
        elif "10." in line:
            for d in doi_re.findall(line):
                if d[-1]=='.': d=d[:-1]
                doi.append(d)
    return doi

cross_ref_url="http://www.crossref.org/guestquery/?queryType=doi&restype=unixref&doi=%s"
def get_doi_xml(doi):
    page=urllib2.urlopen( cross_ref_url%urllib.quote_plus(doi) )
    page_tree=BeautifulSoup(page.read())
    return page_tree.find("doi_records")

def tostr(node):
    return node.string.strip() if node!=None else None

def parse_doi_xml(doi):
    # Process the Journal
    #   <journal_metadata language="en">
    #       <full_title>Brain Cell Biology</full_title>
    #       <abbrev_title>Brain Cell Bio</abbrev_title>
    #       <issn media_type="print">1559-7105</issn>
    #       <issn media_type="electronic">1559-7113</issn>
    #   </journal_metadata>
    journal_xml=doi.doi_record.crossref.journal.journal_metadata
    journal_title=journal_xml.full_title.string.strip()
    journal=Journal(journal_title,'')
    for issn in journal_xml.findAll('issn'):
        media_type=''
        if 'media_type' in issn.attrs:
            media_type=issn.attrs['media_type']
        journal.issn[media_type]=issn.string.strip()

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
    issue_xml=doi.doi_record.crossref.journal.journal_issue

    vol_xml=issue_xml.journal_volume.volume
    if vol_xml!=None:
        volume=issue_xml.journal_volume.volume.string.strip()
    else:
        volume=''

    issue_number_xml=issue_xml.issue
    if issue_number_xml!=None:
        issue_number=issue_number_xml.string.strip()
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
    article_xml=doi.doi_record.crossref.journal.journal_article
    doi=article_xml.doi_data.doi.string.strip()
    title=article_xml.titles.title.string.strip()
    url=article_xml.doi_data.resource.string.strip()
    article=Article(doi,title,url,'')
    article.issue=issue
    for pub_date in article_xml.findAll('publication_date'):
        pub=Publication(pub_date.attrs['media_type'],
                        tostr(pub_date.year),
                        tostr(pub_date.month),
                        tostr(pub_date.day))
        article.add_publication(pub)
    for author_xml in article_xml.contributors.findAll('person_name'):
        given_name=author_xml.given_name.string.strip()
        surname=author_xml.surname.string.strip()
        author=Author(given_name,surname)
        article.authors.append(author)
    return article
