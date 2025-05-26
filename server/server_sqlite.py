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
DB_PATH = f'./db/{NAME}.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使返回结果可以像字典一样访问
    return conn

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
        if search_by != '':
            if len(search_by) == 42:  # 地址
                query = 'SELECT * FROM transactions WHERE relayer_address = ? OR EXISTS (SELECT 1 FROM authorizations WHERE tx_hash = transactions.tx_hash AND (authorizer_address = ? OR code_address = ?))'
                params = [search_by.lower(), search_by.lower(), search_by.lower()]
            elif len(search_by) == 66:  # 交易哈希
                query = 'SELECT * FROM transactions WHERE tx_hash = ?'
                params = [search_by]
            else:
                query = 'SELECT * FROM transactions WHERE 1=0'
                params = []
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
        
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'transactions': transactions
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
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000" AND (authorizer_address = ? or code_address = ?)'
                params = [search_by.lower(), search_by.lower()]
            else:
                query = 'SELECT * FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000" AND provider LIKE ?'
                params = [f'%{search_by}%']
        else:
            query = 'SELECT * FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000"'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers
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
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM authorizers WHERE authorizer_address = ? or code_address = ?'
                params = [search_by.lower(), search_by.lower()]
            else:
                query = 'SELECT * FROM authorizers WHERE provider LIKE ?'
                params = [f'%{search_by}%']
        else:
            query = 'SELECT * FROM authorizers'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers
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
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM codes WHERE code_address = ?'
                params = [search_by.lower()]
            else:
                query = 'SELECT * FROM codes WHERE provider LIKE ? or tags LIKE ?'
                params = [f'%{search_by}%', f'%{search_by}%']
        else:
            query = 'SELECT * FROM codes'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes
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
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM codes WHERE code_address = ?'
                params = [search_by.lower()]
            else:
                query = 'SELECT * FROM codes WHERE provider LIKE ? or tags LIKE ?'
                params = [f'%{search_by}%', f'%{search_by}%']
        else:
            query = 'SELECT * FROM codes'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes
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
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = ?'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
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
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = ?'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
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
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = ?'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
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
        
        # 返回结果
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
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
        
        # 获取基本统计信息
        cursor.execute('SELECT COUNT(*) as tx_count FROM transactions')
        tx_count = cursor.fetchone()['tx_count']
        
        cursor.execute('SELECT COUNT(*) as authorizer_count FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000"')
        authorizer_count = cursor.fetchone()['authorizer_count']
        
        cursor.execute('SELECT COUNT(*) as code_count FROM codes')
        code_count = cursor.fetchone()['code_count']
        
        cursor.execute('SELECT COUNT(*) as relayer_count FROM relayers')
        relayer_count = cursor.fetchone()['relayer_count']
        
        # 获取每日统计数据
        cursor.execute('SELECT * FROM daily_stats ORDER BY date')
        daily_stats = cursor.fetchall()
        
        daily_tx_count = {}
        daily_cumulative_tx_count = {}
        daily_authorization_count = {}
        daily_cumulative_authorization_count = {}
        daily_code_count = {}
        daily_relayer_count = {}
        
        for row in daily_stats:
            date = row['date']
            daily_tx_count[date] = row['tx_count']
            daily_cumulative_tx_count[date] = row['cumulative_transaction_count']
            daily_authorization_count[date] = row['authorization_count']
            daily_cumulative_authorization_count[date] = row['cumulative_authorization_count']
            daily_code_count[date] = row['code_count']
            daily_relayer_count[date] = row['relayer_count']
        
        # 获取top10数据
        cursor.execute('SELECT * FROM codes ORDER BY authorizer_count DESC LIMIT 10')
        top10_codes_rows = cursor.fetchall()
        top10_codes = []
        for row in top10_codes_rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            top10_codes.append(code)
        
        cursor.execute('SELECT * FROM relayers ORDER BY tx_count DESC LIMIT 10')
        top10_relayers = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000" ORDER BY tvl_balance DESC LIMIT 10')
        top10_authorizers_rows = cursor.fetchall()
        top10_authorizers = []
        for row in top10_authorizers_rows:
            auth = dict(row)
            auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth['historical_code_address'] else []
            top10_authorizers.append(auth)
        
        overview = {
            'tx_count': tx_count,
            'authorizer_count': authorizer_count,
            'code_count': code_count,
            'relayer_count': relayer_count,
            'daily_tx_count': daily_tx_count,
            'daily_cumulative_tx_count': daily_cumulative_tx_count,
            'daily_authorizaion_count': daily_authorization_count,
            'daily_cumulative_authorizaion_count': daily_cumulative_authorization_count,
            'daily_code_count': daily_code_count,
            'daily_relayer_count': daily_relayer_count,
            'top10_codes': top10_codes,
            'top10_relayers': top10_relayers,
            'top10_authorizers': top10_authorizers,
        }
        
        conn.close()
        
        return jsonify({
            'overview': overview
        })
    except Exception as e:
        app.logger.error(f"获取overview数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 开发环境使用
    app.run(host='0.0.0.0', port=3000, debug=False)
else:
    # 生产环境入口点
    # 使用Gunicorn或uWSGI运行时，这里是WSGI入口点
    app.logger.info(f"{NAME}应用已启动，准备接受请求") 