import mysql.connector
import traceback
import json
import ast
import re
import conf
import textract
from os import listdir
from os.path import isfile, join
from shutil import copyfile

OK_MESSAGE = json.dumps({'msg': 'True'})
import os
import time, datetime

SAVE_PATH = 'uploads/'
STOP_LIST = set(['json', 'txt', 'xlsx'])
SPECIAL_CHARS = set(['.', ',', '(', ')', '(', '"'])


def create_res_obj(data, success=True):
    '''
    create return obj with array of data.
    :param data: dict of 'data_obj'
    :param success: json format for response
    :return:
    '''
    return json.dumps({
        "success": success,
        "data": data
    })


def data_obj(author, content, docname, path):
    '''
    create node of data object
    :param author: string
    :param content: string
    :param docname: string
    :param path: string
    :return: data_obj
    '''
    return {
        "docname": docname,
        "author": author,
        "path": path,
        "content": content
    }


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class db_handler(object):
    # __metaclass__ = Singleton

    def __init__(self):
        self.user = 'root'
        self.password = ''
        self.host = '192.168.1.30'
        self.database = 'dataretrieval'
        self.port = '3306'
        self.cnx = None

    def connect(self):
        try:
            self.cnx = mysql.connector.connect(user=self.user,
                                               password=self.password,
                                               host=self.host,
                                               database=self.database,
                                               port=self.port)
            print('yes!')
        except Exception as e:
            return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                                  success=False)

    def disconnect(self):
        if self.cnx:
            self.cnx.close()

    # singelton
    @property
    def connection(self):
        if self.cnx is None:
            return self.connect()
        return self.cnx

    def get_all_tables(self):
        query = "SHOW TABLES"
        cursor = self.connection.cursor()
        cursor.execute(query)
        tables = cursor.fetchall()
        return tables

    def show_table(self, table_name):
        query = "SELECT * FROM " + table_name
        cursor = self.connection.cursor()
        cursor.execute(query)
        tables = []
        tables = cursor.fetchall()
        return tables

    def drop_all_tables(self):
        tables_names = []
        cursor = self.connection.cursor()
        tables_names = self.get_all_tables()
        for table_name in tables_names:
            str = ''.join(table_name)
            try:
                cursor.execute("drop table " + str)
            except Exception as e:
                return create_res_obj({'traceback': traceback.format_exc(),
                                       'msg': "{}".format(e.args),
                                       'text': "DROP TABLE failed WITH TABLE {} ".format(str)},
                                      success=False)


db = db_handler()


def init_db():
    global db
    db.connect()
    cursor = db.cnx.cursor()
    query = "DELETE FROM `indextable`"
    cursor.execute(query)
    db.cnx.commit()
    query = "DELETE FROM `doc_tbl`"
    cursor.execute(query)
    db.cnx.commit()
    query = "DELETE FROM `postfiletable`"
    cursor.execute(query)
    db.cnx.commit()
    query = "ALTER TABLE indextable AUTO_INCREMENT = 1"
    cursor.execute(query)
    db.cnx.commit()
    query = "ALTER TABLE doc_tbl AUTO_INCREMENT = 1"
    cursor.execute(query)
    db.cnx.commit()
    query = "ALTER TABLE postfiletable AUTO_INCREMENT = 1"
    cursor.execute(query)
    db.cnx.commit()
    query = "DELETE FROM `hidden_files`"
    cursor.execute(query)
    db.cnx.commit()
    target_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), conf.UPLOAD_FOLDER)
    files = [f for f in listdir(target_uploads) if isfile(os.path.join(target_uploads, f))]
    if files:
        for file in files:
            path = os.path.join(target_uploads, file)
            print('delete file {}'.format(path))
            os.remove(path)
    print('folder {} is empty'.format(target_uploads))


def res_upload_file(file_name, path):
    try:
        global db
        db.connect()
        text = parse_file(path)
        values = parse_text_to_dict(text)
        doc_id = update_words_to_db(values['words_dict'], file_name, path, values['author'], values['year'],
                                    values['intro'])
        db.disconnect()
        return {'docid': doc_id, 'docname': file_name, 'path': path, 'author': values['author'],
                'year': values['year'], 'intro': values['intro'], 'content': text}
    except Exception as e:
        return {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)}


def get_file_extention(file_name):
    return str(file_name).split('.')[-1].lower()


def parse_file(file_path):
    if os.path.splitext(file_path)[1] == '.txt':
        return parse_text(file_path)
    else:
        return textract.process(file_path)


