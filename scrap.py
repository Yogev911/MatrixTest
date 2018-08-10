import newspaper
from newspaper import Article
import os

cnn_paper = newspaper.build('http://cnn.com', memoize_articles=False)

for article in cnn_paper.articles:
    if article.url.endswith('index.html'):
        print(article.url)
        article.download()
        article.parse()
        with open(os.path.join('tmp',article.title+'.txt'), 'w') as f:
            pre_data = f'''# Author name : {str(article.authors)}
# Year : {str(article.publish_date)}
# Intro : {article.summary}'''
            f.write(pre_data + article.text)



# article = Article('http://money.cnn.com/2018/08/08/investing/startup-invest/index.html')
