#!/usr/bin/env python
# coding:utf-8
import sys
from keywordextraction import *

def main():

  text="""
  Jim took bus from New York, NY to Washington on Wednesday.
  """
  # load keyword classifier
  preload = True
  classifier_type = 'logistic'
  keyword_classifier = get_keywordclassifier(preload,classifier_type)['model']

  # extract top k keywords
  top_k = 15
  keywords = extract_keywords(text,keyword_classifier,top_k,preload)
  print(("ORIGINAL TEXT:\n%s\nTOP-%d KEYWORDS returned by model: %s \nner: %s \n" % (text,top_k, keywords['keywords'], keywords['named_entities'])))

if __name__ == '__main__':
	main()
