from typing import Optional, Any, List, Tuple
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Cache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(128), nullable=False)
    value = db.Column(db.PickleType, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    @staticmethod
    def get_cache(user_id, key):
        cache_entry = Cache.query.filter_by(user_id=user_id, key=key).first()
        if cache_entry:
            return cache_entry.value
        return None

    @staticmethod
    def set_cache(user_id, key, value):
        cache_entry = Cache.query.filter_by(user_id=user_id, key=key).first()
        if cache_entry:
            cache_entry.value = value
            cache_entry.timestamp = db.func.current_timestamp()
        else:
            cache_entry = Cache(user_id=user_id, key=key, value=value)
            db.session.add(cache_entry)
        db.session.commit()

    @staticmethod
    def delete_cache(user_id, key):
        Cache.query.filter_by(user_id=user_id, key=key).delete()
        db.session.commit()

    @staticmethod
    def get_public_cache(key: str) -> Optional[Any]:
        return Cache.get_cache(user_id=-1, key=key)

    @staticmethod
    def set_public_cache(key: str, value: Any) -> None:
        Cache.set_cache(user_id=-1, key=key, value=value)

    @staticmethod
    def delete_public_cache(key: str) -> None:
        Cache.delete_cache(user_id=-1, key=key)

    @staticmethod
    def key_exists(user_id: int, key: str) -> bool:
        return Cache.get_cache(user_id, key) is not None

    @staticmethod
    def check_keys(user_id: int, keys: List[str]) -> Tuple[List[str], List[str]]:
        keys_in_db = []
        keys_not_in_db = []
        for key in keys:
            if Cache.key_exists(user_id, key):
                keys_in_db.append(key)
            else:
                keys_not_in_db.append(key)
        return keys_in_db, keys_not_in_db
