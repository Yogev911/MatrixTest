import newspaper
import os
import conf
from time import sleep, time
import api_handler
def get_articles():
    global article
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER)
    while True:
        for site in conf.SITES:
            paper = newspaper.build(site, memoize_articles=False)
            for article in paper.articles:
                try:
                    if article.url.endswith('index.html'):
                        print(article.url)
                        article.download()
                        article.parse()
                        article_file_name = article.title + '.txt'
                        article_file_path = os.path.join('tmp', article_file_name)

                        with open(article_file_path, 'w') as f:
                            pre_data = f'''# Author name : {str(article.authors)}
# Year : {str(article.publish_date)}
# Intro : {article.summary}'''
                            f.write(pre_data + article.text)

                        api_handler.res_upload_file(article_file_name, article_file_path)
                        uuid = str(time()).split('.')[0]
                        parsed_file_name = uuid + article_file_name
                        os.rename(article_file_path, os.path.join(target,parsed_file_name))
                        print(f'file {parsed_file_name} parsed and inserted to db.')
                        sleep(0.5)
                except:
                    pass


if __name__ == '__main__':
    get_articles()



