
def ecrecover(auth):
    chain_id = to_bytes(hexstr=auth['chainId'])
    address_bytes = to_bytes(hexstr=auth['address'])
    nonce = to_bytes(hexstr=auth['nonce'])

    # RLP 编码 [chain_id, address, nonce]
    encoded_data = rlp.encode([chain_id, address_bytes, nonce])

    # 构造 EIP-7702 消息：0x05 || rlp(...)
    message_bytes = b'\x05' + encoded_data
    # 计算 Keccak-256 哈希
    message_hash = keccak(message_bytes)

    # 将签名组件转换为标准格式
    r_bytes = HexBytes(auth['r'])
    s_bytes = HexBytes(auth['s'])
    # yParity (0 or 1) is used directly
    y_parity = int(auth['yParity'], 16)

    # 创建vrs元组
    vrs = (y_parity, r_bytes, s_bytes)
    recovered_address = Account()._recover_hash(message_hash, vrs=vrs)
    
    return recovered_address
