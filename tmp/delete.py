import os
import time
import logging
from flask import Flask
from sqlalchemy import create_engine
from redis import Redis

from config import Config
from extensions import db, Cache

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
cache = Cache()


def clear_redis_cache():
    redis_client = Redis(host=app.config['CACHE_REDIS_HOST'], port=app.config['CACHE_REDIS_PORT'],
                         db=app.config['CACHE_REDIS_DB'])
    redis_client.flushall()
    logging.info('Redis cache cleared')


def clear_flask_cache():
    cache_entries = Cache.query.all()
    for entry in cache_entries:
        db.session.delete(entry)
    db.session.commit()
    logging.info('Flask cache cleared')


def remove_db_file():
    db_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tmp', 'test.db')
    if os.path.exists(db_file_path):
        try:
            os.remove(db_file_path)
            logging.info(f'Database file {db_file_path} removed')
        except PermissionError:
            logging.error(f'File {db_file_path} is still in use, retrying...')
            time.sleep(1)
            os.remove(db_file_path)


def delete_db():
    with app.app_context():
        db.drop_all()
        db.session.commit()
        db.session.remove()

        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        engine.dispose()

        remove_db_file()

        if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI']):
            logging.info('Database file deleted successfully')

        db.create_all()
        db.session.commit()

        clear_redis_cache()
        clear_flask_cache()

        logging.info('Database tables and caches dropped and recreated')

delete_db()