def index_text(text):
    regex = re.compile('[^a-zA-Z \']')
    text = regex.sub('', text)
    text = ' '.join(text.split())
    words_dict = {}
    for line in text.split('\n'):
        for word in line.split(' '):
            # if word[-1:] == ',' or word[-1:] == ')' or word[-1:] == '(' or word[-1:] == '.': word = word[:-1]
            if word[:1] == '\'': word = word[1:]
            # if word == '' or word == ' ':
            #     continue
            if word not in words_dict:
                words_dict[word] = 1
            else:
                words_dict[word] += 1
    return words_dict


def parse_text_to_dict(text):
    author = ''
    year = ''
    intro = ''
    words_dict = {}
    for line in text.split('\n'):
        if line.startswith(conf.TEMPLATES[0]):
            author = line.replace(conf.TEMPLATES[0], '').strip()
        elif line.startswith(conf.TEMPLATES[1]):
            year = line.replace(conf.TEMPLATES[1], '').strip()
        elif line.startswith(conf.TEMPLATES[2]):
            intro = line.replace(conf.TEMPLATES[2], '').strip()
        else:
            tmp_line = conf.REGEX.sub('', line).lower()
            for word in tmp_line.split(' '):
                if word[:1] == '\'': word = word[1:]
                if word == '' or word == ' ':
                    continue
                if word not in words_dict:
                    words_dict[word] = 1
                else:
                    words_dict[word] += 1

    values = {'words_dict': words_dict,
              'author': author,
              'year': year,
              'intro': intro
              }
    return values


def parse_text(file_name):
    file = open(file_name, 'r')
    return file.read()
    # with open(file_name, 'r').read().lower() as f:
    #     return f


def parse_doc(file_name):
    (fi, fo, fe) = os.popen3('catdoc -w "%s"' % file_name)
    fi.close()
    retval = fo.read()
    erroroutput = fe.read()
    fo.close()
    fe.close()
    if not erroroutput:
        return retval
    else:
        raise OSError("Executing the command caused an error: %s" % erroroutput)


def _get_doc_id_by_file_name(docname):
    docid = None
    # print "working on {}".format(docname)
    cursor = db.cnx.cursor()
    query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    cursor.execute(query, data)
    try:
        ret = cursor.fetchone()
        docid = ret[0]
    except:
        pass
    if docid:
        return docid
    return 0


def update_words_to_db(words_dict, file_name, path, author, year, intro):
    if not _is_duplicated_file(file_name):
        for key in sorted(words_dict.iterkeys()): _update_word(key, words_dict[key], file_name, path,
                                                               author, year, intro)
    return _get_doc_id_by_file_name(file_name)


def _is_duplicated_file(docname):
    docid = None
    cursor = db.cnx.cursor()
    query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    cursor.execute(query, data)
    try:
        ret = cursor.fetchone()
        docid = ret[0]
    except:
        pass
    if docid:
        return True
    return False


def _update_word(term, term_hits, file_name, path, author, year, intro):
    try:
        cursor = db.cnx.cursor()
        query = ("SELECT postid,hit FROM Indextable WHERE term=%s")
        data = (term,)
        cursor.execute(query, data)
        try:
            ret = cursor.fetchone()
            postid = ret[0]
            hit = ret[1]
        except:
            pass
        if not ret:
            # found new term
            new_postid = _add_new_term(term)
            docid = _insert_row_doc_tbl(file_name, author, path, year, intro)
            _insert_row_postfile_tbl(new_postid, term_hits, docid)

        else:
            # found term which is alreay exists
            _inc_hit_indextbl(hit, postid)
            docid = _insert_row_doc_tbl(file_name, author, path, year, intro)
            _insert_row_postfile_tbl(postid, term_hits, docid)
        cursor.close()
        return True
    except:
        print(traceback.format_exc())
        return False


def _add_new_term(term):
    '''
    :param term: add new row with term, hit = 1
    :return: the new postfile id
    '''
    cursor = db.cnx.cursor()
    query = ("INSERT INTO Indextable (term, hit) VALUES (%s , 1)")
    data = (term,)
    cursor.execute(query, data)
    new_postfile_id = cursor.lastrowid
    db.cnx.commit()
    try:
        query = ("SELECT postid FROM Indextable WHERE term=%s")
        data = (term,)
        cursor.execute(query, data)
        new_postfile_id = cursor.fetchone()[0]
    except:
        pass
    db.cnx.commit()
    cursor.close()
    return new_postfile_id


