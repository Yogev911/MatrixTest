import os
from os import listdir
from os.path import isfile
from shutil import copyfile
import time
import api_handler
import conf

target_tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.TMP_FOLDER)
target_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER)


def lisener():
    filename_cache = []
    while True:
        print('searching for files....')
        files = [f for f in listdir(target_tmp) if isfile(os.path.join(target_tmp, f))]
        if files:
            for file in files:
                if file in filename_cache:
                    os.remove(os.path.join(target_tmp, file))
                    continue
                filename_cache.append(file)
                path = os.path.join(target_tmp, file)
                print('working on file{}'.format(path))
                uuid = str(time.time()).split('.')[0]
                filename = uuid + file
                target_path = os.path.join(target_uploads, filename)
                copyfile(path, target_path)
                api_handler.res_upload_file(file, target_path)
                os.remove(path)
        time.sleep(1)
