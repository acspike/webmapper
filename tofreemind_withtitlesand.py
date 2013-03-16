#!/usr/bin/env python

#
# tofreemind_withtitlesand.py
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

def dict2xml(elt, tree):
    for leaf in tree.keys():
        title = tree[leaf].row.get('title','')
        if title:
            #print repr(title)
            title = ' (%s)' % (title.strip().split('\n')[0],)
        else:
            title = ''
        
        subelt = etree.SubElement(elt,'node',{'TEXT':'%s%s'%(leaf,title)})
        dict2xml(subelt,tree[leaf])

if __name__=='__main__':
    db = './www.db'
    conn = sqlite3.connect(db)
    conn.row_factory=dict_factory
    c = conn.cursor()
    #c.execute('''select url from site where ctype like '%html%' and status = 200 ''')
    c.execute('''select * from site where status = 200 ''')
    
    tree = TreeDict()
    tree.row = {}
    
    for row in c:
        x = row['url']
        path = x.replace('//','/').strip('/').split('/')[1:]
        cursor = tree
        for idx, leaf in reverse_enum(path):
            node = TreeDict()
            setattr(node,'row',{})
            if idx == 0:
                setattr(node,'row',row)
            cursor = cursor.setdefault(leaf,node)

    doc = etree.Element('map',{'version':'0.9.0'})
    dict2xml(doc,tree)
    print etree.tostring(doc)
