#!/usr/bin/env python
import atexit
import sys
import os
import unittest
source= os.path.abspath("../src")
sys.path=[source]+sys.path

def remove_pyc():
	for d,child_dir,files in os.walk(source):
		for f in [f for f in files if f.endswith("pyc")]:
			os.unlink(os.path.join(d,f))

class XLibrisTests(unittest.TestCase):

		def test_lazymap(self):
			lm = LazyMap(lambda s: s.upper(),{'x':'a','y':'b','z':'c'})
			self.assertTrue(len(lm)==3)
			self.assertTrue(lm['x']=='A')
			self.assertTrue(lm['y']=='B')
			self.assertTrue(lm['z']=='C')
			lm['d']='D'
			self.assertTrue(len(lm)==4)
			self.assertTrue(lm['d']=='D')
			del lm['x']
			self.assertTrue(len(lm)==3)
			self.assertRaises(KeyError, lambda:lm['a'])

		def test_lazylist(self):
			ll = LazyList(lambda n:n+1,[4,5,6])
			self.assertTrue(len(ll)==3)
			self.assertTrue(ll[0]==5)
			self.assertTrue(ll[1]==6)
			self.assertTrue(ll[2]==7)
			self.assertRaises(IndexError, lambda:ll[3])
			ll.append('foo')
			self.assertTrue(len(ll)==4)
			self.assertTrue(ll[3]=='foo')
			del ll[0]
			self.assertTrue(len(ll)==3)
			self.assertTrue(ll[0]==6)


if __name__== '__main__':
	atexit.register(remove_pyc)
	remove_pyc()
	sys.path=[source]+sys.path
	import xlibris as xl
	import xlibris.xlibris_store as xls
	from xlibris.lazy_collections import LazyMap,LazyList
	xl.debug_on()
	unittest.main()


