import api
import file_handler
import scrap
import multiprocessing
import api_handler
import utils

if __name__ == '__main__':
    utils.validate_paths()

    print('Init DB')
    api_handler.db.init_db()
    print('Starting scrapper')
    scrapper = multiprocessing.Process(target=scrap.get_articles)
    scrapper.start()
    print('Starting listener')
    listener = multiprocessing.Process(target=file_handler.lisener)
    listener.start()
    print('Starting REST API')
    api = multiprocessing.Process(target=api.run)
    api.start()
