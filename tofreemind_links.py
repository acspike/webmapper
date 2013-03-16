#!/usr/bin/env python

#
# tofreemind_links.py
# Copyright (c) 2010-2013 Aaron C Spike
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 

import sqlite3
import xml.etree.ElementTree as etree

class TreeDict(dict):
    pass

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

reverse_enum = lambda x: reversed(list(enumerate(reversed(x))))
url_to_path = lambda x: x.replace('//','/').strip('/').split('/')[1:]
url_to_id = lambda x: 'ID_'+'_'.join(url_to_path(x))
link_count = 0
def dict2xml(elt, tree, links):
    global link_count
    for leaf in tree.keys():
        url = tree[leaf].row.get('url','')
        title = tree[leaf].row.get('title','')
        if title:
            #print repr(title)
            title = ' (%s)' % (title.strip().split('\n')[0],)
        else:
            title = ''
        parent_id = url_to_id(url)
        subelt = etree.SubElement(elt,'node',{'TEXT':'%s%s'%(leaf,title), 'ID':parent_id})
        for link in list(links.get(parent_id,[])):
            if link_count < 1000:
                etree.SubElement(subelt, 'arrowlink',{'COLOR':'#ffcccc','DESTINATION':link,'ENDARROW':'Default','STARTARROW':'None', 'ENDINCLINATION':'60;0;', 'STARTINCLINATION':'60;0;'})
                link_count += 1
        dict2xml(subelt,tree[leaf], links)

if __name__=='__main__':
    db = './www.db'
    conn = sqlite3.connect(db)
    conn.row_factory=dict_factory
    c = conn.cursor()
    
    
    c.execute('''
select parent, child 
from links 
where child in
(
    select child 
    from links 
    where child like '%www.mlc-wels.edu%' 
    group by child 
    having count(child) < 91 
    order by count(child) desc 
)
''')
    links = {}
    for row in c:
        parent_url = row['parent']
        child_url = row['child']
        
        child_path = url_to_path(child_url)
        parent_path = url_to_path(parent_url)
        parent_path.append(child_path[-1])
        
        if ''.join(child_path)==''.join(parent_path):
            continue
        
        parent_id = url_to_id(parent_url)
        child_id = url_to_id(child_url)
        links.setdefault(parent_id,set([])).add(child_id)    
    
    #c.execute('''select url from site where ctype like '%html%' and status = 200 ''')
    c.execute('''select * from site where status = 200 ''')
    
    tree = TreeDict()
    tree.row = {}
    
    for row in c:
        x = row['url']
        path = url_to_path(x)
        cursor = tree
        for idx, leaf in reverse_enum(path):
            node = TreeDict()
            setattr(node,'row',{})
            if idx == 0:
                setattr(node,'row',row)
            cursor = cursor.setdefault(leaf,node)

    doc = etree.Element('map',{'version':'0.9.0'})
    dict2xml(doc,tree,links)
    print etree.tostring(doc)
