import collections

class LazyMap(collections.MutableMapping):
	def __init__(self,get,keys={}):
		self._keys=keys
		self._map={}
		self._map.update([ (k,None) for k in keys.keys()])
		self._get=get

	def __getitem__(self,key):
		v=self._map[key]
		if v==None:
			v=self._get(self._keys[key])
			self._map[key]=v
		return v

	def __setitem__(self,key,value):
		self._map[key]=value

	def __delitem__(self,key):
		del self._map[key]
		del self._keys[key]

	def __iter__(self):
		return self._map.__iter__()

	def __len__(self):
		return self._map.__len__()

class LazyList(collections.MutableSequence):
	def __init__(self,get,keys=[]):
		self._keys=keys
		self._sequence=[None]*len(keys)
		self._get=get

	def insert(self,ndx,obj):
		self._sequence.insert(ndx,obj)
		self._keys.insert(ndx,None)

	def __len__(self):
		return self._sequence.__len__()

	def __getitem__(self,ndx):
		v=self._sequence[ndx]
		if v==None:
			v=self._get(self._keys[ndx])
			self._sequence[ndx]=v
		return v

	def __setitem__(self,ndx,value):
		self._sequence[ndx]=value

	def __delitem__(self,ndx):
		del self._sequence[ndx]
		del self._keys[ndx]

