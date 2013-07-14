import cookielib
import doi
import urllib2
import urlparse
import zlib
import settings as xlsettings
import tempfile
from bs4 import BeautifulSoup
from . import LOG
from collections import OrderedDict

DX_URL="http://dx.doi.org/%s"
#def download_paper(article):
#    try:
#        url=DX_URL % urllib.quote_plus(article.doi) 
#        page=urllib2.urlopen(url)
#    except urllib2.HTTPError as e:
#        LOG.debug('Unable to get page %s : %s',url,e)
#        try:
#            url=article.url
#            page=urllib2.urlopen(url)
#        except urllib2.HTTPError as e:
#            LOG.debug('Unable to get page %s : %s',url,e)
#            return None

# http://rspa.royalsocietypublishing.org/content/459/2039/2663 -> same as below
# http://gji.oxfordjournals.org/content/31/4/447 -> same as below
# http://lithosphere.gsapubs.org/content/5/2/163.abstract -> <a href="/content/5/2/163.full.pdf+html" rel="view-full-text.pdf">Full Text (PDF)</a> : rel
# http://www.nature.com/nature/journal/v441/n7096/abs/nature04797.html -> <a href="/nature/journal/v441/n7096/pdf/nature04797.pdf" class="download-pdf">Download PDF</a> : a + class
# http://www.sciencemag.org/content/296/5567/485 -> <meta content="http://www.sciencemag.org/content/296/5567/485.full.pdf" name="citation_pdf_url" />
# http://www.sciencedirect.com/science/article/pii/S0040195109005678 -> <a id="pdfLink" href="http://www.sciencedirect.com/science?_ob=MiamiImageURL&amp;_cid=271882&amp;_user=4429&amp;_pii=S0040195109005678&amp;_check=y&amp;_origin=article&amp;_zone=toolbar&amp;_coverDate=01-Mar-2010&amp;view=c&amp;originContentFamily=serial&amp;wchp=dGLzVBA-zSkWz&amp;md5=e1daab8e3c5f9c5f0307f5395c2e7bb4&amp;pid=1-s2.0-S0040195109005678-main.pdf" target="newPdfWin" pdfurl="http://www.sciencedirect.com/science?_ob=MiamiImageURL&amp;_cid=271882&amp;_user=4429&amp;_pii=S0040195109005678&amp;_check=y&amp;_origin=article&amp;_zone=toolbar&amp;_coverDate=01-Mar-2010&amp;view=c&amp;originContentFamily=serial&amp;wchp=dGLzVBA-zSkWz&amp;md5=e1daab8e3c5f9c5f0307f5395c2e7bb4&amp;pid=1-s2.0-S0040195109005678-main.pdf" suggestedarturl="http://www.sciencedirect.com/science/suggestedArt/citeList/pii/S0040195109005678/eid/1-s2.0-S0040195109005678/serial" class="big pdf ext_sdlink" style="cursor:pointer" title="Download PDF">PDF  (1726 K)</a> : id

# http://onlinelibrary.wiley.com/doi/10.1029/2007JB005270/abstract -> <a href="/doi/10.1029/2007JB005270/pdf" title="Article in pdf format" id="journalToolsPdfLink" class="readcubePdfLink" shape="rect">Get PDF (3544K)</a> : id
# <iframe id="pdfDocument" src="http://onlinelibrary.wiley.com/store/10.1029/2001GC000171/asset/ggge133.pdf?v=1&amp;t=hj20yc39&amp;s=29dd91f038ffa3a1cf23db87cba086e8b24ac4a3" width="100%" height="675px">

# http://ieeexplore.ieee.org/xpl/articleDetails.jsp?arnumber=4380548 -> <a href='/stamp/stamp.jsp?tp=&arnumber=4380548' class="pdf"> Full Text as PDF</a> : class="pdf"
# http://link.springer.com/article/10.1007%2FBF00876946 -> <a id="action-bar-download-pdf-link" class="webtrekk-track pdf-link" doi="10.1007/BF00876946" pageType="rd_springer_com.journal.article_full_text" parentContentType="Journal" contentType="Article" viewType="Full text download" publication="24 | pure and applied geophysics" href="/content/pdf/10.1007%2FBF00876946.pdf"> Download PDF <span id="action-bar-download-pdf-size"> (617 KB) </span> </a> : id