def _inc_hit_indextbl(old_hit, postid):
    '''
    :param old_hit: number of doc hits
    :param postid: postid to update
    :return: bool
    '''
    cursor = db.cnx.cursor()
    new_hit = old_hit + 1
    query = ("UPDATE `indextable` SET `hit` = {} WHERE `indextable`.`postid` = %s").format(str(new_hit))
    data = (postid,)
    cursor.execute(query, data)
    db.cnx.commit()
    cursor.close()
    return True


def _insert_row_postfile_tbl(postid, term_hits, docid):
    cursor = db.cnx.cursor()
    query = ("INSERT INTO postfiletable (postid, hit, docid) VALUES (%s , %s , %s)")
    data = (postid, term_hits, docid)
    cursor.execute(query, data)
    db.cnx.commit()
    cursor.close()
    return True


def _insert_row_doc_tbl(docname, author, path, year, intro):
    '''
    :param docname:
    :param author:
    :param path:
    :return: id of the row
    '''
    docid = None
    cursor = db.cnx.cursor()
    query = ("SELECT docid FROM doc_tbl WHERE path=%s")
    data = (path,)
    cursor.execute(query, data)
    try:
        ret = cursor.fetchone()
        docid = ret[0]
    except:
        pass

    if docid:
        return docid
    else:
        query = ("INSERT INTO doc_tbl (docname, author,path, year, intro, hidden) VALUES (%s , %s , %s, %s , %s,%s)")
        data = (docname, author, path, year, intro, 0)
        cursor.execute(query, data)
        db.cnx.commit()
        query = ("SELECT docid FROM doc_tbl WHERE path=%s")
        data = (path,)
        cursor.execute(query, data)
        try:
            docid = cursor.fetchone()[0]
        except:
            pass
        db.cnx.commit()
        cursor.close()
        return docid


def list_hidden_files():
    cursor = db.cnx.cursor()
    query = "SELECT docid FROM hidden_files "
    try:
        cursor.execute(query)
        return [doc[0] for doc in cursor]
    except:
        return []


def findWholeWord(w):
    return re.compile(r'\b{}\b'.format(w)).search


def is_in_order(arg1, arg2, list):
    any([arg1, arg2] == list[i:i + 2] for i in range(len(list) - 1))

    def _get_doc_hits(word):
        try:
            ret = None
            cursor = db.cnx.cursor()
            query = ("SELECT hit FROM indextable WHERE term=%s")
            data = (word,)
            cursor.execute(query, data)
            ret = cursor.fetchone()
            if ret:
                return ret[0]
            return 0
        except:
            return 0


def _get_post_id_by_term(word):
    try:
        cursor = db.cnx.cursor()
        query = ("SELECT postid FROM indextable WHERE term=%s")
        data = (word,)
        cursor.execute(query, data)
        ret = cursor.fetchone()
        try:
            cursor.fetchall()
        except:
            pass
        return ret[0]
    except:
        return 0


def _get_word_weight(doc, words):
    try:
        doc_weight = 0
        post_ids = [_get_post_id_by_term(word) for word in words]
        for postid in post_ids:
            query = ("SELECT hit FROM postfiletable WHERE postid=%s and docid =%s")
            data = (postid, doc,)
            cursor = db.cnx.cursor()
            cursor.execute(query, data)
            ret = cursor.fetchone()
            doc_weight += ret[0]
            try:
                cursor.fetchall()
            except:
                pass
        return doc, doc_weight
    except:
        return doc, 0


def _rank(docs, words_list):
    ranking = [_get_word_weight(doc, words_list) for doc in docs]
    return ranking


