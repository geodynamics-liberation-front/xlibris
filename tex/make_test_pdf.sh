#!/bin/sh

mkdir -p ../test/pdf

for t in  \
	article_10.prefix  \
	article_doi_prefix  \
	article_dx.doi.org_prefix  \
	duplicate_author  \
	duplicate_issue  \
	duplicate_journal  \
	book ; do
		echo $t
		pdflatex $t.tex
		cp $t.pdf ../test/pdf
done

# cleanup
rm -f *.aux *.log *.pdf


