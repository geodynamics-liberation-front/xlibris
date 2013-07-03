# vim: set fileencoding=utf-8 :
import imp
import os
import unittest
import xlibris.settings as xlsettings
import xlibris.xlibris_db as xldb
import xlibris.xlibris_store as xlstore
import sqlite3
from . import settings


pdfs=['article_10.prefix.pdf',
      'article_doi_prefix.pdf',
      'article_dx.doi.org_prefix.pdf',
      'book.pdf',
      'duplicate_author.pdf',
      'duplicate_issue.pdf',
      'duplicate_journal.pdf']

AUTHORS=[ (u'Allen', u'Craig D.'),
    (u'Anderson', u'R. Scott'),
    (u'Atudorei', u'Viorel'),
    (u'Bercovici', u'D.'),
    (u'Bercovici', u'David'),
    (u'Berke', u'Melissa A.'),
    (u'Brown', u'Erik T.'),
    (u'Bürgmann', u'Roland'),
    (u'Cisneros-Dozal', u'Luz M.'),
    (u'Donohoo-Hurley', u'Linda'),
    (u'Dresen', u'Georg'),
    (u'Fawcett', u'Peter J.'),
    (u'Fessenden', u'Julianna'),
    (u'Fukano', u'Takashi'),
    (u'Geissman', u'John W.'),
    (u'Glatzmaier', u'G. A.'),
    (u'Goff', u'Fraser'),
    (u'Heikoop', u'Jeffrey M.'),
    (u'Higashijima', u'Shin-ichi'),
    (u'Huang', u'Yongsong'),
    (u'Iimura', u'Tadahiro'),
    (u'Jellinek', u'A. Mark'),
    (u'Kitaguchi', u'Tetsuya'),
    (u'Miyawaki', u'Atsushi'),
    (u'Schouten', u'Stefan'),
    (u'Schubert', u'G.'),
    (u'Shimozono', u'Satoshi'),
    (u'Sinninghe Damsté', u'Jaap S.'),
    (u'Smith', u'Susan J.'),
    (u'Toney', u'Jaime'),
    (u'Werne', u'Josef P.'),
    (u'WoldeGabriel', u'Giday')]
class Tests(unittest.TestCase):

        def test_import_file(self):
            script=imp.load_source('script',os.path.join(settings.source,'scripts/xlibris'))
            script.settings=settings
            xlsettings.create_dirs(settings)

            settings.db=xldb.XLibrisDB(settings.db_file)
            settings.store=xlstore.XLibrisStore(settings.db)

            for pdf in pdfs:
                script.import_file(os.path.join('pdf',pdf),settings)
            # Check the Authors table
            conn=sqlite3.connect(settings.db_file)
            cur=conn.cursor()
            for surname, given_name in AUTHORS:
                cur.execute("SELECT COUNT(*) FROM author WHERE surname=? AND given_name=?", (surname,given_name) )
                count=cur.fetchone()[0]
                self.assertEqual(count,1,"Expected 1 author for %s, %s found %d" % (surname,given_name,count))


def get_suite():
    return unittest.TestLoader().loadTestsFromTestCase(Tests)
