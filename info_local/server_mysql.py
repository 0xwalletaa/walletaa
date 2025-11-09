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
import pymysql
from pymysql.cursors import DictCursor
import glob

# 从环境变量读取允许的链名称列表
ALLOWED_NAMES_STR = os.environ.get("ALLOWED_NAMES", "mainnet")
ALLOWED_NAMES = set(name.strip() for name in ALLOWED_NAMES_STR.split(','))

NAME = "multi"  # 服务名称用于日志目录
util.NAME = NAME

# Configure logging
log_dir = f"logs_{NAME}"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "server.log")

# Create log handler
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# Configure Flask application logging
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Add CORS support, allow all domains to access
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

def validate_chain_name(name):
    """验证链名称是否在允许的列表中"""
    if name not in ALLOWED_NAMES:
        return jsonify({
            'error': f'Chain name "{name}" is not supported',
            'allowed_names': list(ALLOWED_NAMES)
        }), 404
    return None

def get_db_connection(name):
    """Get MySQL database connection for specified chain"""
    mysql_db_name = f'walletaa_{name}'
    conn = pymysql.connect(
        host='localhost',
        user=mysql_db_name,
        password=mysql_db_name,
        database=mysql_db_name,
        charset='utf8mb4',
        cursorclass=DictCursor  # Make returned results accessible like a dictionary
    )
    return conn

# Pagination query interface
@app.route('/<name>/transactions', methods=['GET'])
def get_transactions(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42 or search_by == "error":  # address
                query = 'SELECT * FROM transactions WHERE relayer_address = %s OR tx_hash in (SELECT tx_hash FROM authorizations WHERE authorizer_address = %s OR code_address = %s)'
                params = [search_by.lower(), search_by.lower(), search_by.lower()]
            elif len(search_by) == 66:  # transaction hash
                query = 'SELECT * FROM transactions WHERE tx_hash = %s'
                params = [search_by]
            else:
                query = 'SELECT * FROM transactions WHERE 1=0'
                params = []
        else:
            query = 'SELECT * FROM transactions'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY timestamp ASC'
        else:
            query += ' ORDER BY timestamp DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary and parse JSON fields
        transactions = []
        for row in rows:
            tx = dict(row)
            tx['authorization_list'] = json.loads(tx['authorization_list'])
            transactions.append(tx)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'transactions': transactions
        })
    except Exception as e:
        app.logger.error(f"Error getting transaction data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizers pagination query interface
@app.route('/<name>/authorizers', methods=['GET'])
def get_authorizers(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        order_by = request.args.get('order_by', 'tvl_balance')
        
        if order_by not in set(['tvl_balance', 'historical_code_address_count']):
            order_by = 'tvl_balance'
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42 or search_by == "error":
                # 对于地址搜索，先过滤 authorizers 表，再 JOIN codes 表
                query = '''SELECT a.*, c.provider 
                          FROM (SELECT * FROM authorizers 
                                WHERE code_address != "0x0000000000000000000000000000000000000000" 
                                AND (authorizer_address = %s OR code_address = %s)) a 
                          LEFT JOIN codes c ON a.code_address = c.code_address'''
                params = [search_by.lower(), search_by.lower()]
            else:
                # 对于 provider 搜索，先过滤 codes 表，再过滤 authorizers 表，再 JOIN codes 表
                query = '''SELECT a.*, c.provider 
                          FROM (SELECT * FROM authorizers 
                                WHERE code_address != "0x0000000000000000000000000000000000000000" 
                                AND (code_address in (SELECT code_address FROM codes WHERE provider LIKE %s))) a 
                          LEFT JOIN codes c ON a.code_address = c.code_address'''
                params = [f'%{search_by}%']
        else:
            # 默认查询，先过滤 authorizers 表，再 JOIN codes 表
            query = '''SELECT a.*, c.provider 
                      FROM (SELECT * FROM authorizers 
                            WHERE code_address != "0x0000000000000000000000000000000000000000") a 
                      LEFT JOIN codes c ON a.code_address = c.code_address'''
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += f' ORDER BY a.{order_by} ASC'
        else:
            query += f' ORDER BY a.{order_by} DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary - in MySQL with DictCursor, rows are already dicts
        authorizers = []
        for row in rows:
            auth = dict(row)
            # MySQL doesn't have historical_code_address field in updater_mysql.py, skip this line
            # auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth.get('historical_code_address') else []
            authorizers.append(auth)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers
        })
    except Exception as e:
        app.logger.error(f"Error getting authorizer data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizers_with_zero pagination query interface
@app.route('/<name>/authorizers_with_zero', methods=['GET'])
def get_authorizers_with_zero(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        order_by = request.args.get('order_by', 'tvl_balance')
        
        if order_by not in set(['tvl_balance', 'historical_code_address_count']):
            order_by = 'tvl_balance'
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42 or search_by == "error":
                # 对于地址搜索，先过滤 authorizers 表，再 JOIN codes 表
                query = '''SELECT a.*, c.provider 
                          FROM (SELECT * FROM authorizers 
                                WHERE authorizer_address = %s OR code_address = %s) a 
                          LEFT JOIN codes c ON a.code_address = c.code_address'''
                params = [search_by.lower(), search_by.lower()]
            else:
                # 对于 provider 搜索，先过滤 codes 表，再过滤 authorizers 表，再 JOIN codes 表
                query = '''SELECT a.*, c.provider 
                          FROM (SELECT * FROM authorizers 
                                WHERE code_address in (SELECT code_address FROM codes WHERE provider LIKE %s)) a 
                          LEFT JOIN codes c ON a.code_address = c.code_address'''
                params = [f'%{search_by}%']
        else:
            # 默认查询，先过滤 authorizers 表，再 JOIN codes 表
            query = '''SELECT a.*, c.provider 
                      FROM (SELECT * FROM authorizers) a 
                      LEFT JOIN codes c ON a.code_address = c.code_address'''
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += f' ORDER BY a.{order_by} ASC'
        else:
            query += f' ORDER BY a.{order_by} DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        authorizers = []
        for row in rows:
            auth = dict(row)
            # MySQL doesn't have historical_code_address field in updater_mysql.py, skip this line
            # auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth.get('historical_code_address') else []
            authorizers.append(auth)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'authorizers': authorizers
        })
    except Exception as e:
        app.logger.error(f"Error getting authorizer data (including zero): {str(e)}")
        return jsonify({'error': str(e)}), 500

