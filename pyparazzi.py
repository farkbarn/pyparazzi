# -*- coding: utf-8 -*-
#
# Author: Wil Alvarez (aka Satanas)
# Feb 28, 2011

import re
import time
import urllib2
import datetime
from urllib import urlencode

# Config variables
TITLE = 'Galer&iacute;a de prueba'
COLUMNS = 5
HASHTAG = ''
TEMPLATE = 'html/template.html'
OUTPUT = 'html/test.html'

# Don't touch this :P
SERVICES = ['plixi.com', 'twitpic.com', 'instagr.am', 'moby.to', 'picplz.com']
TWITTER_URL = 'http://search.twitter.com/search.json'
STR_REQ = '%s?q=&ors=twitpic.com+moby.to+plixi.com+instagr.am+picplz.com&tag=%s&rpp=30'
URL_PATTERN = re.compile('((http://|ftp://|https://|www\.)[-\w._~:/?#\[\]@!$&\'()*+,;=]*)')
PLIXI_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (id=\"photo\") />')
PLIXI2_PATTERN = re.compile('<img (src=\".*?\") (alt=\".*?\") (style=\".*?\") />')
TWITPIC_PATTERN = re.compile('<img (class=\"photo\") (id=\"photo-display\") (src=\".*?\") (alt=\".*?\") />')
MOBY_PATTERN = re.compile('<img (class=\"imageLinkBorder\") (src=\".*?\") (id=\"main_picture\") (alt=\".*?\") />')
INSTAGR_PATTERN = re.compile('<img (src=\".*?\") (class=\"photo\") />')
PICPLZ_PATTERN = re.compile('<img (src=\".*?\") (width=\".*?\") (height=\".*?\") (id=\"mainImage\") (class=\"main-img\") (alt=\".*?\") />')

def _py26_or_greater():
    import sys
    return sys.hexversion > 0x20600f0
    
if _py26_or_greater():
    import json
else:
    import simplejson as json

def detect_urls(text):
    '''Returns an array with all URLs in a tweet'''
    urls = []
    match_urls = URL_PATTERN.findall(text)
    for item in match_urls:
        url = item[0]
        if url[-1] == ')':
            url = url[:-1]
        urls.append(url)
    return urls
    
def convert_time(str_datetime):
    ''' Take the date/time and convert it into Unix time'''
    month_names = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
        'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    date_info = str_datetime.split()
    
    if date_info[1] in month_names:
        month = month_names.index(date_info[1])
        day = int(date_info[2])
        year = int(date_info[5])
        time_info = date_info[3].split(':')
    else:
        month = month_names.index(date_info[2])
        day = int(date_info[1])
        year = int(date_info[3])
        time_info = date_info[4].split(':')
        
    hour = int(time_info[0])
    minute = int(time_info[1])
    second = int(time_info[2])
    
    d = datetime.datetime(year, month, day, hour, minute, second)
    
    i_hate_timezones = time.timezone
    if (time.daylight):
        i_hate_timezones = time.altzone
    
    dt = datetime.datetime(*d.timetuple()[:-3]) - \
         datetime.timedelta(seconds=i_hate_timezones)
    return time.strftime('%b %d, %I:%M %p', dt.timetuple())
    
def get_image_url(url, service):
    image_url = ''
    comment = ''
    handle = urllib2.urlopen(url)
    response = handle.read()
    if service == SERVICES[0]:
        code = PLIXI_PATTERN.findall(response)
        if len(code) <= 0:
            start = response.find('class="photo"><img src')
            end = response.find('>', start + 15) + 1
            piece = response[start:end]
            code = PLIXI2_PATTERN.findall(piece)
        
        if len(code) > 0:
            image_url = code[0][0][5:-1]
    elif service == SERVICES[1]:
        code = TWITPIC_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][2][5:-1]
            comment = code[0][3][5:-1]
    elif service == SERVICES[2]:
        code = INSTAGR_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][0][5:-1]
    elif service == SERVICES[3]:
        code = MOBY_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][1][5:-1]
            comment = code[0][3][5:-1]
    elif service == SERVICES[4]:
        code = PICPLZ_PATTERN.findall(response)
        if len(code) > 0:
            image_url = code[0][0][5:-1]
            comment = code[0][5][5:-1]
    
    return image_url, comment
    
def get_first_photo(text):
    for url in detect_urls(text):
        for srv in SERVICES:
            if url.find(srv) > 0:
                try:
                    return get_image_url(url, srv)
                except Exception, e:
                    print e
                    return None, None
    return None, None
    
def generate_image(user, timestamp, image_url, comment, first=False):
    _class = ' first' if first else ''
    
    try:
        return '''<div class="image%s">
            <a href="%s" rel="lytebox[pyparazzi]" title="%s">
                <img src="%s" width="150" height="150" />
            </a>
            <div class="author">Por: @%s</div>
            <div class="timestamp">%s</div>
        </div>''' % (_class, image_url, comment, image_url, user, timestamp)
    except:
        return '''<div class="image">
                <img src="" width="150" height="150" />
            <div class="author">No se pudo cargar la imagen</div>
        </div>'''
    
    
def main():
    urlreq = STR_REQ % (TWITTER_URL, HASHTAG)
    handle = urllib2.urlopen(urlreq)
    rtn = handle.read()
    response = json.loads(rtn)
    
    count = 0
    content = ''
    for tweet in response['results']:
        user = tweet['from_user']
        timestamp = convert_time(tweet['created_at'])
        image_url, comment = get_first_photo(tweet['text'])
        if image_url:
            first = True if (count % COLUMNS == 0) else False
            content += generate_image(user, timestamp, image_url, comment, first)
            count += 1
    
    fd = open(TEMPLATE, 'r')
    temp = fd.read()
    fd.close()
    
    page = temp.replace('$title$', TITLE)
    page = page.replace('$content$', content)
    
    fd = open(OUTPUT, 'w')
    fd.write(page)
    fd.close()

if __name__ == '__main__':
    main()
