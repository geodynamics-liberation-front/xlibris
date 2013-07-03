#from . import LOG
# vim: set fileencoding=utf-8 :
import os

class Abbreviations(object):
	def __init__(self,afile):
		if not os.path.exists(afile):
			open(afile,"w").close()
		self.afile=afile
		self.abrs={}
		self.titles={}
		self.changed=False
		self.read()

	def abbreviate(self,title):
		return self.abrs[title]

	def title(self,abr):
		return self.titles[abr]

	def read(self,f=None):
		if f==None:
			f=open(self.afile)
		for line in f:
			line=line.strip()
			if len(line)>0 and line[0]!='#':
				title=line[:line.rfind(":")]
				abr=line[line.rfind(":")+1:]
				self.abrs[title]=abr
				self.titles[abr]=title

	def write(self,f=None):
		if f==None:
			f=open(self.afile,"w")
		for title in sorted(self.abrs.keys()):
			f.write("%s:%s\n"%(title,self.abrs[title]))
		f.close()

	def add(self,title,abr):
		self.changed=True
		self.abrs[title]=abr
		self.titles[abr]=title


ABBREV="""
Nature:Nat
Science:Sci
Nature Geoscience:NatGeo
Tectonophysics:TecP
Geochemistry, Geophusics, Geosystems:G3
Geophysical Research Letters:GRL
Journam of Advances in Modeling Earth Systems:JAMES
Journal of Geophysical Research:JRG
Water Resources Research:WRR
Earth Interactions:EI
Earth's Future:EF
Physics of the Earth and Planetary Interiors:PEPI
"""

def create(filename):
	pass


		
