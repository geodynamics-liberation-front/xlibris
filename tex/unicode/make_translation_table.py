# vim: set fileencoding=utf-8 :
import re
import cPickle as pickle

translation_table = {}

# Get translations for LaTeX base packag
with open('utf8ienc.dtx') as f:
    for line in f:
        m = re.match(r'%.*\DeclareUnicodeCharacter\{(\w+)\}\{(.*)\}', line)
        if m:
            codepoint, latex = m.groups()
            latex = latex.replace('@tabacckludge', '') # remove useless (??) '@tabacckludge'
            if latex[-1]!=u'}':
                latex=latex+u'{}'
            translation_table[int(codepoint, 16)] = unicode(latex)

# Additional translations from on the internet
with open('unicode_latex.txt') as f:
    for line in f:
        line=line.strip()
        if not line.startswith("#") and len(line)>0:
            m = re.match(r'(\S+).*?"(.*)"', line)
            if m != None:
                unichar, latex = m.groups()
                try:
                    codepoint = ord(eval(unichar))
                except TypeError:
                    print("Unable to process unicode character %s" % unichar )

                if codepoint not in translation_table:
                    try:
                        translation_table[codepoint] = unicode(latex)
                    except UnicodeDecodeError:
                        print("Unable to process LaTeX character %s" % latex )
            else:
                print("Line did not match regular expression : %s" % line)

with open('../../src/xlibris/utl.p','w') as f:
    pickle.dump(translation_table, f)
print u"été à l'eau".translate(translation_table)
print u"Mühlhaus, H.-B.".translate(translation_table)
