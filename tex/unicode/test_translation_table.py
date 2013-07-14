# vim: set fileencoding=utf-8 :
import re
import cPickle

translation_table = {}

with open('../../src/xlibris/unicode_to_latex','r') as f:
    translation_table=cPickle.load(f)
print u"été à l'eau".translate(translation_table)
print u"Mühlhaus, H.-B.".translate(translation_table)
