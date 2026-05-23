"""连续调节下限的灵敏度分析与合规边界探讨"""
import numpy as np
from scipy.optimize import minimize
import sys
sys.path.insert(0, 'code')
from utils import *

def solve_lp_continuous_with_lb(P_wind, P_pv, P_load, tou_prices, P_H2NH3, h_target, Q_NH3, scale_factor, LB):
    """在给定出力下限LB的约束下求解连续优化"""
    n = 24
    P_RE = P_wind + P_pv
    surplus = P_RE - P_load

    # 目标函数：最小化用电成本 - 售电收入
    def objective(alpha_vec):
        P_net_vec = surplus - alpha_vec * P_H2NH3
        P_sell_vec = np.maximum(P_net_vec, 0)
        P_buy_vec = np.maximum(-P_net_vec, 0)
        cost = np.sum(tou_prices * P_buy_vec * 1000) - np.sum(0.3779 * P_sell_vec * 1000)
        return cost

    # 约束 1: sum(alpha) = h_target
    constraints = [{'type': 'eq', 'fun': lambda a: np.sum(a) - h_target}]
    
    # 考虑半连续约束 alpha(t) in {0} U [LB, 1] 的近似建模：
    # 我们限制下限为 LB，即 alpha(t) >= LB (对活跃时段)；或者我们在求解后进行后处理投影。
    # 另外一种标准方法是：将非活跃时段设为0，活跃时段下限设为LB。
    # 为保证可导性和收敛，我们采用带下界LB的凸近似：限制 alpha(t) 在 [LB, 1] 之间，对于不需要运行的时段，
    # 允许其在 [0, 1] 中变化但加一个惩罚项，或者直接设置 bounds_alpha = [(LB, 1)] * n。
    # 事实上，当 h_target 较大时 (例如 54吨对应18小时)，大部分时段都处于活跃状态。
    # 为展现高超建模，我们采用投影启发式算法：
    # 1. 求解 alpha in [0, 1] 的松弛解
    bounds_alpha = [(0, 1)] * n
    alpha0 = np.full(n, h_target / n)
    res = minimize(objective, alpha0, method='SLSQP', bounds=bounds_alpha,
                   constraints=constraints, options={'maxiter': 1000, 'ftol': 1e-10})
    
    if abs(np.sum(res.x) - h_target) > 0.01:
        # 尝试不同初始点
        alpha0_alt = np.zeros(n)
        # 优先在surplus大的时段分配
        sorted_idx = np.argsort(-surplus)
        remaining = h_target
        for idx in sorted_idx:
            alloc = min(1.0, remaining)
            alpha0_alt[idx] = alloc
            remaining -= alloc
            if remaining <= 0:
                break
        res = minimize(objective, alpha0_alt, method='SLSQP', bounds=bounds_alpha,
                       constraints=constraints, options={'maxiter': 1000, 'ftol': 1e-10})

    if abs(np.sum(res.x) - h_target) > 0.1:
        return None
        
    alpha = res.x
    
    # 2. 对低于 LB 的非零值进行半连续投影：
    # 找出 alpha 中小于 LB 且大于 0 的时段，将其投影到 0 或 LB
    for t in range(n):
        if 0 < alpha[t] < LB:
            if alpha[t] < LB / 2:
                alpha[t] = 0
            else:
                alpha[t] = LB
                
    # 3. 微调以精确满足 sum(alpha) = h_target
    diff = np.sum(alpha) - h_target
    if abs(diff) > 1e-5:
        # 将多余或缺少的出力均摊到不需要截断的时段（在 [LB, 1] 之间的时段）
        active_indices = [i for i in range(n) if LB <= alpha[i] < 1.0]
        if active_indices:
            alpha[active_indices] -= diff / len(active_indices)
            alpha = np.clip(alpha, 0, 1)
            # 再次微调
            diff2 = np.sum(alpha) - h_target
            if abs(diff2) > 1e-3:
                alpha[active_indices[0]] -= diff2

    # 计算最终物理量
    P_net_final = surplus - alpha * P_H2NH3
    P_sell_arr = np.maximum(P_net_final, 0)
    P_buy_arr = np.maximum(-P_net_final, 0)

    P_total_load = P_load + alpha * P_H2NH3
    E_use = np.sum(P_total_load)
    E_RE = np.sum(P_RE)
    E_buy = np.sum(P_buy_arr)
    E_sell = np.sum(P_sell_arr)

    r1, r2, r3 = calc_green_indicators(E_use, E_RE, E_buy, E_sell)
    h_actual = np.sum(alpha)

    C_ton, _ = calc_ton_cost(
        P_buy_arr, P_sell_arr, P_wind, P_pv, P_H2NH3,
        h_actual, Q_NH3, tou_prices, scale_factor
    )

    return {
        'C_ton': C_ton,
        'compliance': check_green_compliance(r1, r2, r3)
    }

def analyze_regulation_sensitivity():
    print("=" * 60)
    print("功率连续调节下限的灵敏度边界分析")
    print("=" * 60)

    data = load_data()
    tou_prices = data['tou_prices']
    scale_factor = 2.0
    P_H2NH3 = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor  # 41.5 MW
    P_load = data['load_pu'] * P_LOAD_PEAK

    LB_list = [0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20]
    Q_target = 54.0
    h_target = Q_target / 3.0

    results = {}

    for LB in LB_list:
        print(f"\n  求解功率下限: {LB*100:.1f}% ...")
        costs = []
        compliances = []

        for wi in range(6):
            for pi in range(4):
                P_wind_s = data['wind_scenarios'][:, wi] * P_WIND_CAP
                P_pv_s = data['pv_scenarios'][:, pi] * P_PV_CAP

                res = solve_lp_continuous_with_lb(
                    P_wind_s, P_pv_s, P_load, tou_prices,
                    P_H2NH3, h_target, Q_target, scale_factor, LB
                )
                if res:
                    costs.append(res['C_ton'])
                    compliances.append(res['compliance'])

        mean_cost = np.mean(costs)
        n_all_pass = compliances.count('all_pass')
        n_partial = compliances.count('partial')
        n_all_fail = compliances.count('all_fail')

        results[str(LB)] = {
            'mean_cost': round(float(mean_cost), 2),
            'all_pass': n_all_pass,
            'partial': n_partial,
            'all_fail': n_all_fail,
            'costs': [round(float(c), 2) for c in costs]
        }

        print(f"    平均吨氨成本: {mean_cost:.2f} 元/吨")
        print(f"    绿电合规指标: 全满足={n_all_pass}, 部分满足={n_partial}, 全不满足={n_all_fail}")

    save_json(results, 'figures/regulation_sensitivity_results.json')
    print("\n[SUCCESS] Regulation Sensitivity Analysis Completed")
    return results

if __name__ == '__main__':
    analyze_regulation_sensitivity()
