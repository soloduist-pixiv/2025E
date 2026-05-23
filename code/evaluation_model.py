"""GRA-Entropy-TOPSIS多维度园区运行方案综合评价量化模型"""
import numpy as np
import pandas as pd
import json
import sys
sys.path.insert(0, 'code')
from utils import save_json

def run_evaluation_model():
    print("=" * 70)
    print("GRA-Entropy-TOPSIS 多维度综合评价模型")
    print("=" * 70)

    # 1. 方案列表
    schemes = [
        "方案A：联网运行 + 离散调节 (Q2最优)",
        "方案B：联网运行 + 连续调节 (Q3最优)",
        "方案C：离网运行 + 无储能 (Q4-1)",
        "方案D：离网运行 + 最优储能 (Q4-2)"
    ]
    
    # 2. 指标列表
    indicators = [
        "吨氨综合成本 (元/吨) [成本型]",
        "全年绿电直连合规天数 (天) [效益型]",
        "风光自给消纳率 (%) [效益型]",
        "电网支撑柔性调峰容量 (MW) [效益型]",
        "碳减排强度与绿氨溢价 (%) [效益型]",
        "能源自治抗电价风险能力 (%) [效益型]"
    ]
    
    # 3. 原始决策矩阵 X (4种方案, 6个指标)
    # 数据来源于前几题的计算结果及隐性效益量化：
    # C1: 吨氨综合成本 (越低越好)：4585.15, 4283.62, 4220.00, 4133.64
    # C2: 合规天数 (越高越好)：Q2离散为0天, Q3连续为165天, 离网(C, D)为100%合规即360天
    # C3: 风光自给消纳率 (越高越好)：45.0, 72.0, 100.0, 100.0
    # C4: 电网支撑柔性调峰容量 (越高越好)：离散为0, 连续调节为 0.9 * 41.5 = 37.35 MW, 离网(C, D)为0 MW
    # C5: 碳减排与绿氨溢价 (越高越好)：联网离散为45.0%, 联网连续为72.0%, 离网(C, D)为100.0%
    # C6: 能源自治抗电价风险能力 (越高越好)：离散为10.0%, 连续为30.0%, 离网(C, D)为100.0%
    X = np.array([
        [4585.15, 0.0,   45.0,  0.0,   45.0,  10.0],  # 方案A
        [4283.62, 165.0, 72.0,  37.35, 72.0,  30.0],  # 方案B
        [4220.00, 360.0, 100.0, 0.0,   100.0, 100.0], # 方案C
        [4133.64, 360.0, 100.0, 0.0,   100.0, 100.0]  # 方案D
    ])
    
    n_schemes, n_indicators = X.shape
    
    # 4. 矩阵标准化 Z
    Z = np.zeros_like(X)
    # 指标类型：0是成本型，1-5是效益型
    for j in range(n_indicators):
        col = X[:, j]
        min_val = np.min(col)
        max_val = np.max(col)
        if max_val == min_val:
            Z[:, j] = 1.0
        else:
            if j == 0:  # 成本型
                Z[:, j] = (max_val - col) / (max_val - min_val)
            else:       # 效益型
                Z[:, j] = (col - min_val) / (max_val - min_val)
                
    # 5. 熵权法计算指标权重
    # 为避免 log(0)，加微小正数
    epsilon = 1e-12
    p = np.zeros_like(Z)
    for j in range(n_indicators):
        sum_col = np.sum(Z[:, j])
        if sum_col == 0:
            p[:, j] = 1.0 / n_schemes
        else:
            p[:, j] = Z[:, j] / sum_col
            
    # 计算熵值
    E = -np.sum(p * np.log(p + epsilon), axis=0) / np.log(n_schemes)
    
    # 计算差异度
    D = 1.0 - E
    # 权重
    weights = D / np.sum(D)
    
    # 6. TOPSIS 相对贴近度计算
    # 加权标准化矩阵
    V = Z * weights
    
    # 正负理想解
    V_plus = np.max(V, axis=0)
    V_minus = np.min(V, axis=0)
    
    # 计算距离
    D_plus = np.sqrt(np.sum((V - V_plus)**2, axis=1))
    D_minus = np.sqrt(np.sum((V - V_minus)**2, axis=1))
    
    # 贴近度评分 (TOPSIS得分)
    topsis_scores = D_minus / (D_plus + D_minus)
    
    # 7. 灰色关联度分析 (GRA) 关联度计算
    rho = 0.5
    xi = np.zeros_like(V)
    for i in range(n_schemes):
        for j in range(n_indicators):
            dist = abs(V_plus[j] - V[i, j])
            min_dist = np.min(np.abs(V - V_plus))
            max_dist = np.max(np.abs(V - V_plus))
            xi[i, j] = (min_dist + rho * max_dist) / (dist + rho * max_dist)
            
    gra_scores = np.dot(xi, weights)
    
    # 8. 组合得分 (TOPSIS与GRA等权重融合)
    combined_scores = 0.5 * topsis_scores + 0.5 * gra_scores
    
    # 9. 排序
    rank_indices = np.argsort(-combined_scores)
    
    # 结果打包
    results = {
        'weights': [round(float(w), 4) for w in weights],
        'indicators': indicators,
        'schemes': schemes,
        'decision_matrix': X.tolist(),
        'standardized_matrix': Z.tolist(),
        'topsis_scores': [round(float(s), 4) for s in topsis_scores],
        'gra_scores': [round(float(s), 4) for s in gra_scores],
        'combined_scores': [round(float(s), 4) for s in combined_scores],
        'rank': [int(r + 1) for r in np.argsort(-combined_scores)]
    }
    
    # 打印排版表格
    print("\n--- 熵权法计算得到的权重分布 ---")
    for j in range(n_indicators):
        print(f"  {indicators[j]:<35}: 权重 = {weights[j]*100:.2f}%")
        
    print("\n--- 各方案综合评价得分与排名 ---")
    print(f"{'方案名称':<35} | {'TOPSIS得分':<10} | {'GRA关联度':<10} | {'综合得分':<10} | {'排名':<5}")
    print("-" * 80)
    for idx in rank_indices:
        print(f"{schemes[idx]:<35} | {topsis_scores[idx]:.4f}     | {gra_scores[idx]:.4f}    | {combined_scores[idx]:.4f}    | {np.where(rank_indices == idx)[0][0] + 1}")
        
    save_json(results, 'figures/evaluation_results.json')
    print("\n[SUCCESS] GRA-Entropy-TOPSIS Evaluation Completed")
    return results

if __name__ == '__main__':
    run_evaluation_model()
