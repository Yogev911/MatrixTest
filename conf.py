import re
import json

HOST = '0.0.0.0'
PORT = '8080'

SITES = ['https://edition.cnn.com/', 'http://www.foxnews.com/']

TEMPLATES = ['#Author name :',
             '#Year :',
             '#Intro :',
             '#URL :']

REGEX = re.compile('[^a-zA-Z \']')

TMP_FOLDER = 'tmp'
UPLOAD_FOLDER = 'uploads'
SCRAP_FOLDER = 'scrap_news'

# words to ignore in the search query
STOP_LIST = ['two', 'yogev', 'heskia']

OK_MESSAGE = json.dumps({'msg': 'True'})

# number of workers will be len(total items)/CHUNK
CHUNK = 25