# http://www.opticsinfobase.org/josaa/viewmedia.cfm?uri=josaa-15-3-586&seq=0
# http://www.opticsinfobase.org/josaa/abstract.cfm?uri=JOSAA-15-3-586 -> <meta name="citation_pdf_url" content="http://www.opticsinfobase.org/viewmedia.cfm?uri=josaa-15-3-586&seq=0">
# http://www.opticsinfobase.org/view_article.cfm?gotourl=http%3A%2F%2Fwww.opticsinfobase.org%2FDirectPDFAccess%2F3FFE4BEB-02AE-FA37-1E34D0F7DF413F45_1421%2Fjosaa-15-3-586.pdf%3Fda%3D1%26id%3D1421%26seq%3D0%26mobile%3Dno&org=University%20of%20California%20San%20Diego%20%28CDL%29 : extract link from URL
# http://www.opticsinfobase.org/DirectPDFAccess/3FFE4BEB-02AE-FA37-1E34D0F7DF413F45_1421/josaa-15-3-586.pdf%3Fda%3D1%26id%3D1421%26seq%3D0%26mobile%3Dno&org=University%20of%20California%20San%20Diego%20%28CDL%29 : 
# http://www.opticsinfobase.org/DirectPDFAccess%2F3FC0059C-F2B5-2278-08816748FB4FDB24_1421%2Fjosaa-15-3-586.pdf%3Fda%3D1%26id%3D1421%26seq%3D0%26mobile%3Dno&org=University%20of%20Cali0fornia%20San%20Diego%20%28CDL%29 : extract url to get -> 

# Generic look for PDF, "Full Text", "Download PDF"
# <meta name="citation_pdf_url" content="http://www.opticsinfobase.org/viewmedia.cfm?uri=josaa-15-3-586&seq=0">



class WebPage(object):
    def __init__(self,url):
        self.response=get_response(url)
        self.source=self.response.read()
        self.soup=BeautifulSoup(self.source)
        self.original_url=url
        self.url=self.response.url

def same(s):
        return s

class TagExtractor(object):
    def __init__(self,tag,attr,value,url_attr,filter=same):
        self._t=tag
        self._a=attr
        self._v=value
        self._ua=url_attr
        self._f=filter

    def __call__(self,page):
        url=[]
        t=page.soup.find(self._t,attrs={self._a:self._v})
        if t != None:
            url.append(self._f(t[self._ua]))
        return url

class AnchorExtractor(TagExtractor):
    def __init__(self,attr,value,filter=same):
        TagExtractor.__init__(self,'a',attr,value,'href',filter)

class IFrameExtractor(TagExtractor):
    def __init__(self,attr,value,filter=same):
        TagExtractor.__init__(self,'iframe',attr,value,'src',filter)

class MetaExtractor(TagExtractor):
    def __init__(self,value,filter=same):
        TagExtractor.__init__(self,'iframe','name',value,'content',filter)

class FrameExtractor(object):
    def __init__(self,frame_number,filter=same):
        self._fn=frame_number
        self._f=filter

    def __call__(self,page):
        url=[]
        f=page.soup.findAll('frame')
        if len(f)>self._fn:
            url.append(self._f(f[self._fn]['src']))
        return url

class QueryStringExtractor(object):
    def __init__(self,value,filter=same):
        self._v=value
        self._f=filter

    def __call__(self,page):
        qs=urlparse.parse_qs(urlparse.urlparse(page.url).query)
        url=[qs[self._f(self._v)]]
        return url

class TextSearchExtractor(object):
    def __init__(self,values,filter=same):
        self._v=values
        self._f=filter

    def __call__(self,page):
        url=[]
        for anchor in page.soup.findAll('a'):
            if anchor.string != None and any([v.lower() in anchor.string.lower() for v in self._v]):
                url.append(self._f(anchor['href']))
        return url

class ChainedPDFExtractor(object):
    def __init__(self,extractors):
        self._e=extractors

    def __call__(self,page):
        pages=[page]
        for e in self._e:
            url=[]
            for p in pages:
                url.extend([urlparse.urljoin(p.url,u) for u in e(p)])
            LOG.debug("Intermediate url : %s",url)
            pages=[WebPage(u) for u in url]
        return url

class TryExtractor(object):
    def __init__(self,extractors):
        self._e=extractors

    def __call__(self,page):
        url=[]
        for e in self._e:
            LOG.debug('Trying %s',e)
            url.extend(e(page))
            if len(url)>0:
                break
        return url

