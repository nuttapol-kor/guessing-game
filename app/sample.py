from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
import os, json, redis

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=os.environ.get("REDIS_DB", 0))

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/setup')
def setup():
    dict_step = {1:'first', 2:'second', 3:'third', 4:'fourth'}
    if db.game.count_documents({}) > 1:
        return redirect(url_for('restart'))
    doc1 = db.game.find_one({"stage": 1})
    step1 = None
    right_answer = None
    if doc1 is not None:
        step1 = doc1['step']
        right_answer = ' '.join(map(str,doc1['rightAns']))
    return render_template('setup.html', step1=step1, right_answer=right_answer, step_show=dict_step.get(step1))

@application.route('/update_setup', methods=['POST'])
def update_setup():
    user_choice = request.form.get('questioning')
    updated_content = {"$set": {'rightAns.$': user_choice},"$inc": {'step': 1}}
    db.game.update_one({'stage': 1, 'rightAns': '_'}, updated_content)
    return redirect(url_for('setup'))

@application.route('/insert_setup', methods=['GET','POST'])
def insert_setup():
    insert_content = {
            'stage': 1,
            'rightAns': ["_","_","_","_"],
            'count': 0,
            'userAns': [],
            'isWinning': False,
            'step': 1
        }
    db.game.insert_one(insert_content)
    return redirect(url_for('setup'))

@application.route('/gameplay')
def gameplay():
    dict_step = {5:'first', 6:'second', 7:'third', 8:'fourth'}
    doc1 = db.game.find_one({"stage": 1})
    right_answer = doc1['rightAns']
    hinting = '* '*len(right_answer)
    step1 = doc1['step']
    right_answer = ' '.join(map(str,doc1['rightAns']))
    count = doc1['count']
    user_ans = ' '.join(map(str,doc1['userAns']))
    if len(right_answer) == 0:
        return render_template('winning.html', count=count, user_ans=user_ans)
    return render_template('gameplay.html', step1=dict_step.get(step1), right_answer=right_answer, count=count, user_ans=user_ans, hinting=hinting)

@application.route('/update_gameplay', methods=['GET','POST'])
def update_gameplay():
    doc1 = db.game.find_one({"stage": 1})
    right_answer = doc1['rightAns']
    if len(right_answer) > 0:
            first_element = right_answer[0]
            user_choice = request.form.get('answering')
            if first_element == user_choice:
                updated_content = {
                    "$push": {"userAns": user_choice},
                    "$pop": {"rightAns": -1},
                    "$inc": {'step': 1}
                }
            else:
                updated_content = {
                    "$inc": {'count': 1}
                }
            db.game.update_one({'stage': 1}, updated_content)
    return redirect(url_for('gameplay'))

@application.route('/restart', methods=['GET','DELETE'])
def restart():
    doc1 = db.game.find_one({"stage": 1})
    if doc1 is not None:
        x = db.game.delete_many(doc1)
    return redirect(url_for('index'))
    

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)