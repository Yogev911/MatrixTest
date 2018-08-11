import mysql.connector
import traceback
import conf
from os import listdir
from os.path import isfile
import os
import utils


class DB_Handler(object):
    # __metaclass__ = Singleton

    def __init__(self):
        self._user = 'root'
        self._password = ''
        self._host = 'localhost'
        self._database = 'dataretrieval'
        self._port = '3306'
        self.cnx = self.connect()

    def connect(self):
        try:
            return mysql.connector.connect(user=self._user,
                                           password=self._password,
                                           host=self._host,
                                           database=self._database,
                                           port=self._port)
        except:
            print('Error connecting to DB')
            raise

    def disconnect(self):
        if self.cnx:
            self.cnx.close()

    def get_all_tables(self):
        query = "SHOW TABLES"
        cursor = self.cnx.cursor()
        cursor.execute(query)
        tables = cursor.fetchall()
        return tables

    def show_table(self, table_name):
        query = "SELECT * FROM " + table_name
        cursor = self.cnx.cursor()
        cursor.execute(query)
        tables = cursor.fetchall()
        return tables

    def drop_all_tables(self):
        cursor = self.cnx.cursor()
        tables_names = self.get_all_tables()
        for table_name in tables_names:
            str = ''.join(table_name)
            try:
                cursor.execute("drop table " + str)
            except Exception as e:
                return utils.create_res_obj({'traceback': traceback.format_exc(),
                                             'msg': "{}".format(e.args),
                                             'text': "DROP TABLE failed WITH TABLE {} ".format(str)},
                                            success=False)

    def init_db(self):
        query = "DELETE FROM `indextable`"
        self.run_query(query)

        query = "DELETE FROM `doc_tbl`"
        self.run_query(query)

        query = "DELETE FROM `postfiletable`"
        self.run_query(query)

        query = "ALTER TABLE indextable AUTO_INCREMENT = 1"
        self.run_query(query)

        query = "ALTER TABLE doc_tbl AUTO_INCREMENT = 1"
        self.run_query(query)

        query = "ALTER TABLE postfiletable AUTO_INCREMENT = 1"
        self.run_query(query)

        query = "DELETE FROM `hidden_files`"
        self.run_query(query)

        target_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER)
        files = [f for f in listdir(target_uploads) if isfile(os.path.join(target_uploads, f))]
        if files:
            for file in files:
                path = os.path.join(target_uploads, file)
                print('delete file {}'.format(path))
                os.remove(path)
        print('folder {} is empty'.format(target_uploads))

    def run_query(self, query, params=None, one=False, many=False, commit=False):
        '''
        :param query: SQL string
        :param params: Tuple of params
        '''
        cursor = self.cnx.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if commit:
            self.cnx.commit()
        if one:
            data = cursor.fetchone()
            cursor.close()
            return data
        elif many:
            data = cursor.fetchall()
            cursor.close()
            return data
        cursor.close()
        return None