_extractors={}
_extractors['royalsocietypublishing.org']=AnchorExtractor('rel','view-full-text.pdf',lambda s: s[:-5] if s[-5:]=='+html' else s)
_extractors['oxfordjournals.org']=AnchorExtractor('rel','view-full-text.pdf',lambda s: s[:-5] if s[-5:]=='+html' else s)
_extractors['gsapubs.org']=AnchorExtractor('rel','view-full-text.pdf',lambda s: s[:-5] if s[-5:]=='+html' else s)
_extractors['nature.com']=AnchorExtractor('class','download-pdf')
_extractors['sciencemag.org']=MetaExtractor('citation_pdf_url')
_extractors['sciencedirect.com']=AnchorExtractor('id','pdfLink')
_extractors['onlinelibrary.wiley.com']=ChainedPDFExtractor([AnchorExtractor('id','journalToolsPdfLink'),IFrameExtractor('id','pdfDocument')])
_extractors['ieeexplore.ieee.org']=ChainedPDFExtractor([AnchorExtractor('class','pdf'),FrameExtractor(1)])
_extractors['springer.com']=AnchorExtractor('id','action-bar-download-pdf-link')
_extractors['springer.com']=AnchorExtractor('id','action-bar-download-pdf-link')
_extractors['opticsinfobase.org']=ChainedPDFExtractor([MetaExtractor('citation_pdf_url'),QueryStringExtractor('gotourl')])
_default_extractor=TryExtractor([MetaExtractor('citation_pdf_url'),TextSearchExtractor(['full text','pdf'])])

def extract_pdf_url(url):
    LOG.debug("Extracting PDF url for %s",url)
    page=WebPage(url)
    LOG.debug("%s resolved to %s",page.original_url,page.url)
    host_parts=urlparse.urlparse(page.url).netloc.split('.')
    extractor = None
    while len(host_parts)>0 and extractor == None:
        try:
            key = '.'.join(host_parts)
            extractor=_extractors[key]
            LOG.debug('Using the %s extractor',key)
        except KeyError:
            host_parts = host_parts[1:]
    if extractor == None:
        LOG.debug('Using the default extractor')
        extractor = _default_extractor

    pdf_url=extractor(page)
    urls=[urlparse.urljoin(page.url,url) for url in pdf_url]
    # Make the list unique
    urls=list(OrderedDict.fromkeys(urls))
    return urls

def download_pdf(url):
    pdf = None
    try:
        page=get_response(url)
        content_type=page.info().getheader('content-type').split(';')[0]
        if content_type == 'application/pdf':
            f=tempfile.NamedTemporaryFile(suffix='.pdf',dir=xlsettings.settings.download_dir,delete=False)
            while True:
                buffer = page.read(8192)
                if not buffer:
                    break
                f.write(buffer)
            f.close()
            pdf=f.name
        else:
            LOG.error('%s returned a resource of type %s, was expecting application/pdf, skipping',url,content_type)
    except urllib2.HTTPError:
        LOG.exception('Problem downloading %s',url)
    return pdf

def get_pdf(url):
    pdfs=[]
    pdf_url=extract_pdf_url(url)
    for u in pdf_url:
        pdf=download_pdf(u)
        if pdf != None:
            pdfs.append(pdf)
    return pdfs

def get_doi(url):
    #TODO: extract the doi from the URL if it is present
    doi_numbers=[]
    html_src = None
    try:
        page=get_response(url)
        html_src=page.read()
    except urllib2.HTTPError as e:
        # Some journals (hmm, Nature, hmm) return a 401 if the article needs to be purchased 
        # but still provides the metadata necessary to extract the DOI
        if e.code==401:
            # Check if it is gzipped
            if e.info().getheader('Content-Encoding')=='gzip':
                html_src=zlib.decompress(e.read(),16+zlib.MAX_WBITS)
            else:
                html_src=e.read()
        else:
            LOG.debug('Unable to get page %s : %s',url,e)
    # First look for a meta tag
    # works for: Nature, Science, Wiley, Springer, Oxford Journals, GSA Pubs,
    #            Royal Society Publishing
    if html_src != None:
        html=BeautifulSoup(html_src)
        meta=html.find('meta',attrs={'name':'citation_doi'})
        if meta == None:
            meta=html.find('meta',attrs={'name':'dc.Identifier','scheme':'doi'})
        if meta != None:
            doi_number=meta['content']
            # remove the occasional doi: prefix
            doi_numbers.extend(doi.doi_from_text(doi_number))
        else:
            # ScienceDirect (Elsevier) and other journals that can't be bothered to 
            # include meta-data in their HTML : scan line by line
            doi_numbers.extend(doi.doi_from_text(html_src))
    return doi_numbers

proxy_user = None
proxy_password = None
proxy_address = None
proxy_port = None
def get_response(url):
    handlers=[]
    # proxy
    if proxy_address != None:
        if proxy_user != None:
            proxy_auth="%s:%s@"%(proxy_user,proxy_password)
        else:
            proxy_auth=''
        handlers.append(urllib2.ProxyHandler(
            {'http': 'http://%s%s:%d' % (proxy_auth,proxy_address,proxy_port) }))
    # Authorization Handler
    handlers.append(urllib2.HTTPBasicAuthHandler())
    # Some sites like cookies
    handlers.append(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
    # Build the opener
    opener = urllib2.build_opener(*handlers)
    # F Elsivier for making me put in a fake agent-header
    req=urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0')
    return opener.open(req)
