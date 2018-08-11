import traceback
import ast
import re
import os
from db_util import DB_Handler
import utils
import conf

db = DB_Handler()


def res_upload_file(file_name, path):
    try:
        text = parse_file(path)
        values = parse_text_to_dict(text)
        doc_id = update_words_to_db(values['words_dict'], file_name, path, values['author'], values['year'],
                                    values['intro'], values['url'])
        return {'docid': doc_id, 'docname': file_name, 'path': path, 'author': values['author'],
                'year': values['year'], 'intro': values['intro'], 'content': text}
    except Exception as e:
        return {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)}


def parse_file(file_path):
    if os.path.splitext(file_path)[-1] == '.txt':
        return parse_text(file_path)
    else:
        return ''


def parse_text(file_name):
    with open(file_name, 'r') as f:
        data = f.read()
    return data


def parse_text_to_dict(text):
    author = ''
    year = ''
    intro = ''
    url = ''
    words_dict = {}
    for line in text.split('\n'):
        if line.startswith(conf.TEMPLATES[0]):
            author = line.replace(conf.TEMPLATES[0], '').strip()
        elif line.startswith(conf.TEMPLATES[1]):
            year = line.replace(conf.TEMPLATES[1], '').strip()
        elif line.startswith(conf.TEMPLATES[2]):
            intro = line.replace(conf.TEMPLATES[2], '').strip()
        elif line.startswith(conf.TEMPLATES[3]):
            url = line.replace(conf.TEMPLATES[3], '').strip()
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
              'intro': intro,
              'url': url}
    return values


def _get_doc_id_by_file_name(docname):
    query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    ret = db.run_query(query, data, one=True)
    try:
        docid = ret[0]
    except:
        docid = None
    if docid:
        return docid
    return 0


def update_words_to_db(words_dict, file_name, path, author, year, intro, url):
    if not _is_duplicated_file(file_name):
        for key in sorted(words_dict.keys()):
            _update_word(key, words_dict[key], file_name, path, author, year, intro, url)
    return _get_doc_id_by_file_name(file_name)


def _is_duplicated_file(docname):
    query = ("SELECT docid FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    ret = db.run_query(query, data, one=True)
    try:
        docid = ret[0]
    except:
        docid = False
    return bool(docid)


def _update_word(term, term_hits, file_name, path, author, year, intro, url):
    try:
        query = ("SELECT postid,hit FROM Indextable WHERE term=%s")
        data = (term,)
        ret = db.run_query(query, data, one=True)
        try:
            postid = ret[0]
            hit = ret[1]
        except:
            pass
        if not ret:
            # found new term
            new_postid = _add_new_term(term)
            docid = _insert_row_doc_tbl(file_name, author, path, year, intro, url)
            _insert_row_postfile_tbl(new_postid, term_hits, docid)

        else:
            # found term which is alreay exists
            _inc_hit_indextbl(hit, postid)
            docid = _insert_row_doc_tbl(file_name, author, path, year, intro, url)
            _insert_row_postfile_tbl(postid, term_hits, docid)
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
    new_hit = old_hit + 1
    query = ("UPDATE `indextable` SET `hit` = {} WHERE `indextable`.`postid` = %s").format(str(new_hit))
    data = (postid,)
    db.run_query(query, data, commit=True)
    return True


def _insert_row_postfile_tbl(postid, term_hits, docid):
    query = ("INSERT INTO postfiletable (postid, hit, docid) VALUES (%s , %s , %s)")
    data = (postid, term_hits, docid)
    db.run_query(query, data, commit=True)
    return True


def _insert_row_doc_tbl(docname, author, path, year, intro, url):
    '''
    :param docname:
    :param author:
    :param path:
    :return: id of the row
    '''
    query = ("SELECT docid FROM doc_tbl WHERE path=%s")
    data = (path,)
    ret = db.run_query(query, data, one=True)
    try:
        docid = ret[0]
    except:
        docid = None

    if docid:
        return docid
    else:
        query = (
            "INSERT INTO doc_tbl (docname, author,path, year, intro, hidden, url) VALUES (%s , %s , %s, %s , %s,%s,%s)")
        data = (docname, author, path, year, intro, 0, url)
        db.run_query(query, data, commit=True)

        query = ("SELECT docid FROM doc_tbl WHERE path=%s")
        data = (path,)
        ret = db.run_query(query, data, one=True)
        try:
            docid = ret[0]
        except:
            pass
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


def _get_post_id_by_term(word):
    try:
        query = ("SELECT postid FROM indextable WHERE term=%s")
        data = (word,)
        ret = db.run_query(query, data, one=True)
        try:
            return ret[0]
        except:
            return 0
    except:
        return 0


def _get_word_weight(doc, words):
    try:
        doc_weight = 0
        post_ids = [_get_post_id_by_term(word) for word in words]
        for postid in post_ids:
            query = ("SELECT hit FROM postfiletable WHERE postid=%s and docid =%s")
            data = (postid, doc,)
            ret = db.run_query(query, data, one=True)
            doc_weight += ret[0]
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
        hidden_files = list_hidden_files()
        operator = ['OR', 'AND', 'NOT']
        data = []
        query = query.replace("\'", "'")

        # check for more than one operator in a row
        splited_query = query.split()
        duplicate_op_counter = 0
        for first in operator:
            for second in operator:
                if not is_in_order(first, second, splited_query):
                    duplicate_op_counter += 1
        if duplicate_op_counter < 9:
            # bad query detect
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
                new_query += '('
                for word in text.split():
                    new_query += word + ' OR '
                new_query = new_query[:-3]
                new_query += ') '
            else:
                new_query += text

        # remove stop list terms
        query = new_query
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
        for k, v in words_dict.items():
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

        return utils.create_res_obj(data)
    except Exception as e:
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)


