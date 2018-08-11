import traceback
import re
from multiprocessing import Process, Manager
import newspaper

import os
import conf
import utils

target = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER)


def get_articles():
    with Manager() as manager:
        filename_cache = manager.list()
        try:
            while True:
                for site in conf.SITES:
                    print(f'start working on site {site}')
                    paper = newspaper.build(site, memoize_articles=False)
                    chunks = utils.chunks(paper.articles, conf.CHUNK)
                    pool = [Process(target=extract_article, args=(chunk, paper.brand, filename_cache)) for chunk in
                            chunks]
                    try:
                        for proc in pool:
                            proc.start()
                        for proc in pool:
                            proc.join()
                        print(f'done working on site {site}')
                        print(f'Number of articles so far: {len(filename_cache)}')
                    except:
                        print(f'Failed starting process {traceback.format_exc()}')
                        print('Killing all scraping process')
                        for proc in pool:
                            if proc.is_alive():
                                proc.join(10)
                                if proc.is_alive():
                                    proc.terminate()
                        print('Done killing process, preforming restart')
        except:
            print(traceback.format_exc())


def extract_article(article_chunks, brand, filename_cache):
    for article in article_chunks:
        try:
            if brand not in article.url:
                continue
            article.download()
            article.parse()
            if not (
                    article.title or article.authors or article.publish_date or article.summary or article.text):
                raise ValueError('bad article!')
            article_file_name = re.sub('[^a-zA-Z0-9-_\s]+', '', article.title) + '.txt'
            article_file_path = os.path.join(conf.SCRAP_FOLDER, article_file_name)
            if os.path.exists(os.path.join(target, article_file_name)):
                continue
            if article.title in filename_cache:
                continue
            filename_cache.append(article.title)
            print(article.url)
            write_article(article, article_file_path)
            try:
                os.rename(article_file_path, os.path.join(target, article_file_name))
            except FileExistsError:
                print(f'duplicate file, removing {article_file_path}')
                os.remove(article_file_path)
        except ValueError as v:
            print(f'Error {v}, on {article.url}')
        except newspaper.article.ArticleException as ae:
            print(f'Failed parse article {article.url}, Error {ae.args}')
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


if __name__ == '__main__':
    get_articles()
