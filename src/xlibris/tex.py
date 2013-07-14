import pkg_resources
import cPickle as pickle
from unidecode import unidecode
from . import LOG

U_T_L=pickle.load(pkg_resources.resource_stream(__name__,"utl.p"))
MONTHS=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

BIBTEX_KEY=u'{article.authors[0].surname}{article.earliest_publication.year:04d}{iter}'
def bibkey(article,iter=''):
    return unidecode(BIBTEX_KEY.format(article=article,iter=iter)).lower().replace(' ','')

"""
@article{ribe1995,
  title={The dynamics of plume-ridge interaction, 1: Ridge-centered plumes},
  author={Ribe, NM and Christensen, UR and Theissing, J},
  journal={Earth and Planetary Science Letters},
  volume={134},
  number={1},
  pages={155--168},
  year={1995},
  publisher={Elsevier},
  doi={10.1016/0012-821X(95)00116-T}
}
"""
def article_to_bibtex(articles):
    try:
        iterator = iter(articles)
    except TypeError:
        iterator = iter([articles])
    references={}
    for article in iterator:
        pub=article.get_earliest_publication()
        bibtexKey=bibkey(article)
        i=ord('a')-1    
        while bibtexKey in references:
            i+=1
            bibtexKey=bibkey(article,chr(i))
        ref_items=[]
        ref_items.append(u"  title={{%s}}" % article.title)

        authors=" and ".join(
            [u"{author.surname}, {author.given_name}".format(author=a) 
             for a in article.authors] )
        ref_items.append(u"  author={%s}" % authors)
        ref_items.append(u"  journal={%s}" % article.issue.journal.title)

        volume = article.issue.volume
        if volume != None and volume != '':
            ref_items.append(u"  volume={%s}" % volume)

        number = article.issue.issue
        if number != None and number != '':
            ref_items.append(u"  number={%s}" % number)

        first_page=article.first_page
        last_page=article.last_page
        if first_page != None and first_page != '':
            if last_page != None and last_page !='':
                ref_items.append(u"  pages={%s--%s}" % (first_page,last_page))
            else:
                ref_items.append(u"  pages={%s}" % first_page)

        if pub.month != None and pub.month != '':
            month=pub.month
            try:
               month=MONTHS[int(month)-1]
            except:
               LOG.warning("Couldn't turn month '%s' into an int",pub.month)
            ref_items.append(u"  month={%s}" % month)
        if pub.year != None and pub.year != '':
            ref_items.append(u"  year={%s}" % pub.year)

        if article.url != None and article.url != '':
            ref_items.append(u"  url={%s}" % article.url)

        ref_items.append(u"  doi={%s}" % article.doi)

        reference="@article{%s,\n%s\n}"%(bibtexKey,",\n".join(ref_items))

        references[bibtexKey] = reference.translate(U_T_L)
    return references                   
