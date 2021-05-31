from flask import Flask, render_template, jsonify, request
import jwt

import datetime

import hashlib
import requests

app = Flask(__name__)

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.dbsparta_matjp

SECRET_KEY = 'SPARTA'


@app.route('/')
def main():
    return render_template("main.html")


@app.route('/input')
def input():
    return render_template("input.html")


@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/card', methods=['GET'])
def show_card():
    mymatjip = list(db.mymatjip.find({}, {'_id': False}))
    return jsonify({'all_mymatjip': mymatjip})


@app.route('/mymatjip', methods=['POST'])
def save_mymatjip():
    title_receive = request.form['title_give']
    menu_receive = request.form['menu_give']
    address_receive = request.form['address_give']
    desc_receive = request.form['desc_give']

    doc = {
        'title': title_receive,
        'menu': menu_receive,
        'address': address_receive,
        'desc': desc_receive,
    }

    db.mymatjip.insert_one(doc)
    return jsonify({'msg': '저장완료!'})
    print(title, menu, address, desc)


@app.route('/load', methods=['POST'])
def load():
    matjips = list(db.mymatjip.find({}))

    result = []
    for matjip in matjips:
        id = matjip['_id']
        menu = matjip['menu']
        address = matjip['address']
        title = matjip['title']
        desc = matjip['desc']
        x = matjip.get('x')
        y = matjip.get('y')

        if not x or not y:
            headers = {
                "X-NCP-APIGW-API-KEY-ID": "j7f8jzk31x",
                "X-NCP-APIGW-API-KEY": "nhgCLRcE0YE0V9OvlIvCpe0vYr9nmTEv1G9c2X1k"
            }
            r = requests.get(f"https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}",
                             headers=headers)
            response = r.json()
            if response["status"] == "OK":
                if len(response["addresses"]) > 0:
                    x = float(response["addresses"][0]["x"])
                    y = float(response["addresses"][0]["y"])
                    print(x, y)
                    db.mymatjip.update_one({'_id': id}, {'$set': {'x': x, 'y': y}})

        if not x or not y:
            continue
        doc = {
            'title': title,
            'address': address,
            'desc': desc,
            'menu': menu,
            'mapx': x,
            'mapy': y,
        }
        result.append(doc)
    return jsonify({'matjips': result})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
