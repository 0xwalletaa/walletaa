import util
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# 全局变量
txs = util.get_all_type4_txs_with_timestamp()
last_update_time = time.time()
authorizers = util.get_authorizer_info(txs)
authorizers_with_zero = util.get_authorizer_info(txs, include_zero=True)
codes_by_eth_balance = util.get_code_info(authorizers, sort_by="eth_balance")
codes_by_authorizer_count = util.get_code_info(authorizers, sort_by="authorizer_count")
# 后台更新线程
def update_txs():
    global txs, last_update_time, authorizers, authorizers_with_zero, codes_by_eth_balance, codes_by_authorizer_count
    while True:
        time.sleep(30)  # 每30秒更新一次
        try:
            txs = util.get_all_type4_txs_with_timestamp()
            authorizers = util.get_authorizer_info(txs)
            authorizers_with_zero = util.get_authorizer_info(txs, include_zero=True)
            codes_by_eth_balance = util.get_code_info(authorizers, sort_by="eth_balance")
            codes_by_authorizer_count = util.get_code_info(authorizers, sort_by="authorizer_count")
            last_update_time = time.time()
            print(f"已更新交易数据，共 {len(txs)} 条记录")
        except Exception as e:
            print(f"更新交易数据时出错: {str(e)}")


# 分页查询接口
@app.route('/transactions', methods=['GET'])
def get_transactions():
    # 获取分页参数，默认第1页，每页10条
    reversed_txs = txs[::-1]
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的交易
    page_txs = reversed_txs[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(txs),
        'page': page,
        'page_size': page_size,
        'transactions': page_txs,
        'last_update_time': last_update_time
    })

# authorizers分页查询接口
@app.route('/authorizers', methods=['GET'])
def get_authorizers():
    # 获取分页参数，默认第1页，每页10条
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的授权者信息
    page_authorizers = authorizers[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(authorizers),
        'page': page,
        'page_size': page_size,
        'authorizers': page_authorizers,
        'last_update_time': last_update_time
    })


# authorizers_with_zero分页查询接口
@app.route('/authorizers_with_zero', methods=['GET'])
def get_authorizers_with_zero():
    # 获取分页参数，默认第1页，每页10条
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的授权者信息
    page_authorizers = authorizers_with_zero[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(authorizers_with_zero),
        'page': page,
        'page_size': page_size,
        'authorizers': page_authorizers,
        'last_update_time': last_update_time
    })

# codes_by_eth_balance分页查询接口
@app.route('/codes_by_eth_balance', methods=['GET'])
def get_codes_by_eth_balance():
    # 获取分页参数，默认第1页，每页10条
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的代码信息
    page_codes = codes_by_eth_balance[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(codes_by_eth_balance),
        'page': page,
        'page_size': page_size,
        'codes': page_codes,
        'last_update_time': last_update_time
    })


# codes_by_authorizer_count分页查询接口
@app.route('/codes_by_authorizer_count', methods=['GET'])
def get_codes_by_authorizer_count():
    # 获取分页参数，默认第1页，每页10条
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的代码信息
    page_codes = codes_by_authorizer_count[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(codes_by_authorizer_count),
        'page': page,
        'page_size': page_size,
        'codes': page_codes,
        'last_update_time': last_update_time
    })
    
# 启动后台更新线程
update_thread = threading.Thread(target=update_txs, daemon=True)
update_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
