import sqlite3
from . import LOG

class Database(object):
	def __init__(self,db,tables):
		self._db=db
		self._tables=tables
		self._create_tables()
	
	def _get_db(self):
		conn = sqlite3.connect(self._db)
		return conn

	def _get_columns(self,table):
		return [name for name,col_type in self._tables[table] if '(' not in col_type ]

	def _create_tables(self):
			conn=self._get_db()
			cur=conn.cursor()
			for name,cols in self._tables.iteritems():
				col_def=', '.join([ "%s %s"%col for col in cols ])
				create_sql="CREATE TABLE IF NOT EXISTS %s ( %s )"%(name,col_def)
				LOG.debug('create table : SQL=%s'%create_sql)
				cur.execute(create_sql)
			cur.close()
			conn.close()
	
	def _get_row(self,table,equal):
		rows=self._get_rows(table,{},equal)
		return None if len(rows)==0 else rows[0]


	def _get_rows(self,table,like,equal):
		LOG.debug("table=%s"%table)
		LOG.debug("like=%s"%like)
		LOG.debug("equal=%s"%equal)
		val_list=[]
		wheres=[]
		table_col=self._get_columns(table)
		LOG.debug("Columns for table '%s' : %s"%(table,table_col))
		for column in table_col:
			if column in like:
				val_list.append('%'+like[column]+'%')
				wheres.append('%s like ?'%column)
			if column in equal:
				val_list.append(equal[column])
				wheres.append('%s=?'%column)
		where='WHERE '+(' AND '.join(wheres)) if len(wheres)>0 else ''
		values=tuple(val_list)
		cols=','.join(table_col)
		sql='SELECT %s FROM %s %s'%(cols,table,where)
		return self._select(sql,table_col,values)

	def _one_from_many(self,t1,t2,id,t2id='id'):
		rows=self._simple_join(t1,t2,id,t2id)
		return None if len(rows)==0 else rows[0]

	def _simple_join(self,t1,t2,id,t2id='id'):
		"""
|----|      |-------| 
| t1 |      |   t2  | 
|----|      |-------| 
| id |--|   | id    | 
|    |  |--<| t1_id | 
|----|      |-------| 

also for selecting one side of a many to many if t2id is specified

|----|      |-------|   |----|
| t1 |      |   t2  |   | t3 |
|----|      |-------|   |----|
| id |--|   | t2_id |>--| id |
|    |  |--<| t1_id |   |    |
|----|      |-------|   |----|

Selects one row from t1 based on the t2.id where t1 is 1 to many of t2.
Results in:
SELECT t1.*
FROM t1
JOIN t2 ON t1.id=t2.t1_id
WHERE t2.id=id
		"""
		return self._join_rows([t1],[t2],[('%s.id'%t1,'%s.%s_id'%(t2,t1))],equal={"%s.%s"%(t2,t2id):id})

	def _join_rows(self,select_tables,join_tables,joins,like={},equal={},orderby=[],asc=True):
		"""
Performs a join on [tables] with [joins] where [like]
and [equal]

SELECT TableA.*
FROM TableA
	JOIN TableB
		ON TableB.aID = TableA.aID
	JOIN TableC
		ON Tableb.cID = TableB.cID
	JOIN TableD
	ON TableD.dID = TableA.dID
WHERE DATE(TableC.date)=date(now()) 
ORDER BY TableC.date ASC
"""
		LOG.debug("select tables=%s"%select_tables)
		LOG.debug("join tables=%s"%join_tables)
		LOG.debug("like=%s"%like)
		LOG.debug("equal=%s"%equal)
		val_list=[]
		join_list=[]
		wheres=[]
		select_col=[]
		# Build the select columns
		for table in select_tables:
			select_col.extend([table+'.'+col for col in self._get_columns(table)])
		# The list of all columne
		table_col=select_col[:]
		for table in join_tables:
			table_col.extend([table+'.'+col for col in self._get_columns(table)])
		LOG.debug("select columns : %s"%select_col)
		LOG.debug("tables columns : %s"%table_col)
		for column in table_col:
			if column in like:
				val_list.append('%'+like[column]+'%')
				wheres.append('%s like ?'%column)
			if column in equal:
				val_list.append(equal[column])
				wheres.append('%s=?'%column)
		# The where clause
		where='WHERE '+(' AND '.join(wheres)) if len(wheres)>0 else ''
		# Build the join
		tables=select_tables+join_tables
		for n,join in enumerate(joins):
			join_list.append("JOIN %s ON %s = %s"%( (tables[n+1],)+join ))
		join_clause=' '.join(join_list)

		table=tables[0]
		col_names=self._get_columns(table)
		LOG.debug("column names : %s"%col_names)

		# The order by clause
		order_clause="ORDER BY %s %s"%(",".join(orderby),"ASC" if asc else "DESC") if len(orderby)>0 else ''
		values=tuple(val_list)
		cols=','.join(select_col)
		sql='SELECT %s FROM %s %s %s %s'%(cols,table,join_clause,where,order_clause)
		return self._select(sql,col_names,values)

	def _select(self,sql,cols,values):
		result=[]
		conn=self._get_db()
		cur=conn.cursor()
		LOG.debug('get : SQL=%s'%sql)
		LOG.debug('get : cols=%s'%str(cols))
		LOG.debug('get : values=%s'%str(values))
		cur.execute(sql,values)
		for row in cur:
			r={}
			for n,column in enumerate(cols):
				r[column]=row[n]
			LOG.debug('row: %s'%r)
			result.append(r)
		cur.close()
		conn.close()
		return result

	def _add(self,table,values):
		conn=self._get_db()
		cur=conn.cursor()
		columns=self._get_columns(table)
		if columns[0]=='id':
			sql= 'INSERT INTO %s ( %s ) VALUES ( NULL%s)'%( table , ','.join(columns), ',?'*len(values) )
		else:
			sql= 'INSERT INTO %s ( %s ) VALUES ( %s)'%( table , ','.join(columns), ','.join(['?']*len(values)) )
		LOG.debug('add : SQL=%s'%sql)
		LOG.debug('add : values=%s'%str(values))
		cur.execute(sql,values)
		id=cur.execute('SELECT last_insert_rowid()').next()[0]
		conn.commit()
		conn.close()
		return id

	def _delete_row(self,table,id):
		conn=self._get_db()
		cur=conn.cursor()
		sql= 'DELETE FROM %s WHERE id=?'%table
		LOG.debug('delete : SQL=%s'%sql)
		LOG.debug('delete : id=%s'%id)
		cur.execute(sql,(id))
		conn.commit()
		cur.close()
		conn.close()

	def _delete_all_rows(self,table):
		conn=self._get_db()
		cur=conn.cursor()
		sql= 'DELETE FROM %s'%table
		LOG.debug('delete : SQL=%s'%sql)
		try:
		        cur.execute(sql)
		        conn.commit()
		        LOG.debug('delete : rows deleted')
		except:
			LOG.error('Error processing delete command "%s"'%sql,exc_info=True)
		cur.close()
		conn.close()

