import os
import json
from flask_cors import CORS
from flask import Flask, request, jsonify
import traceback

import api_handler
import conf
import utils

app = Flask(__name__)
CORS(app)


@app.route('/init', methods=['GET', 'POST'])
def init():
    try:
        api_handler.db.init_db()
        return utils.create_res_obj({'status': 'init success'})
    except Exception as e:
        return utils.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        res_data = api_handler.res_query(query)
        res_data = jsonify(res_data)
        return res_data


@app.route('/delete/<filename>', methods=['GET', 'POST'])
def delete(filename):
    try:
        x = api_handler.delete_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return utils.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/hide/<filename>', methods=['GET', 'POST'])
def hide(filename):
    try:
        x = api_handler.hide_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return utils.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/restore/<filename>', methods=['GET', 'POST'])
def restore(filename):
    try:
        x = api_handler.restore_doc(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return utils.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route('/getfile/<filename>', methods=['GET', 'POST'])
def getfile(filename):
    try:
        x = api_handler.getfile(filename)
        x = jsonify(x)
        return x
    except Exception as e:
        return utils.create_res_obj(
            {'traceback': traceback.format_exc(), 'msg': "{}".format(e.args)},
            success=False)


@app.route("/showall", methods=['POST'])
def showall():
    if request.method == 'POST':
        return jsonify(api_handler.get_all_docs())


def run():
    app.run(host=conf.HOST, port=conf.PORT)
