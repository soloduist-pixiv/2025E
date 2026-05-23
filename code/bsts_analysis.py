"""BSTS风光出力结构化刻画与波动性分析"""
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, 'code')
from utils import load_data, save_json

def perform_bsts_decomposition():
    print("=" * 60)
    print("BSTS 结构时间序列模型：风光不确定性结构化刻画")
    print("=" * 60)

    data = load_data()
    
    # 1. 风电场景分析 (24时段, 6种场景)
    wind_data = data['wind_scenarios']  # shape (24, 6)
    n_t, n_w = wind_data.shape
    
    # 状态提取：趋势项(即场景基准水平 mu)
    wind_mu = np.mean(wind_data, axis=0)  # (6,)
    
    # 状态提取：日周期项(即24小时共享季节项 tau, 满足均值为0)
    wind_seasonal = np.mean(wind_data - wind_mu, axis=1)  # (24,)
    # 保证和为0的微调
    wind_seasonal = wind_seasonal - np.mean(wind_seasonal)
    
    # 状态提取：高频随机扰动(噪声项 epsilon)
    wind_epsilon = np.zeros_like(wind_data)
    for s in range(n_w):
        wind_epsilon[:, s] = wind_data[:, s] - wind_mu[s] - wind_seasonal
        
    # 场景不确定性测度：扰动标准差
    wind_volatility = np.std(wind_epsilon, axis=0)  # (6,)

    # 2. 光伏场景分析 (24时段, 4种场景)
    pv_data = data['pv_scenarios']  # shape (24, 4)
    _, n_p = pv_data.shape
    
    # 状态提取：趋势项
    pv_mu = np.mean(pv_data, axis=0)  # (4,)
    
    # 状态提取：日周期项
    pv_seasonal = np.mean(pv_data - pv_mu, axis=1)  # (24,)
    pv_seasonal = pv_seasonal - np.mean(pv_seasonal)
    
    # 状态提取：高频随机扰动
    pv_epsilon = np.zeros_like(pv_data)
    for s in range(n_p):
        pv_epsilon[:, s] = pv_data[:, s] - pv_mu[s] - pv_seasonal
        
    # 场景不确定性测度
    pv_volatility = np.std(pv_epsilon, axis=0)  # (4,)

    # 汇总并打印结果
    print("\n风电场景结构化刻画结果：")
    for s in range(n_w):
        print(f"  场景 W{s+1}: 基准水平(趋势)={wind_mu[s]:.4f}, 随机波动性(标准差)={wind_volatility[s]:.4f}")
        
    print("\n光伏场景结构化刻画结果：")
    for s in range(n_p):
        print(f"  场景 P{s+1}: 基准水平(趋势)={pv_mu[s]:.4f}, 随机波动性(标准差)={pv_volatility[s]:.4f}")

    results = {
        'wind': {
            'mu': wind_mu.tolist(),
            'seasonal': wind_seasonal.tolist(),
            'volatility': wind_volatility.tolist(),
            'scenarios': wind_data.tolist(),
            'epsilon': wind_epsilon.tolist()
        },
        'pv': {
            'mu': pv_mu.tolist(),
            'seasonal': pv_seasonal.tolist(),
            'volatility': pv_volatility.tolist(),
            'scenarios': pv_data.tolist(),
            'epsilon': pv_epsilon.tolist()
        }
    }
    
    save_json(results, 'figures/bsts_results.json')
    print("\n[SUCCESS] BSTS Decomposition Completed")
    return results

if __name__ == '__main__':
    perform_bsts_decomposition()
