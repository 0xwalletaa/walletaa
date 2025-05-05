import util
from flask import Flask, request, jsonify
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import os

# 配置日志
log_dir = "logs"
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
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# 添加数据锁
data_lock = threading.RLock()

# 全局变量
txs = []
last_update_time = 0
authorizers = []
authorizers_with_zero = []
codes_by_eth_balance = []
codes_by_authorizer_count = []

# 初始化数据
def initialize_data():
    global txs, last_update_time, authorizers, authorizers_with_zero, codes_by_eth_balance, codes_by_authorizer_count
    try:
        with data_lock:
            txs = util.get_all_type4_txs_with_timestamp()
            authorizers = util.get_authorizer_info(txs)
            authorizers_with_zero = util.get_authorizer_info(txs, include_zero=True)
            codes_by_eth_balance = util.get_code_info(authorizers, sort_by="eth_balance")
            codes_by_authorizer_count = util.get_code_info(authorizers, sort_by="authorizer_count")
            last_update_time = time.time()
        app.logger.info(f"数据初始化成功，共 {len(txs)} 条记录")
    except Exception as e:
        app.logger.error(f"数据初始化失败: {str(e)}")
        raise

# 后台更新线程
def update_txs():
    global txs, last_update_time, authorizers, authorizers_with_zero, codes_by_eth_balance, codes_by_authorizer_count
    while True:
        time.sleep(30)  # 每30秒更新一次
        try:
            new_txs = util.get_all_type4_txs_with_timestamp()
            new_authorizers = util.get_authorizer_info(new_txs)
            new_authorizers_with_zero = util.get_authorizer_info(new_txs, include_zero=True)
            new_codes_by_eth_balance = util.get_code_info(new_authorizers, sort_by="eth_balance")
            new_codes_by_authorizer_count = util.get_code_info(new_authorizers, sort_by="authorizer_count")
            
            with data_lock:
                txs = new_txs
                authorizers = new_authorizers
                authorizers_with_zero = new_authorizers_with_zero
                codes_by_eth_balance = new_codes_by_eth_balance
                codes_by_authorizer_count = new_codes_by_authorizer_count
                last_update_time = time.time()
            
            app.logger.info(f"已更新交易数据，共 {len(txs)} 条记录")
        except Exception as e:
            app.logger.error(f"更新交易数据时出错: {str(e)}")


# 分页查询接口
@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        with data_lock:
            # 创建副本避免竞态条件
            current_txs = txs.copy()
            current_last_update_time = last_update_time
        
        # 获取分页参数，默认第1页，每页10条
        reversed_txs = current_txs[::-1]
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 计算分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的交易
        page_txs = reversed_txs[start_idx:end_idx]
        
        # 返回结果
        return jsonify({
            'total': len(current_txs),
            'page': page,
            'page_size': page_size,
            'transactions': page_txs,
            'last_update_time': current_last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取交易数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# authorizers分页查询接口
@app.route('/authorizers', methods=['GET'])
def get_authorizers():
    try:
        with data_lock:
            # 创建副本避免竞态条件
            current_authorizers = authorizers.copy()
            current_last_update_time = last_update_time
        
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 计算分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的授权者信息
        page_authorizers = current_authorizers[start_idx:end_idx]
        
        # 返回结果
        return jsonify({
            'total': len(current_authorizers),
            'page': page,
            'page_size': page_size,
            'authorizers': page_authorizers,
            'last_update_time': current_last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取授权者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# authorizers_with_zero分页查询接口
@app.route('/authorizers_with_zero', methods=['GET'])
def get_authorizers_with_zero():
    try:
        with data_lock:
            # 创建副本避免竞态条件
            current_authorizers_with_zero = authorizers_with_zero.copy()
            current_last_update_time = last_update_time
        
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 计算分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的授权者信息
        page_authorizers = current_authorizers_with_zero[start_idx:end_idx]
        
        # 返回结果
        return jsonify({
            'total': len(current_authorizers_with_zero),
            'page': page,
            'page_size': page_size,
            'authorizers': page_authorizers,
            'last_update_time': current_last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取带零授权者数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# codes_by_eth_balance分页查询接口
@app.route('/codes_by_eth_balance', methods=['GET'])
def get_codes_by_eth_balance():
    try:
        with data_lock:
            # 创建副本避免竞态条件
            current_codes_by_eth_balance = codes_by_eth_balance.copy()
            current_last_update_time = last_update_time
        
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 计算分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的代码信息
        page_codes = current_codes_by_eth_balance[start_idx:end_idx]
        
        # 返回结果
        return jsonify({
            'total': len(current_codes_by_eth_balance),
            'page': page,
            'page_size': page_size,
            'codes': page_codes,
            'last_update_time': current_last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以ETH余额排序的代码数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# codes_by_authorizer_count分页查询接口
@app.route('/codes_by_authorizer_count', methods=['GET'])
def get_codes_by_authorizer_count():
    try:
        with data_lock:
            # 创建副本避免竞态条件
            current_codes_by_authorizer_count = codes_by_authorizer_count.copy()
            current_last_update_time = last_update_time
        
        # 获取分页参数，默认第1页，每页10条
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # 计算分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的代码信息
        page_codes = current_codes_by_authorizer_count[start_idx:end_idx]
        
        # 返回结果
        return jsonify({
            'total': len(current_codes_by_authorizer_count),
            'page': page,
            'page_size': page_size,
            'codes': page_codes,
            'last_update_time': current_last_update_time
        })
    except Exception as e:
        app.logger.error(f"获取以授权者数量排序的代码数据时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'last_update_time': last_update_time})

# 初始化数据
initialize_data()
    
# 启动后台更新线程
update_thread = threading.Thread(target=update_txs, daemon=True)
update_thread.start()

if __name__ == '__main__':
    # 开发环境使用
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # 生产环境入口点
    # 使用Gunicorn或uWSGI运行时，这里是WSGI入口点
    app.logger.info("应用已启动，准备接受请求")