# code_statistics query interface
@app.route('/<name>/code_statistics', methods=['GET'])
def get_code_statistics(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    cached_code_statistics_path = f'/dev/shm/{name}_code_statistics.json'
    if os.path.exists(cached_code_statistics_path):
        code_statistics = json.loads(open(cached_code_statistics_path).read())
        return jsonify(code_statistics)
    else:
        return jsonify({'error': 'Code statistics not found'}), 404

# trace_statistics query interface
@app.route('/<name>/trace_statistics', methods=['GET'])
def get_trace_statistics(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    cached_trace_statistics_path = f'/dev/shm/{name}_trace_statistics.json'
    if os.path.exists(cached_trace_statistics_path):
        trace_statistics = json.loads(open(cached_trace_statistics_path).read())
        return jsonify(trace_statistics)
    else:
        return jsonify({'error': 'Trace statistics not found'}), 404

    
# codes_by_tvl_balance pagination query interface
@app.route('/<name>/codes_by_tvl_balance', methods=['GET'])
def get_codes_by_tvl_balance(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        tags_by = request.args.get('tags_by', '')  # Get filter tags_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM codes WHERE code_address = %s'
                params = [search_by.lower()]
            else:
                query = 'SELECT * FROM codes WHERE provider LIKE %s or tags LIKE %s'
                params = [f'%{search_by}%', f'%{search_by}%']
        elif tags_by != '':
            tags = tags_by.split(',')            
            tag_conditions = ' AND '.join(['tags LIKE %s' for _ in tags])
            query = f'SELECT * FROM codes WHERE {tag_conditions}'
            params = [f'%{tag}%' for tag in tags]
        else:
            query = 'SELECT * FROM codes'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY tvl_balance ASC'
        else:
            query += ' ORDER BY tvl_balance DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary and parse JSON fields
        codes = []
        for row in rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            code['type'] = code['details']['type'] if code['details'] and 'type' in code['details'] else ""
            codes.append(code)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes
        })
    except Exception as e:
        app.logger.error(f"Error getting codes by TVL balance: {str(e)}")
        return jsonify({'error': str(e)}), 500

# codes_by_authorizer_count pagination query interface
@app.route('/<name>/codes_by_authorizer_count', methods=['GET'])
def get_codes_by_authorizer_count(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        tags_by = request.args.get('tags_by', '')  # Get filter tags_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42:
                query = 'SELECT * FROM codes WHERE code_address = %s'
                params = [search_by.lower()]
            else:
                query = 'SELECT * FROM codes WHERE provider LIKE %s or tags LIKE %s'
                params = [f'%{search_by}%', f'%{search_by}%']
        elif tags_by != '':
            tags = tags_by.split(',')            
            tag_conditions = ' AND '.join(['tags LIKE %s' for _ in tags])
            query = f'SELECT * FROM codes WHERE {tag_conditions}'
            params = [f'%{tag}%' for tag in tags]
        else:
            query = 'SELECT * FROM codes'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY authorizer_count ASC'
        else:
            query += ' ORDER BY authorizer_count DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary and parse JSON fields
        codes = []
        for row in rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            code['type'] = code['details']['type'] if code['details'] and 'type' in code['details'] else ""

            codes.append(code)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'codes': codes
        })
    except Exception as e:
        app.logger.error(f"Error getting codes by authorizer count: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_tx_count pagination query interface
@app.route('/<name>/relayers_by_tx_count', methods=['GET'])
def get_relayers_by_tx_count(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = %s'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY tx_count ASC'
        else:
            query += ' ORDER BY tx_count DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
        })
    except Exception as e:
        app.logger.error(f"Error getting relayers by tx count: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_authorization_count pagination query interface
@app.route('/<name>/relayers_by_authorization_count', methods=['GET'])
def get_relayers_by_authorization_count(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = %s'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY authorization_count ASC'
        else:
            query += ' ORDER BY authorization_count DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
        })
    except Exception as e:
        app.logger.error(f"Error getting relayers by authorization count: {str(e)}")
        return jsonify({'error': str(e)}), 500

