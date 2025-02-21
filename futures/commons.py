import requests 
from bs4 import BeautifulSoup
import os
import glob
import pandas as pd
import hashlib
import random
import json

import numpy as np

from lxml import html
from bs4 import BeautifulSoup
import trafilatura
import io

import os, openai, datetime, hashlib, re
import time

import pandas as pd

import string
LETTERS = string.ascii_uppercase


import pandas as pd
import os


import re
    
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')
FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3



def find_md_links(md):
    """ Return dict of links in markdown """

    links = list(INLINE_LINK_RE.findall(md))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(md))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(md))

    for key in footnote_links.keys():
        links.append((footnote_links[key], footnote_urls[footnote_links[key]]))

    return links

def get_cache(BASE_URL,moar=[]):
    """Returns the list of pages from substack"""
    page_url = "https://"+BASE_URL+"/archive"

    page_sourced = requests.get(page_url).content 

    html_content = BeautifulSoup(page_sourced, "html.parser")
    # #main > div.archive-page.typography.use-theme-bg > div > div > div.portable-archive-list > div:nth-child(19) > div.post-preview-content > a.post-preview-title.newsletter
    links = html_content.findAll('a', class_="pencraft")
    #print(len(links)) 
    pages = [i.get('href') for i in links if (not (i.get('href') is None))]
    if len(moar):
        for x in moar:
            pages.append(x)
    pages = [ i for i in pages if "https://"+BASE_URL+"/p/" in i ]
    pages = list(set([ i for i in pages if not i.endswith("comments") ]))
    len(pages), pages

    return pages

def txtRead(filename):
    with io.open(filename,'r',encoding='utf8') as f:
        txt= f.read()
    return txt