def res_query(query):
    class MyTransformer(ast.NodeTransformer):
        def visit_Str(self, node):
            return ast.Set(words_dict[node.s])

    try:
        global db
        db.connect()
        data = []
        hidden_files = list_hidden_files()

        operator = ['OR', 'AND', 'NOT']
        data = []

        # query = 'hi two "two birds in the sky" my "hello\'"     name AND is OR (yogev   "heskia\'" dfk)   OR ("hiii" OR (bla OR boom)) NOT hi two "two" hello are'
        query = query.replace("\'", "'")

        # check for more than one operator in a row
        splited_query = query.split()
        duplicate_op_counter = 0
        for first in operator:
            for second in operator:
                if not is_in_order(first, second, splited_query):
                    duplicate_op_counter += 1
        if duplicate_op_counter < 9:
            # bad query detet
            for op in operator:
                query = re.sub(r'\b' + op + r'\b', ' ', query)

        tmp_quote = ''
        quotes_string = re.findall(r'"([^"]*)"', query)
        if quotes_string:
            for text in quotes_string:
                if len(text.split()) > 1:
                    words_in_quotes = text.split()
                    for item in words_in_quotes:
                        tmp_quote += ' \"' + item + '\" '
                    query = query.replace('\"{}\"'.format(text), tmp_quote, 1)
                tmp_quote = ''

        # check for terms only without operators
        tmp_query = re.sub(' +', ' ', query)
        if tmp_query.endswith(' AND') or tmp_query.endswith(' OR') or tmp_query.endswith(' NOT'):
            tmp_query = query.replace('AND', '').replace('OR', '').replace('NOT', '')

        if not query.replace(')', '').replace('(', '').replace('AND', '').replace('OR', '').replace('NOT', '').replace(
                '"', '').strip():
            query = 'error'

        if not ((findWholeWord(operator[0])(query)) or (findWholeWord(operator[1])(query)) or (
                findWholeWord(operator[2])(query))):
            query = query.strip()
            query = ' OR '.join(query.split())

        tmp_query = re.split(r'(OR|AND|NOT)', query)  # split to text OP text OP text

        new_query = ''
        for text in tmp_query:
            if text in operator:
                new_query += text + ' '
                continue
            if len(text.split()) > 1:
                # if len(text.replace('(', '').replace(')', '').split()) > 1:
                new_query += '('
                for word in text.split():
                    new_query += word + ' OR '
                new_query = new_query[:-3]
                new_query += ') '
            else:
                new_query += text

        # remove stop list terms
        query = new_query
        quotes_words_indexs = []
        for word in new_query.split():
            for term in conf.STOP_LIST:
                tmp_word = word.replace(')', '').replace('(', '').replace('"', '')
                if term == tmp_word:
                    if word[0] == '\"' and word[-1] == '\"':
                        quotes_words_indexs = [(m.start(0), m.end(0)) for m in
                                               re.finditer(r'\b{}\b'.format(term), query)]
                        if quotes_words_indexs:
                            for tup in quotes_words_indexs:
                                if query[tup[0] - 1] == '\"' and query[tup[1]] == '\"':
                                    query = query[:tup[0] - 1] + '$' + query[tup[0]:]
                                    query = query[:tup[1]] + '$' + query[tup[1] + 1:]
                                    break
                                else:
                                    continue
                    else:
                        quotes_words_indexs = [(m.start(0), m.end(0)) for m in
                                               re.finditer(r'\b{}\b'.format(tmp_word), query)]
                        # query = new_query.replace(tmp_word, 'STOPPED')
                        for tup in quotes_words_indexs:
                            if query[tup[0] - 1] == '$':
                                continue
                            else:
                                start = query[:tup[0]]
                                mid = ' stoppedword '
                                end = query[tup[1] + 1:]
                                query_helper = start + mid + end
                                query = query_helper
                                break

            quotes_words_indexs = []
        query = re.sub(' +', ' ', query)
        query = query.replace('$', ' ')
        # careful
        query = query.replace('\"', '')
        tmp_query = query.replace(')', '').replace('(', '').replace('AND', '').replace('OR', '').replace('NOT', '')
        tmp_query = tmp_query.lower()
        words_list = tmp_query.split()

        words_list_in_quotes = ['\'' + re.sub("'", "\\'", w) + '\'' for w in words_list]
        words_dict = {}
        for i in range(len(words_list)):
            words_dict[words_list[i]] = words_list_in_quotes[i]

        processed_query = ''
        for item in query.split():
            if item.lower() in words_dict:
                processed_query += words_dict[item.lower()]
            elif item.replace(')', '').lower() in words_dict:
                b = item.count(')')
                processed_query += words_dict[item.replace(')', '').lower()]
                processed_query += b * ')'
            elif item.replace('(', '').lower() in words_dict:
                b = item.count('(')
                processed_query += b * '('
                processed_query += words_dict[item.replace('(', '').lower()]
            else:
                processed_query += item
            processed_query += ' '

        print(words_dict)
        print(words_list)
        for k, v in words_dict.iteritems():
            if k == 'stoppedword':
                ast_list = create_ast_list([])
            else:
                doc_list = get_doc_list_by_term(k, hidden_files, words_list)
                ast_list = create_ast_list(doc_list)
            words_dict[k] = ast_list

        words_dict = dict({k.replace('*', ''): v for k, v in words_dict.items()})
        words_list = list([word.replace('*', '') for word in words_list])
        processed_query = processed_query.replace('*', '')
        processed_query = processed_query.replace('AND', '&')
        processed_query = processed_query.replace('OR', '|')
        processed_query = processed_query.replace('NOT', '-')

        input_code = ast.parse(processed_query, mode='eval')
        MyTransformer().visit(input_code)
        fixed = ast.fix_missing_locations(input_code)
        code = compile(fixed, '<string>', 'eval')
        result = eval(code)
        result = list(result)
        ranked_doc = _rank(result, words_list)
        sorted_by_rank = sorted(ranked_doc, key=lambda tup: tup[1])
        sorted_docit = [tup[0] for tup in sorted_by_rank]
        sorted_docit = sorted_docit[::-1]
        result = sorted_docit
        for doc_id in result:
            data.append(get_data_by_docid(doc_id, words_list))

        db.disconnect()
        return create_res_obj(data)
    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                              success=False)