def create_ast_list(num_list):
    l = []
    if num_list is None:
        return l
    for num in num_list:
        l.append(ast.Num(num))
    return l


def get_doc_list_by_term(term, hidden_files, words_list):
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
    cursor.close()
    new_list = [doc for doc in doc_list if doc not in hidden_files]
    return new_list


def get_data_by_docid(doc_id, word_list):
    path = None
    docname = None
    author = None
    year = None
    intro = None
    query = ("SELECT docid,docname,author,path,year,intro, hidden FROM doc_tbl WHERE docid =%s")
    data = (doc_id,)
    try:
        ret = db.run_query(query, data, one=True)
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
        postid_list = []
        query = ("SELECT path FROM doc_tbl WHERE docname=%s")
        data = (docname,)
        doc_path = db.run_query(query, data, one=True)[0]
        query = ("SELECT docid FROM doc_tbl WHERE path=%s")
        data = (doc_path,)
        docid = db.run_query(query, data, one=True)[0]
        query = ("SELECT postid FROM postfiletable WHERE docid=%s")
        data = (docid,)
        for row in db.run_query(query, data):
            postid_list.append(row[0])
        for postid in postid_list:
            query = ("SELECT hit FROM indextable WHERE postid=%s")
            data = (postid,)
            hit = db.run_query(query, data, one=True)[0]
            if hit == 1:
                query = ("DELETE FROM indextable WHERE postid=%s")
                data = (postid,)
                db.run_query(query, data, commit=True)
            else:
                new_hit = hit - 1
                query = ("UPDATE `indextable` SET `hit` = {} WHERE `indextable`.`postid` = %s").format(str(new_hit))
                data = (postid,)
                db.run_query(query, data, commit=True)
        query = ("DELETE FROM postfiletable WHERE docid=%s")
        data = (docid,)
        db.run_query(query, data, commit=True)
        query = ("DELETE FROM doc_tbl WHERE docid=%s")
        data = (docid,)
        db.run_query(query, data, commit=True)
        query = ("DELETE FROM hidden_files WHERE docid=%s")
        data = (docid,)
        db.run_query(query, data, commit=True)
        if os.path.exists(doc_path):
            os.remove(doc_path)
        return utils.create_res_obj(data)
    except Exception as e:
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)


def hide_doc(docname):
    try:
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
        cursor.close()
        return utils.create_res_obj(data)
    except Exception as e:
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)


def get_all_docs():
    try:
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
        cursor.close()
        return utils.create_res_obj(data)
    except Exception as e:
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)


def restore_doc(docname):
    try:
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
        cursor.close()
        return utils.create_res_obj(data)
    except Exception as e:
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)


def getfile(docname):
    query = ("SELECT * FROM doc_tbl WHERE docname=%s")
    data = (docname,)
    try:
        row = db.run_query(query, data, one=True)
        db.disconnect()
        return utils.create_res_obj({
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
        return utils.create_res_obj({'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
                                    success=False)
