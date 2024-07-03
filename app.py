# -*- coding: utf-8 -*-
# other imports and code here
import os
import time
import logging
from flask import Flask, session, abort, flash, request, render_template, redirect, url_for, current_app, jsonify, \
    send_from_directory
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from config import Config
from models import User
from forms import LoginForm, RegisterForm
from getpubmedinfo import PubmedSearch
from extensions import db, Cache

# from tmp import delete

# 配置日志格式和级别
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# 创建 Flask 应用实例
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)  # Initialize SQLAlchemy with the Flask app here
cache = Cache()

# delete.delete_db() # 删除数据库和清理缓存

with app.app_context():
    db.create_all()
    db.session.commit()
    logging.info('Database tables created.')

pms = PubmedSearch()

# 初始化 Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    with current_app.app_context():
        return db.session.get(User, int(user_id))


def get_elements_in_list1_not_in_list2(list1: list, list2: list) -> list:
    set_list1 = set(list1)
    set_list2 = set(list2)
    result = set_list1 - set_list2
    return [value for value in result if value]


def set_cache_list_append(user_id, key, list_data):
    db_data = cache.get_cache(user_id, key) or []
    if db_data is None:
        db_data = []
    list_return = set(db_data) | set(list_data)
    cache.set_cache(user_id, key, list(list_return))


def set_cache_list_append_public(key, list_data):
    db_data = cache.get_public_cache(key) or []
    if db_data is None:
        db_data = []
    list_return = set(db_data) | set(list_data)
    cache.set_public_cache(key, list(list_return))


def set_cache_list_append_dict(user_id, key, dict_data=None):
    db_data = cache.get_cache(user_id, key) or []
    update_db_data = db_data + [dict_data]
    cache.set_cache(user_id, key, update_db_data)