# relayers_by_authorization_fee pagination query interface
@app.route('/<name>/relayers_by_authorization_fee', methods=['GET'])
def get_relayers_by_authorization_fee(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            query = 'SELECT * FROM relayers WHERE relayer_address = %s'
            params = [search_by.lower()]
        else:
            query = 'SELECT * FROM relayers'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY authorization_fee ASC'
        else:
            query += ' ORDER BY authorization_fee DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        relayers = [dict(row) for row in rows]
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'relayers': relayers
        })
    except Exception as e:
        app.logger.error(f"Error getting relayers by authorization fee: {str(e)}")
        return jsonify({'error': str(e)}), 500

# overview query interface
@app.route('/<name>/overview', methods=['GET'])
def get_overview(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    cached_overview_path = f'/dev/shm/{name}_overview.json'
    if os.path.exists(cached_overview_path):
        overview = json.loads(open(cached_overview_path).read())
        return jsonify({
            'overview': overview
        })

    try:
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Get basic statistical information
        cursor.execute('SELECT COUNT(*) as tx_count FROM transactions')
        tx_count = cursor.fetchone()['tx_count']
        
        cursor.execute('SELECT COUNT(*) as authorizer_count FROM authorizers WHERE code_address != "0x0000000000000000000000000000000000000000"')
        authorizer_count = cursor.fetchone()['authorizer_count']
        
        cursor.execute('SELECT COUNT(*) as code_count FROM codes')
        code_count = cursor.fetchone()['code_count']
        
        cursor.execute('SELECT COUNT(*) as relayer_count FROM relayers')
        relayer_count = cursor.fetchone()['relayer_count']
        
        # Get daily statistical data
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
        
        # Get top10 data
        cursor.execute('SELECT * FROM codes ORDER BY authorizer_count DESC LIMIT 10')
        top10_codes_rows = cursor.fetchall()
        top10_codes = []
        for row in top10_codes_rows:
            code = dict(row)
            code['tags'] = json.loads(code['tags']) if code['tags'] else []
            code['details'] = json.loads(code['details']) if code['details'] else None
            code['type'] = code['details']['type'] if code['details'] and 'type' in code['details'] else ""
            top10_codes.append(code)
        
        cursor.execute('SELECT * FROM relayers ORDER BY tx_count DESC LIMIT 10')
        top10_relayers = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT a.*, c.provider 
            FROM (
                SELECT * FROM authorizers 
                WHERE code_address != "0x0000000000000000000000000000000000000000" 
                ORDER BY tvl_balance DESC 
                LIMIT 10
            ) a 
            LEFT JOIN codes c ON a.code_address = c.code_address
        ''')
        top10_authorizers_rows = cursor.fetchall()
        top10_authorizers = []
        for row in top10_authorizers_rows:
            auth = dict(row)
            # MySQL doesn't have historical_code_address field in updater_mysql.py, skip this line
            # auth['historical_code_address'] = json.loads(auth['historical_code_address']) if auth.get('historical_code_address') else []
            top10_authorizers.append(auth)
        
        cursor.execute('SELECT * FROM tvl')
        tvl_balance = cursor.fetchone()
        
        tvls = {
            'total_tvl_balance': tvl_balance['total_tvl_balance'],
            'eth_tvl_balance': tvl_balance['eth_tvl_balance'], 
            'weth_tvl_balance': tvl_balance['weth_tvl_balance'], 
            'wbtc_tvl_balance': tvl_balance['wbtc_tvl_balance'], 
            'usdt_tvl_balance': tvl_balance['usdt_tvl_balance'], 
            'usdc_tvl_balance': tvl_balance['usdc_tvl_balance'], 
            'dai_tvl_balance': tvl_balance['dai_tvl_balance']
        }
        
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
            'tvls': tvls
        }
        
        conn.close()
        
        return jsonify({
            'overview': overview
        })
    except Exception as e:
        app.logger.error(f"Error getting overview data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# calls pagination query interface
@app.route('/<name>/calls', methods=['GET'])
def get_calls(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters, default to page 1, 10 items per page
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        order = request.args.get('order', 'desc')  # Get sort parameter, default to descending
        search_by = request.args.get('search_by', '')  # Get filter search_by parameter
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        if search_by != '':
            if len(search_by) == 42:  # address (only search indexed fields)
                query = 'SELECT * FROM calls WHERE original_code_address = %s OR parsed_code_address = %s'
                params = [search_by.lower(), search_by.lower()]
            elif len(search_by) == 10:  # function selector
                query = 'SELECT * FROM calls WHERE calling_function = %s'
                params = [search_by.lower()]
            else:
                query = 'SELECT * FROM calls WHERE 1=0'
                params = []
        else:
            query = 'SELECT * FROM calls'
            params = []
        
        # Add sorting
        if order.lower() == 'asc':
            query += ' ORDER BY timestamp ASC'
        else:
            query += ' ORDER BY timestamp DESC'
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        calls = []
        for row in rows:
            call = dict(row)
            calls.append(call)
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'order': order,
            'calls': calls
        })
    except Exception as e:
        app.logger.error(f"Error getting calls data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizations by authorizer pagination query interface
@app.route('/<name>/authorizations_by_authorizer', methods=['GET'])
def get_authorizations_by_authorizer(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        authorizer_address = request.args.get('authorizer_address', '')
        
        if not authorizer_address:
            return jsonify({'error': 'authorizer_address is required'}), 400
        
        conn = get_db_connection(name)
        cursor = conn.cursor()
        
        # Build query
        query = 'SELECT * FROM authorizations WHERE authorizer_address = %s ORDER BY date ASC'
        params = [authorizer_address.lower()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM authorizations WHERE authorizer_address = %s"
        cursor.execute(count_query, [authorizer_address.lower()])
        total = cursor.fetchone()['count']
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, (page - 1) * page_size])
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary
        authorizations = [dict(row) for row in rows]
        
        conn.close()
        
        # Return results
        return jsonify({
            'total': total,
            'page': page,
            'page_size': page_size,
            'authorizations': authorizations
        })
    except Exception as e:
        app.logger.error(f"Error getting authorizations by authorizer: {str(e)}")
        return jsonify({'error': str(e)}), 500

# comparison query interface
@app.route('/<name>/comparison', methods=['GET'])
def get_comparison(name):
    # 验证链名称
    error_response = validate_chain_name(name)
    if error_response:
        return error_response
    
    try:
        # 查找 /dev/shm/ 目录下所有的 *overview.json 文件
        overview_files = glob.glob('/dev/shm/*overview.json')
        
        ret = {}
        
        for file_path in overview_files:
            try:
                # 从文件名提取链的名字（去掉路径和 _overview.json 后缀）
                filename = os.path.basename(file_path)
                chain_name = filename.replace('_overview.json', '')
                if chain_name == "sepolia":
                    continue
                
                # 读取 JSON 文件
                with open(file_path, 'r') as f:
                    overview_data = json.load(f)
                
                # 提取需要的字段
                info = {
                    'tx_count': overview_data.get('tx_count'),
                    'authorizer_count': overview_data.get('authorizer_count'),
                    'code_count': overview_data.get('code_count'),
                    'relayer_count': overview_data.get('relayer_count'),
                    'tvls': overview_data.get('tvls')
                }
                
                # 按照链名存储
                ret[chain_name] = info
                
            except Exception as e:
                app.logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        
        return jsonify(ret)
        
    except Exception as e:
        app.logger.error(f"Error getting comparison data: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Development environment usage
    app.run(host='0.0.0.0', port=3000, debug=False)
else:
    # Production environment entry point
    # When using Gunicorn or uWSGI, this is the WSGI entry point
    app.logger.info(f"{NAME} application has started, ready to accept requests")
