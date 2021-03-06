from bson.json_util import dumps, RELAXED_JSON_OPTIONS
import logging
from apscheduler.schedulers.background import BackgroundScheduler

import api.rssParser as rssParser
import api.db as db
import api.logger as apiLogger
logger = apiLogger.getLogger(__name__)

from flask import Flask

# Scheduler
# --------------------
def rssScheduler(file):
    rssParser.processRSSCsv(file)

def initScheduler(file):
    scheduler = BackgroundScheduler()
    scheduler.add_job(rssScheduler, 'interval', minutes=30, id='scheduler_bg_rss_parser', args=[file])
    scheduler.start()

# app
# --------------------

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('flask.cfg')
    db.initDb(app)
    initScheduler(app.config['INPUT_RSS_FILE_PATH'])
    return app

app = create_app()

import api.repo as repo

# Decorators
# --------------------
from functools import wraps
from flask import request, abort
def validate_apikey(func):
    @wraps(func)
    def decoratedFunc(*args, **kwargs):
        if (app.config['ADMIN_KEY'] == request.headers.get('api-key') 
        or app.config['ADMIN_KEY'] == request.args.get('api-key')):
            return(func(*args, **kwargs))
        else:
            abort(401)
    return decoratedFunc

# Routes
# --------------------
@app.route("/")
@validate_apikey
def index():
    return "NEWS-MAKER v1.0.1"

@app.route("/post")
@validate_apikey
def getPost():
    limit = request.args.get('limit') or 20
    result = repo.find("Post", { 'title': 1, 'link': 1, 'text': 1 }, int(limit))
    return dumps(result, json_options=RELAXED_JSON_OPTIONS)

@app.route("/rss")
@validate_apikey
def rss():
    inputfile = app.config['INPUT_RSS_FILE_PATH']
    parsedData = rssParser.processRSSCsv(inputfile)
    result = {
        "result" : parsedData
    }
    return dumps(result)

@app.route('/stats')
@validate_apikey
def getStats():
    result = repo.getStats()
    return dumps(result)

# Main
# --------------------

if __name__ == '__main__':
    app.run(host='localhost', port=app.config['PORT'], debug=app.config['DEBUG'])