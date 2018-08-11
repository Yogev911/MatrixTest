import re
import json
local_db = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'dataretrieval',
    'port': '3306'
}
remote_db = {
    'user': 'id6748919_yogev166',
    'password': 'Yogev123456',
    'host': 'https://databases-auth.000webhost.com/sql.php?server=1&db=id6748919_yogevtest1&table=doc_tbl&pos=0&token=06808a5f2c34255d1e840ba780abfdd1',
    'database': 'id6748919_yogevtest1',
    'port': '3306'
}

TEMPLATES = ['#Author name :',
             '#Year :',
             '#Intro :',
             '#URL :']

REGEX = re.compile('[^a-zA-Z \']')

TMP_FOLDER = 'tmp'
UPLOAD_FOLDER = 'uploads'

STOP_LIST = ['two','yogev','heskia']

HIDDEN_FILES_ID = [12]

HOST='localhost'

SITES = ['https://edition.cnn.com/', 'http://www.foxnews.com/']

OK_MESSAGE = json.dumps({'msg': 'True'})

#number of workers will be len(total)/MAX_ITEMS
MAX_ITEMS = 25

