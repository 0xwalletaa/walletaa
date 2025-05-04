import util
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# 全局变量
txs = util.get_all_type4_txs_with_timestamp()
last_update_time = time.time()

# 后台更新线程
def update_txs():
    global txs, last_update_time
    while True:
        time.sleep(30)  # 每30秒更新一次
        try:
            txs = util.get_all_type4_txs_with_timestamp()
            last_update_time = time.time()
            print(f"已更新交易数据，共 {len(txs)} 条记录")
        except Exception as e:
            print(f"更新交易数据时出错: {str(e)}")


# 分页查询接口
@app.route('/transactions', methods=['GET'])
def get_transactions():
    # 获取分页参数，默认第1页，每页10条
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    # 计算分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # 获取当前页的交易
    page_txs = txs[start_idx:end_idx]
    
    # 返回结果
    return jsonify({
        'total': len(txs),
        'page': page,
        'page_size': page_size,
        'transactions': page_txs,
        'last_update_time': last_update_time
    })

# 启动后台更新线程
update_thread = threading.Thread(target=update_txs, daemon=True)
update_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