# 设置缓存头
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 1 year.
    """
    response.headers["Cache-Control"] = "public, max-age=31536000"
    return response


# 如果需要，定义静态文件路由
@app.route('/static/<path:filename>')
def staticfiles(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


# 首页路由
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    user_id = current_user.id
    search_history = cache.get_cache(user_id, "search_history") or []
    total_results_list = [history for history in search_history]

    if request.method == 'POST':
        # 获取表单数据
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        max_results = request.form.get('max_results')

        # 验证和处理 start_date 和 end_date
        if not start_date:  # 如果 start_date 是 None 或空字符串
            start_date = None  # 或者你可以设置为某个默认值，例如 'default_start_date'

        if not end_date:  # 如果 end_date 是 None 或空字符串
            end_date = None  # 或者你可以设置为某个默认值，例如 'default_end_date'

        # 验证和处理 max_results
        if max_results is None:
            max_results = 10  # 设置默认值
        else:
            max_results = int(max_results)  # 转换为整数

        search_query = request.form.get('search_query')
        session['start_date'] = start_date
        session['end_date'] = end_date
        session['max_results'] = max_results
        session['search_query'] = search_query
        return redirect(url_for('search_results'))
    else:
        return render_template('history.html',
                               start_date=session.get('start_date'),
                               end_date=session.get('end_date'),
                               max_results=session.get('max_results'),
                               search_query=session.get('search_query'),
                               results=total_results_list,
                               title="Search History",
                               search_counts_all=cache.get_public_cache("search_results_counts") or int(),
                               username=current_user.username)


# 搜索结果路由
@app.route('/search_results', methods=['GET', 'POST'])
@login_required
def search_results():
    user_id = current_user.id
    start_time = time.time()
    if request.method == 'POST':
        query = request.form.get('query')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        max_results = int(request.form.get('max_results'))
        search_pubmed_ids_list = pms.search_pubmed_ids(query, start_date=start_date, end_date=end_date,
                                                       retmax=max_results)

        search_counts_all = cache.get_public_cache("search_results_counts") or ""
        # Check if search_counts_all is empty and set it to 0 if it is
        if not search_counts_all:
            search_counts_all = 0
        else:
            search_counts_all = int(search_counts_all.replace(",", ""))
        search_counts_all += len(search_pubmed_ids_list)
        search_counts_all = f"{search_counts_all:,}"

        cache.set_public_cache("search_results_counts", search_counts_all)  # 保存搜索结果数量

        search_history = {"search_start_date": start_date,
                          "search_end_date": end_date,
                          "search_max_results": max_results,
                          "search_query": query,
                          "search_pubmed_ids": search_pubmed_ids_list,
                          "search_time": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
                          }
        set_cache_list_append_dict(user_id, "search_history", search_history)  # 保存搜索历史
        cache.set_cache(user_id, "search_results_by_pubmed_ids", search_pubmed_ids_list)  #

        # 检查公共缓存中是否存在搜索结果, 如果不存在则从pubmed 数据库获取
        _, search_pubmed_ids_list_not_in_db = cache.check_keys(-1, search_pubmed_ids_list)
        if search_pubmed_ids_list_not_in_db:
            search_pubmed_ids_list_not_in_db_details = pms.get_pubmed_ids_info(list(search_pubmed_ids_list_not_in_db))
            # 将没有在数据库里的search 结果用pubmed_id 为键保存到公共缓存下
            _ = [cache.set_public_cache(index, result) for index, result in
                 search_pubmed_ids_list_not_in_db_details.items()]

        end_time = time.time()
        logging.info(f"Execution time of search_results: {end_time - start_time} seconds")
    return display_pubmed_ids_user(user_id, 'search_results_by_pubmed_ids', "Search Results")


def check_pubmed_ids_user(user_id, pubmed_ids, cache_key, state_key):
    user_name = current_user.username
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    pubmed_id_check_state_user = cache.get_cache(user_id, "search_results_by_pubmed_ids_state_user") or {}

    set_cache_list_append(user_id, cache_key, pubmed_ids)
    for pubmed_id in pubmed_ids:
        state = pubmed_id_check_state_user.setdefault(pubmed_id, {}).setdefault(state_key, {})
        if not state:
            state["user_name"] = user_name
            state["time"] = now_time

    cache.set_cache(user_id, "search_results_by_pubmed_ids_state_user", pubmed_id_check_state_user)
    
    return {"status": "success", f"{cache_key}": pubmed_ids}


@app.route('/favorite_check', methods=['POST'])
@login_required
def favorite_check():
    user_id = current_user.id
    data = request.get_json()
    favorite_pubmed_ids = data.get('favorite_pubmed_id')
    result = check_pubmed_ids_user(user_id, favorite_pubmed_ids, 'favorite_pubmed_id', 'favorites')
    return jsonify(result)



@app.route('/read_check', methods=['POST'])
@login_required
def read_check():
    user_id = current_user.id
    data = request.get_json()
    read_pubmed_ids = data.get('read_pubmed_id')
    result = check_pubmed_ids_user(user_id, read_pubmed_ids, 'read_pubmed_ids', 'read')
    return jsonify(result)


def check_pubmed_ids_public(pubmed_ids, cache_key, state_key):
    user_name = current_user.username
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    pubmed_id_check_state_public = cache.get_public_cache("search_results_by_pubmed_ids_state_public") or {}

    set_cache_list_append_public(cache_key, pubmed_ids)
    for pubmed_id in pubmed_ids:
        state = pubmed_id_check_state_public.setdefault(pubmed_id, {}).setdefault(state_key, {})
        if not state:
            state["user_name"] = user_name
            state["time"] = now_time

    cache.set_public_cache("search_results_by_pubmed_ids_state_public", pubmed_id_check_state_public)
    
    return {"status": "success", f"{cache_key}": pubmed_ids}


@app.route('/loved_check', methods=['POST'])
@login_required
def loved_check():
    data = request.get_json()
    loved_pubmed_ids = data.get('loved_pubmed_id')
    result = check_pubmed_ids_public(loved_pubmed_ids, 'loved_pubmed_id', 'loved')
    return jsonify(result)


@app.route('/shared_check', methods=['POST'])
@login_required
def shared_check():
    data = request.get_json()
    shared_pubmed_ids = data.get('shared_pubmed_id')
    result = check_pubmed_ids_public(shared_pubmed_ids, 'shared_pubmed_id', 'shared')
    return jsonify(result)


def cancel_pubmed_results_user(user_id, cancel_pubmed_ids, cache_key, state_key):
    pubmed_id_check_state_user = cache.get_cache(user_id, "search_results_by_pubmed_ids_state_user") or {}

    # Remove the PubMed IDs from the specified list in the cache
    current_pubmed_ids = cache.get_cache(user_id, cache_key) or []
    updated_pubmed_ids = get_elements_in_list1_not_in_list2(current_pubmed_ids, cancel_pubmed_ids)
    cache.set_cache(user_id, cache_key, updated_pubmed_ids)

    # Update pubmed_id_check_state_user to reflect the cancellation
    for pubmed_id in cancel_pubmed_ids:
        if pubmed_id in pubmed_id_check_state_user:
            if state_key in pubmed_id_check_state_user[pubmed_id]:
                del pubmed_id_check_state_user[pubmed_id][state_key]
                # If the dictionary for the pubmed_id is empty after deletion, remove the pubmed_id key itself
                if not pubmed_id_check_state_user[pubmed_id]:
                    del pubmed_id_check_state_user[pubmed_id]

    cache.set_cache(user_id, "search_results_by_pubmed_ids_state_user", pubmed_id_check_state_user)
    
    return {"status": "success", "cancel_pubmed_ids": cancel_pubmed_ids}


@app.route('/cancel_favorite_results', methods=['POST'])
@login_required
def cancel_favorite_results():
    user_id = current_user.id
    data = request.get_json()
    cancel_pubmed_ids = data.get('cancel_pubmed_id')
    result = cancel_pubmed_results_user(user_id, cancel_pubmed_ids, 'favorite_pubmed_id', 'favorites')
    return jsonify(result)


@app.route('/cancel_read_results', methods=['POST'])
@login_required
def cancel_read_results():
    user_id = current_user.id
    data = request.get_json()
    cancel_pubmed_ids = data.get('cancel_pubmed_id')
    result = cancel_pubmed_results_user(user_id, cancel_pubmed_ids, 'read_pubmed_ids', 'read')
    return jsonify(result)


def cancel_pubmed_results_public(cancel_pubmed_ids, cache_key, state_key):
    username = current_user.username
    current_pubmed_ids = cache.get_public_cache(cache_key) or []

    not_authorized_list = []
    pubmed_id_check_state_user = cache.get_public_cache("search_results_by_pubmed_ids_state_public") or {}
    for pubmed_id in cancel_pubmed_ids:
        if pubmed_id in pubmed_id_check_state_user:
            if state_key in pubmed_id_check_state_user[pubmed_id]:
                if pubmed_id_check_state_user[pubmed_id][state_key]["user_name"] == username:
                    del pubmed_id_check_state_user[pubmed_id][state_key]
                else:
                    not_authorized_list.append(pubmed_id)
    delete_not_authorized_list = get_elements_in_list1_not_in_list2(cancel_pubmed_ids, not_authorized_list)
    update_pubmed_ids = get_elements_in_list1_not_in_list2(current_pubmed_ids, delete_not_authorized_list)

    cache.set_public_cache(cache_key, update_pubmed_ids)
    cache.set_public_cache("search_results_by_pubmed_ids_state_public", pubmed_id_check_state_user)
    
    return {"status": "success", "cancel_pubmed_ids": cancel_pubmed_ids,
            "not_authorized_list": not_authorized_list if not_authorized_list else None}


@app.route('/cancel_loved_results', methods=['POST'])
@login_required
def cancel_loved_results():
    data = request.get_json()
    cancel_pubmed_ids = data.get('cancel_pubmed_id')
    result = cancel_pubmed_results_public(cancel_pubmed_ids, 'loved_pubmed_id', 'loved')
    return jsonify(result)


@app.route('/cancel_shared_results', methods=['POST'])
@login_required
def cancel_shared_results():
    data = request.get_json()
    cancel_pubmed_ids = data.get('cancel_pubmed_id')
    result = cancel_pubmed_results_public(cancel_pubmed_ids, 'shared_pubmed_id', 'shared')
    return jsonify(result)


# 显示收藏结果路由
def display_pubmed_ids_user(user_id, cache_key, title):
    pubmed_ids = cache.get_cache(user_id, cache_key) or []
    pubmed_ids_render_list = [cache.get_public_cache(pubmed_id) for pubmed_id in pubmed_ids if
                              cache.get_public_cache(pubmed_id)]
    
    return render_template('home.html',
                           pubmed_id_check_state_user=update_pubmed_ids_state(user_id, pubmed_ids),
                           results=pubmed_ids_render_list,
                           username=current_user.username,
                           search_counts_all=cache.get_public_cache("search_results_counts") or int(),
                           title=title)


@app.route('/display_favorites_pubmed_id', methods=['GET'])
@login_required
def display_favorites_pubmed_id():
    user_id = current_user.id
    return display_pubmed_ids_user(user_id, 'favorite_pubmed_id', "Collect Results")


@app.route('/display_read_pubmed_id', methods=['GET'])
@login_required
def display_read_pubmed_id():
    user_id = current_user.id
    return display_pubmed_ids_user(user_id, 'read_pubmed_ids', "Read Results")


def update_pubmed_ids_state(user_id, pubmed_ids=None):
    # 获取公共缓存和用户缓存中的数据

    pubmed_id_check_state_user = cache.get_cache(user_id, "search_results_by_pubmed_ids_state_user") or {}
    pubmed_id_check_state_public = cache.get_public_cache("search_results_by_pubmed_ids_state_public") or {}

    # 遍历公共缓存中的每个 pubmed_id
    for pubmed_id, public_states in pubmed_id_check_state_public.items():
        if pubmed_id in pubmed_id_check_state_user:
            user_states = pubmed_id_check_state_user[pubmed_id]

            # 合并 state_key 键内的字典
            for state_key, public_state in public_states.items():
                if state_key in user_states:
                    user_state = user_states[state_key]
                    # 合并字典
                    merged_state = {**public_state, **user_state}
                    pubmed_id_check_state_user[pubmed_id][state_key] = merged_state
                else:
                    pubmed_id_check_state_user[pubmed_id][state_key] = public_state
        else:
            pubmed_id_check_state_user[pubmed_id] = public_states

    return {pubmed_id_checked: dict_value for pubmed_id_checked, dict_value in pubmed_id_check_state_user.items() if
            pubmed_id_checked in pubmed_ids}


def display_pubmed_ids_public(user_id, cache_key, title):
    pubmed_ids = cache.get_public_cache(cache_key) or []
    pubmed_ids_render_list = [cache.get_public_cache(pubmed_id) for pubmed_id in pubmed_ids if
                              cache.get_public_cache(pubmed_id)]
    
    return render_template('home.html',
                           pubmed_id_check_state_user=update_pubmed_ids_state(user_id, pubmed_ids),
                           results=pubmed_ids_render_list,
                           username=current_user.username,
                           search_counts_all=cache.get_public_cache("search_results_counts") or int(),
                           title=title)


@app.route('/display_loved_pubmed_id', methods=['GET'])
@login_required
def display_loved_pubmed_id():
    user_id = current_user.id
    return display_pubmed_ids_public(user_id, 'loved_pubmed_id', "Loved Results")


@app.route('/display_shared_pubmed_id', methods=['GET'])
@login_required
def display_shared_pubmed_id():
    user_id = current_user.id
    return display_pubmed_ids_public(user_id, 'shared_pubmed_id', "Shared Results")


@app.route('/cancel_search_history', methods=['POST'])
@login_required
def cancel_search_history():
    user_id = current_user.id
    data = request.get_json()
    cancelled_search_history = data.get('cancel_pubmed_id')
    current_search_history = cache.get_cache(user_id, 'search_history') or []
    updated_search_results = [search_history for search_history in current_search_history if
                              search_history.get(
                                  'search_time') not in cancelled_search_history]
    cache.set_cache(user_id, 'search_history', updated_search_results)
    return jsonify({"status": "success"})


@app.route('/display_search_history', methods=['GET', 'POST'])
@login_required
def display_search_history():
    user_id = current_user.id

    if request.method == 'POST':
        data = request.get_json()
        search_history_pubmed_ids = data.get('search_history_pubmed_ids')
        cache.set_cache(user_id, "search_history_pubmed_ids", search_history_pubmed_ids)
        return jsonify(success=True)  #
    else:
        return display_pubmed_ids_user(user_id, 'search_history_pubmed_ids', "Search History")


# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=remember_me)
        return redirect(url_for('home'))

    return render_template('login.html', form=form)


# 登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# 应用入口
if __name__ == '__main__':
    app.run(debug=True)
