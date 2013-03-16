#!/usr/bin/env python

#
# webmapper.py
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

import traceback
import sqlite3
import httplib
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup



def check_headers(url):
    if isinstance(url, basestring):
        parsedUrl = urlparse.urlsplit(url)
    else:
        parsedUrl = url
    request_path = parsedUrl.path
    if not parsedUrl.path:
        request_path = '/'
    if parsedUrl.query:
        request_path += '?'+parsedUrl.query
    
    conn = httplib.HTTPConnection(parsedUrl.netloc)
    conn.request("HEAD",request_path)
    res = conn.getresponse()

    headers = {'content-type':'','content-length':'','location':''}
    for k,v in res.getheaders():
        if headers.has_key(k.lower()):
            headers[k.lower()] = v

    return (urlparse.urlunsplit(parsedUrl), parsedUrl, res.status, res.reason, headers['content-type'], 
        headers['content-length'], headers['location'])

def get_title_and_links(url):
    if isinstance(url, basestring):
        parsedUrl = urlparse.urlsplit(url)
    else:
        parsedUrl = url
    url = urlparse.urlunsplit(parsedUrl)

    try:
        openurl = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
        #print repr(e), dir(e)
        raise
    except:
        #print url
        raise
    urlContent = openurl.read()
    urlUrl = openurl.geturl()
    urlInfo = openurl.info()

    soup = BeautifulSoup(''.join(urlContent))
    try:
        title = soup.html.head.title.string
    except AttributeError:
        title = ''
    try:
        base = soup.html.head.base['href']
    except:
        base = urlUrl
    
    links = set([])
    linkTags = soup.findAll('a')
    for lt in linkTags:
        try:
            link = lt['href']
        except:
            continue
        parsedLink = urlparse.urlsplit(link)
        if not parsedLink.scheme:
            link = urlparse.urljoin(base,link)
        else:
            link = urlparse.urlunsplit(parsedLink)
        links.add(urlparse.urldefrag(link)[0])
    return urlUrl, parsedUrl, title, list(links)

def init_db(sites,conn):
    c = conn.cursor()
    c.execute('''create table site(url text primary key, title text, status integer, reason text, ctype text, clength text, location text, crawled integer)''')
    c.execute('''create table links(parent text, child text, constraint linkspkey primary key (parent,child))''')
    seen = set([])
    for site in sites:
        link = site
        while link:
            crawled = 1
            url2, purl, status, reason, ctype, clength, location = check_headers(link)
            if url2 in seen or len(list(seen)) >= 10:
                break
            seen.add(url2)
            if status == 200 and 'html' in ctype.lower() and 'http' in purl.scheme.lower() :
                link = None
                crawled = None
            elif 300<=reason<=399 and location:
                parsedLink = urlparse.urlsplit(location)
                if not parsedLink.scheme:
                    link = urlparse.urljoin(url2,location)
            else: 
                link = None

            c.execute('insert into site(url,status,reason,ctype,clength,location,crawled) values (?,?,?,?,?,?,?)',(url2, status, reason, ctype, clength, location, crawled))
    conn.commit()
    c.close()
def continue_crawl(conn):
    to_crawl = set([])
    crawled = set([])
    urls = set([])
    c = conn.cursor()
    c.execute('select url,crawled from site')
    for (url,nocrawl) in c:
        urls.add(url)
        if not nocrawl:
            to_crawl.add(url)
        else:
            crawled.add(url)

    while True:
        #print to_crawl
        try:
            url = to_crawl.pop()
        except KeyError:
            break
        try:
            url2, purl1, title, links = get_title_and_links(url)
        except:
            traceback.print_exc()
            print url
            continue
        for this_link in links:
            seen = set([])
            link = this_link
            while link:
                #print url2,link
                try:
                    c.execute('insert into links(parent,child) values (?,?)',(url2,link))
                except sqlite3.IntegrityError:
                    traceback.print_exc()
                    print "\nDuplicate: %s %s" % (url2,link)

                if link in urls or link in seen or len(list(seen)) >= 10 or (urlparse.urlsplit(link)).netloc != purl1.netloc:
                    break

                seen.add(link)
                urls.add(link)

                url3, purl, status, reason, ctype, clength, location = check_headers(link)
                
                nocrawl2 = 1
                if status == 200 and 'html' in ctype.lower() and 'http' in purl.scheme.lower() :
                    link = None
                    nocrawl2 = None
                elif 300<=reason<=399 and location:
                    parsedLink = urlparse.urlsplit(location)
                    if not parsedLink.scheme:
                        link = urlparse.urljoin(url2,location)
                else: 
                    link = None

                c.execute('insert into site(url,status,reason,ctype,clength,location,crawled) values (?,?,?,?,?,?,?)',(url3, status, reason, ctype, clength, location, nocrawl2))
                if nocrawl2:
                    crawled.add(url3)
                else:
                    to_crawl.add(url3)

        c.execute('update site set title=?, crawled=1 where url=?',(title,url2))
        
        conn.commit()
        print '.',


if __name__=='__main__':
    sites = ['http://www.example.com/']
    db = './www.db'
    conn = sqlite3.connect(db)
    #init_db(sites, conn)
    continue_crawl(conn)

