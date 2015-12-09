#!/usr/bin/env python
"""
apertium_wiki.py - Phenny Wikipedia Module
"""

import re
import web, json
from lxml import etree
import lxml.html
import lxml.html.clean

wikiuri = 'http://wiki.apertium.org/wiki/%s'
wikisearchuri = 'http://wiki.apertium.org/api.php?action=query&list=search&srlimit=1&format=json&srsearch=%s&srwhat=%s'


def format_term(term):
   term = web.quote(term)
   term = term[0].upper() + term[1:]
   term = term.replace(' ', '_')
   return term
   
def format_term_display(term):
   term = web.unquote(term)
   term = term[0].upper() + term[1:]
   term = term.replace(' ', '_')
   return term

def format_subsection(section):
   section = section.replace(' ', '_')
   section = web.quote(section)
   section = section.replace('%', '.')
   return section

def apertium_wiki(phenny, origterm, to_nick=None):
   term = format_term(origterm)
   
   try:
      html = str(web.get(wikiuri % (term)))
   except:
      apiResponse = json.loads(str(web.get(wikisearchuri % (term, 'title'))))
      if len(apiResponse['query']['search']):
        term = apiResponse['query']['search'][0]['title']
        html = str(web.get(wikiuri % (term)))
      else:
        apiResponse = json.loads(str(web.get(wikisearchuri % (term, 'text'))))
        if len(apiResponse['query']['search']):
          term = apiResponse['query']['search'][0]['title']
          html = str(web.get(wikiuri % (term)))
        else:
          phenny.reply("No wiki results for that term.")
          return
   
   page = lxml.html.fromstring(html)

   if "#" in origterm:
      section = format_subsection(origterm.split("#")[1])
      text = page.find(".//span[@id='%s']" % section)
      if text is None:
         phenny.reply("That subsection does not exist.")
         return
      text = text.getparent().getnext()
   else:
      paragraphs = page.findall('.//p')
      if len(paragraphs) > 2:
        text = page.findall('.//p')[1]
      else:
        text = page.findall(".//*[@id='mw-content-text']")[0]

   sentences = text.text_content().split(". ")
   sentence = '"' + sentences[0] + '"'
 
   maxlength = 430 - len((' - ' + wikiuri % (format_term_display(term))).encode('utf-8'))
   if len(sentence.encode('utf-8')) > maxlength: 
      sentence = sentence.encode('utf-8')[:maxlength].decode('utf-8', 'ignore')
      words = sentence[:-5].split(' ')
      words.pop()
      sentence = ' '.join(words) + ' [...]'

   if to_nick:
      phenny.say(to_nick + ', ' + sentence + ' - ' + wikiuri % (format_term_display(term)))      
   else:
      phenny.say(sentence + ' - ' + wikiuri % (format_term_display(term)))


def awik(phenny, input):
   """Search for something on Apertium wiki or 
   point another user to a page on Apertium wiki"""
   origterm = input.groups()[1]

   if "->" in origterm: return

   if not origterm: 
      return phenny.say('Perhaps you meant ".wik Zen"?')
   #origterm = origterm.encode('utf-8')

   match_point_cmd = r'point\s(\S*)\s(.*)'
   matched_point = re.compile(match_point_cmd).match(origterm)
   to_nick = None
   if matched_point:
       to_nick = matched_point.groups()[0]
       origterm = matched_point.groups()[1]

   apertium_wiki(phenny, origterm, to_nick=to_nick)


awik.rule = r'\.(awik)\s(.*)'
awik.example = '.awik Begiak or .awik point svineet Begiak'
awik.priority = 'high'


def awik2(phenny, input):
   nick, _, __, lang, origterm = input.groups()
   apertium_wiki(phenny, origterm, nick)


awik2.rule = r'(\S*)(:|,)\s\.(awik)(\.[a-z]{2,3})?\s(.*)'
awik2.example = 'svineet: .awik Begiak'
awik2.priority = 'high'


def awik3(phenny, input):
   _, lang, origterm, __, nick = input.groups()
   apertium_wiki(phenny, origterm, nick)


awik3.rule = r'\.(awik)(\.[a-z]{2,3})?\s(.*)\s(->|→)\s(\S*)'  
awik3.example = '.awik Linguistics -> svineet'
