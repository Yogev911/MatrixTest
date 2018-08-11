import traceback
import re
from time import sleep

import newspaper

import os
import conf


def get_articles():
    try:
        target = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER)
        while True:
            for site in conf.SITES:
                print(f'start working on site {site}')
                paper = newspaper.build(site, memoize_articles=False)
                for article in paper.articles:
                    try:
                        if article.url.endswith('index.html'):
                            print(article.url)
                            sleep(10)
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
                print(f'done with site {site}')
    except:
        print(traceback.format_exc())

def write_article(article, article_file_path):
    pre_data = f'''#Author name : {",".join(article.authors)}
#Year : {str(article.publish_date)}
#Intro : {article.summary}
#URL : {article.url}
'''
    data = pre_data + article.text
    with open(article_file_path, 'w', encoding='utf-8') as f:
        f.write(data)


if __name__ == '__main__':
    get_articles()
