import random
import time
import traceback
import re
from time import sleep
from multiprocessing import Pool, Process
import newspaper

import os
import conf
import utils

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER)


def get_articles():
    try:
        while True:
            for site in conf.SITES:
                print(f'start working on site {site}')
                paper = newspaper.build(site, memoize_articles=False)
                pool = [Process(target=extract_article, args=(chunk,)) for chunk in utils.chunks(paper, conf.MAX_ITEMS)]
                for proc in pool:
                    proc.start()
                for proc in pool:
                    proc.join()
                print(f'done working on site {site}')
    except:
        print(traceback.format_exc())


def extract_article(article_chunks):
    for article in article_chunks:
        try:
            if article.url.endswith('index.html'):
                print(article.url)
                article.download()
                article.parse()
                if not (
                        article.title or article.authors or article.publish_date or article.summary or article.text):
                    raise ValueError('bad article!')
                article_file_name = re.sub('[^a-zA-Z0-9-_\s]+', '', article.title) + '.txt'
                article_file_path = os.path.join('scrap_news', article_file_name)

                write_article(article, article_file_path)
                try:
                    os.rename(article_file_path, os.path.join(target, article_file_name))
                except FileExistsError:
                    print(f'duplicate file, removing {article_file_path}')
                    os.remove(article_file_path)
        except:
            print(traceback.format_exc())
    print('done with chunk')



def write_article(article, article_file_path):
    pre_data = f'''#Author name : {",".join(article.authors)}
#Year : {str(article.publish_date)}
#Intro : {article.summary}
#URL : {article.url}
'''
    data = pre_data + article.text
    with open(article_file_path, 'w', encoding='utf-8') as f:
        f.write(data)


def bla(x):
    sleep(1)
    print(x, time.time())


if __name__ == '__main__':
    get_articles()
