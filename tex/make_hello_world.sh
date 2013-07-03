#!/bin/sh

mkdir -p ../test/pdf

t=hello_world
echo $t
pdflatex $t.tex
cp $t.pdf ../src/xlibris/pdf

# cleanup
rm -f *.aux *.log *.pdf


