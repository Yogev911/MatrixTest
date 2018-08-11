import test
import file_handler
import scrap
import multiprocessing
import api_handler
import os
import conf

if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER)):
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER))
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER)):
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER))

    print('Init DB')
    api_handler.db.init_db()
    print('Starting scrapper')
    scrapper = multiprocessing.Process(target=scrap.get_articles)
    scrapper.start()
    print('Starting listener')
    listener = multiprocessing.Process(target=file_handler.lisener)
    listener.start()
    print('Starting REST API')
    api = multiprocessing.Process(target=test.run)
    api.start()