def create_ast_list(num_list):
    l = []
    if num_list is None:
        return l
    for num in num_list:
        l.append(ast.Num(num))
    return l


def get_doc_list_by_term(term, hidden_files, words_list):
    postid = None
    term = term.replace('*', '%')
    doc_list = []
    cursor = db.cnx.cursor()
    query = ("SELECT postid,term FROM indextable WHERE term LIKE %s")
    data = (term,)
    cursor.execute(query, data)
    post_ids = []
    new_words = []
    try:
        for row in cursor:
            post_ids.append(row[0])
            new_words.append(row[1])
        for word in new_words:
            if word not in words_list:
                words_list.append(word)
        # ret = cursor.fetchone()
        # postid = ret[0]
        # cursor.fetchall()
    except:
        pass
    for postid in post_ids:
        if postid is None:
            return doc_list
        query = ("SELECT docid FROM postfiletable WHERE postid=%s")
        data = (postid,)
        cursor.execute(query, data)
        try:
            for row in cursor:
                doc_list.append(row[0])
        except:
            pass

    new_list = [doc for doc in doc_list if doc not in hidden_files]
    return new_list


def get_data_by_docid(doc_id, word_list):
    path = None
    docname = None
    author = None
    year = None
    intro = None
    cursor = db.cnx.cursor()
    query = ("SELECT docid,docname,author,path,year,intro, hidden FROM doc_tbl WHERE docid =%s")
    data = (doc_id,)
    cursor.execute(query, data)
    try:
        ret = cursor.fetchone()
        docid = ret[0]
        docname = ret[1]
        author = ret[2]
        path = ret[3]
        year = ret[4]
        intro = ret[5]
        hidden = ret[6]
    except:
        pass
    if path is not None:
        with open(path, 'r') as f:
            content = f.read()
    else:
        content = 'Empty'
    content = re.sub(r'^' + conf.TEMPLATES[0] + '.*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'^' + conf.TEMPLATES[1] + '.*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'^' + conf.TEMPLATES[2] + '.*\n?', '', content, flags=re.MULTILINE)

    for term in word_list:
        content = re.sub(r'\b' + term + r'\b', '<span class="mark">' + term + '</span>', content,
                         flags=re.IGNORECASE)
    doc_data = {
        "docid": docid,
        "docname": docname,
        "auther": author,
        "path": path,
        "year": year,
        "intro": intro,
        "hidden": hidden,
        "content": content

    }
    return doc_data


def delete_doc(docname):
    try:
        global db
        db.connect()
        cursor = db.cnx.cursor()
        postid_list = []
        query = ("SELECT path FROM doc_tbl WHERE docname=%s")
        data = (docname,)
        cursor.execute(query, data)
        doc_path = cursor.fetchone()[0]
        query = ("SELECT docid FROM doc_tbl WHERE path=%s")
        data = (doc_path,)
        cursor.execute(query, data)
        docid = cursor.fetchone()[0]
        query = ("SELECT postid FROM postfiletable WHERE docid=%s")
        data = (docid,)
        cursor.execute(query, data)
        for row in cursor:
            postid_list.append(row[0])
        for postid in postid_list:
            query = ("SELECT hit FROM indextable WHERE postid=%s")
            data = (postid,)
            cursor.execute(query, data)
            hit = cursor.fetchone()[0]
            if hit == 1:
                query = ("DELETE FROM indextable WHERE postid=%s")
                data = (postid,)
                cursor.execute(query, data)
                db.cnx.commit()
            else:
                new_hit = hit - 1
                query = ("UPDATE `indextable` SET `hit` = {} WHERE `indextable`.`postid` = %s").format(str(new_hit))
                data = (postid,)
                cursor.execute(query, data)
                db.cnx.commit()
        query = ("DELETE FROM postfiletable WHERE docid=%s")
        data = (docid,)
        cursor.execute(query, data)
        query = ("DELETE FROM doc_tbl WHERE docid=%s")
        data = (docid,)
        cursor.execute(query, data)
        query = ("DELETE FROM hidden_files WHERE docid=%s")
        data = (docid,)
        cursor.execute(query, data)
        if os.path.exists(doc_path):
            os.remove(doc_path)
        db.cnx.commit()
        db.disconnect()

        return create_res_obj(data)
    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                              success=False)


