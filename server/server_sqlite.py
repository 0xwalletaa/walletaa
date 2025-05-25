import util
from flask import Flask, request, jsonify
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_cors import CORS
import random
import json
import sqlite3

NAME = os.environ.get("NAME")

util.NAME = NAME

# 配置日志
log_dir = f"logs_{NAME}"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "server.log")

# 创建日志处理器
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# 配置Flask应用日志
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 添加CORS支持，允许所有域名访问
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# 数据库路径
DB_PATH = f'/dev/shm/{NAME}_info.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使返回结果可以像字典一样访问
    return conn

def get_last_update_time():
    """获取最后更新时间"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp FROM last_update_time ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result['timestamp'] if result else 0
    except Exception as e:
        app.logger.error(f"获取更新时间失败: {str(e)}")
        return 0

def build_transaction_search_query(search_by):
    """构建交易搜索查询"""
    if len(search_by) == 42:  # 地址
        return '''
        SELECT t.* FROM transactions t 
        WHERE t.relayer_address = ? 
        OR EXISTS (
            SELECT 1 FROM authorizations a 
            WHERE a.tx_hash = t.tx_hash 
            AND (a.authorizer_address = ? OR a.code_address = ?)
        )
        ''', [search_by, search_by, search_by]
    elif len(search_by) == 66:  # 交易哈希
        return 'SELECT * FROM transactions WHERE tx_hash = ?', [search_by]
    else:
        return 'SELECT * FROM transactions WHERE 1=0', []

def build_authorizer_search_query(search_by, include_zero=False):
    """构建授权者搜索查询"""
    table_name = 'authorizers_with_zero' if include_zero else 'authorizers'
    base_query = f'SELECT * FROM {table_name}'
    conditions = []
    params = []
    
    if search_by:
        if len(search_by) == 42:  # 地址
            conditions.append('(authorizer_address = ? OR code_address = ?)')
            params.extend([search_by, search_by])
        else:  # 提供者名称
            conditions.append('provider LIKE ?')
            params.append(f'%{search_by}%')
    
    if conditions:
        base_query += ' WHERE ' + ' AND '.join(conditions)
    
    return base_query, params

def build_code_search_query(search_by):
    """构建代码搜索查询"""
    base_query = 'SELECT * FROM codes'
    
    if search_by:
        if len(search_by) == 42:  # 地址
            return base_query + ' WHERE code_address = ?', [search_by]
        else:  # 提供者名称或标签
            return base_query + ' WHERE provider LIKE ? OR tags LIKE ?', [f'%{search_by}%', f'%{search_by}%']
    
    return base_query, []

def build_relayer_search_query(search_by):
    """构建中继者搜索查询"""
    base_query = 'SELECT * FROM relayers'
    
    if search_by and len(search_by) == 42:  # 地址
        return base_query + ' WHERE relayer_address = ?', [search_by]
    
    return base_query, []

# 分页查询接口
@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        if search_by:
            query, params = build_transaction_search_query(search_by)
        else:
            query = 'SELECT * FROM transactions'
            params = []
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY timestamp ASC'
        else:
            query += ' ORDER BY timestamp DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典并解析JSON字段
        transactions = []
        for row in rows:
            tx = dict(row)
            tx['authorization_list'] = json.loads(tx['authorization_list'])
            transactions.append(tx)
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'transactions': transactions,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取交易数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizers分页查询接口
@app.route('/authorizers', methods=['GET'])
def get_authorizers():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_authorizer_search_query(search_by, include_zero=False)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY tvl_balance ASC'
        else:
            query += ' ORDER BY tvl_balance DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典并解析JSON字段
        authorizers = []
        for row in rows:
            auth = dict(row)
            auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth['historical_code_address'] else []
            authorizers.append(auth)
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取授权者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizers_with_zero分页查询接口
@app.route('/authorizers_with_zero', methods=['GET'])
def get_authorizers_with_zero():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_authorizer_search_query(search_by, include_zero=True)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY tvl_balance ASC'
        else:
            query += ' ORDER BY tvl_balance DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典并解析JSON字段
        authorizers = []
        for row in rows:
            auth = dict(row)
            auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth['historical_code_address'] else []
            authorizers.append(auth)
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取带零授权者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# codes_by_tvl_balance分页查询接口
@app.route('/codes_by_tvl_balance', methods=['GET'])
def get_codes_by_tvl_balance():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_code_search_query(search_by)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY tvl_balance ASC'
        else:
            query += ' ORDER BY tvl_balance DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典并解析JSON字段
        codes = []
        for row in rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            codes.append(code)
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以TVL余额排序的代码数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# codes_by_authorizer_count分页查询接口
@app.route('/codes_by_authorizer_count', methods=['GET'])
def get_codes_by_authorizer_count():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_code_search_query(search_by)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY authorizer_count ASC'
        else:
            query += ' ORDER BY authorizer_count DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典并解析JSON字段
        codes = []
        for row in rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            codes.append(code)
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以授权者数量排序的代码数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_tx_count分页查询接口
@app.route('/relayers_by_tx_count', methods=['GET'])
def get_relayers_by_tx_count():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_relayer_search_query(search_by)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY tx_count ASC'
        else:
            query += ' ORDER BY tx_count DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以交易数量排序的中继者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_authorization_count分页查询接口
@app.route('/relayers_by_authorization_count', methods=['GET'])
def get_relayers_by_authorization_count():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_relayer_search_query(search_by)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY authorization_count ASC'
        else:
            query += ' ORDER BY authorization_count DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以授权数量排序的中继者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_authorization_fee分页查询接口
@app.route('/relayers_by_authorization_fee', methods=['GET'])
def get_relayers_by_authorization_fee():
    try:
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # 获取排序参数，默认为倒序
        search_by = request.args.get('search_by', '')  # 获取过滤search_by参数
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query, params = build_relayer_search_query(search_by)
        
        # 添加排序
        if order.lower() == 'asc':
            query += ' ORDER BY authorization_fee ASC'
        else:
            query += ' ORDER BY authorization_fee DESC'
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 添加分页
        query += ' LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以授权费用排序的中继者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# overview查询接口
@app.route('/overview', methods=['GET'])
def get_overview():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取overview数据
        cursor.execute('SELECT key, value FROM overview')
        rows = cursor.fetchall()
        
        overview = {}
        for row in rows:
            overview[row['key']] = json.loads(row['value'])
        
        conn.close()
        
        last_update_time = get_last_update_time()
        
        return jsonify({
            'overview': overview,
            'last_update_time': last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取overview数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    last_update_time = get_last_update_time()
    return jsonify({'status': 'ok', 'last_update_time': last_update_time})

if __name__ == '__main__':
    # 开发环境使用
    app.run(host='0.0.0.0', port=3001, debug=False)
else:
    # 生产环境入口点
    # 使用Gunicorn或uWSGI运行时，这里是WSGI入口点
    app.logger.info(f"{NAME}应用已启动，准备接受请求") 