import json
from flask_cors import CORS
from flask import Flask, request, jsonify
import os
import api_handler
import conf
import traceback
import threading
import scrap

app = Flask(__name__)
CORS(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/init', methods=['GET', 'POST'])
def init():
    try:
        api_handler.init_db()
        return api_handler.create_res_obj({'status': 'init success'})
    except Exception as e:
        return api_handler.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        x = api_handler.res_query(query)
        x = jsonify(x)
        return x
    elif request.method == 'GET':
        return jsonify(api_handler.OK_MESSAGE)


@app.route('/delete/<filename>', methods=['GET', 'POST'])
def delete(filename):
    try:
        x = api_handler.delete_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return api_handler.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/hide/<filename>', methods=['GET', 'POST'])
def hide(filename):
    try:
        x = api_handler.hide_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return api_handler.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format( e.args)},
            success=False)


@app.route('/restore/<filename>', methods=['GET', 'POST'])
def restore(filename):
    try:
        x = api_handler.restore_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return api_handler.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/getfile/<filename>', methods=['GET', 'POST'])
def getfile(filename):
    try:
        x = api_handler.getfile(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return api_handler.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route("/showall", methods=['GET', 'POST'])
def showall():
    if request.method == 'POST':
        return jsonify(api_handler.get_all_docs())
    return jsonify(json.dumps({'msg': 'dude this is POST only!@'}))

if __name__ == '__main__':
    api_handler.init_db()
    # try:
    #     threading.Thread(target=api_handler.lisener, args=(conf.TMP_FOLDER,)).start()
    # except:
    #     print(traceback.format_exc())
    # try:
    #     threading.Thread(target=scrap.get_articles, args=()).start()
    # except:
    #     print(traceback.format_exc())
    scrap.get_articles()
    # api_handler.lisener(conf.TMP_FOLDER)
    app.run(host='0.0.0.0', port='8080')