def lisener(tmp_folder):
    target_tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), tmp_folder)
    if not os.path.exists(target_tmp):
        os.makedirs(target_tmp)
    while True:
        print('searching for files....')
        files = [f for f in listdir(target_tmp) if isfile(os.path.join(target_tmp, f))]
        if files:
            print('found file!')
            target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
            print(target)
            for file in files:
                path = os.path.join(target_tmp, file)
                print('working on file{}'.format(path))
                uuid = str(time.time()).split('.')[0]
                filename = uuid + file
                target_path = os.path.join(target, filename)
                copyfile(path, target_path)
                res_upload_file(file, target_path)
                os.remove(path)
        time.sleep(5)


def scrapper():
    pass


def hide_doc(docname):
    try:
        global db
        db.connect()
        cursor = db.cnx.cursor()

        query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
        data = (docname,)
        cursor.execute(query, data)
        docid = cursor.fetchone()[0]

        query = ("SELECT * FROM hidden_files WHERE docid = %s")
        data = (docid,)
        cursor.execute(query, data)
        row_count = cursor.rowcount
        if row_count == -1:
            x = cursor.fetchall()
            cursor = db.cnx.cursor()
            query = ("INSERT INTO hidden_files (docid) VALUES (%s)")
            data = (docid,)
            cursor.execute(query, data)
            query = ("UPDATE doc_tbl SET hidden = 1 WHERE docid = %s ")
            data = (docid,)
            cursor.execute(query, data)
            db.cnx.commit()
            data = [{'file_hidden': 'True'}]
        else:
            data = [{'file_hidden': 'False'}]
        db.disconnect()

        return create_res_obj(data)
    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                              success=False)


def get_all_docs():
    try:
        global db
        db.connect()
        data = []
        cursor = db.cnx.cursor()
        query = "SELECT * FROM doc_tbl"
        cursor.execute(query)
        for row in cursor:
            data.append({
                'docid': row[0],
                'docname': row[1],
                'author': row[2],
                'path': row[3],
                'year': row[4],
                'intro': row[5],
                'hidden': row[6],
                'content': open(row[3], 'r').read()

            })

        db.disconnect()
        return create_res_obj(data)
    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                              success=False)


def restore_doc(docname):
    try:
        global db
        db.connect()
        cursor = db.cnx.cursor()

        query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
        data = (docname,)
        cursor.execute(query, data)
        docid = cursor.fetchone()[0]

        query = ("SELECT * FROM hidden_files WHERE docid = %s")
        data = (docid,)
        cursor.execute(query, data)
        row_count = cursor.rowcount
        if row_count == -1:
            x = cursor.fetchall()
            cursor = db.cnx.cursor()
            query = ("DELETE FROM hidden_files WHERE docid = %s")
            data = (docid,)
            cursor.execute(query, data)
            query = ("UPDATE doc_tbl SET hidden = 0 WHERE docid = %s ")
            data = (docid,)
            cursor.execute(query, data)
            db.cnx.commit()
            data = [{'file_restored': 'True'}]
        else:
            data = [{'file_restored': 'False'}]
        db.disconnect()

        return create_res_obj(data)
    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                              success=False)


def getfile(docname):
    global db
    db.connect()
    cursor = db.cnx.cursor()
    query = ("SELECT * FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    cursor.execute(query, data)
    try:
        row = cursor.fetchone()
        db.disconnect()
        return create_res_obj({
            'docid': row[0],
            'docname': row[1],
            'author': row[2],
            'path': row[3],
            'year': row[4],
            'intro': row[5],
            'hidden': row[6],
            'content': open(row[3], 'r').read()

        })

    except Exception as e:
        return create_res_obj({'traceback': traceback.format_exc(), 'msg': "{} {}".format(e.message, e.args)},
                              success=False)
