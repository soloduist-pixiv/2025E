"""问题四：绿电直连型电氢氨园区离网运行分析及储能配置研究"""
import numpy as np
from scipy.optimize import minimize
import sys
sys.path.insert(0, 'code')
from utils import *


def solve_offgrid_no_storage(P_wind, P_pv, P_load, P_H2NH3):
    """子问题(1): 无储能离网运行, 最大化产氨量"""
    n = 24
    P_RE = P_wind + P_pv
    surplus = P_RE - P_load

    # 每时段最大可用出力系数
    alpha_max = np.clip(surplus / P_H2NH3, 0, 1)
    # 10%下限: alpha < 0.1 则停机
    alpha = np.where(alpha_max >= 0.1, alpha_max, 0)

    # 产氨量
    Q_NH3 = np.sum(alpha) * 3.0  # 吨 (产氨速率3吨/h at full load)
    h_actual = np.sum(alpha)

    # 弃电量
    P_curtail = P_RE - P_load - alpha * P_H2NH3
    P_curtail = np.maximum(P_curtail, 0)
    E_curtail = np.sum(P_curtail)

    # 风光利用率
    E_RE = np.sum(P_RE)
    E_used = E_RE - E_curtail
    RE_utilization = E_used / E_RE * 100 if E_RE > 0 else 0

    # 吨氨成本(离网, 无购电)
    E_wind = np.sum(P_wind)
    E_pv = np.sum(P_pv)
    C_RE = WIND_COST * E_wind * 1000 + PV_COST * E_pv * 1000

    scale_factor = 2.0
    P_ALKEL = P_ALKEL_BASE * scale_factor
    P_PEMEL = P_PEMEL_BASE * scale_factor
    P_NH3_rated = P_NH3_BASE * scale_factor
    E_ALKEL = P_ALKEL * h_actual * 0.5  # 按比例分配
    E_PEMEL = P_PEMEL * h_actual * 0.5
    # 实际用电 = sum(alpha * P_H2NH3)
    E_H2NH3_actual = np.sum(alpha * P_H2NH3)
    C_OM_H2 = (OM_ALKEL * P_ALKEL / P_H2NH3 * E_H2NH3_actual +
               OM_PEMEL * P_PEMEL / P_H2NH3 * E_H2NH3_actual) * 1000
    C_OM_NH3 = OM_NH3 * P_NH3_rated / P_H2NH3 * E_H2NH3_actual * 1000

    H2_capacity = (H2_RATE_ALKEL + H2_RATE_PEMEL) * scale_factor
    NH3_invest_total = H2_capacity * NH3_INVEST
    C_dep_NH3 = NH3_invest_total / (NH3_LIFE * 365)

    total_cost = C_RE + C_OM_H2 + C_OM_NH3 + C_dep_NH3
    C_ton = total_cost / Q_NH3 if Q_NH3 > 0 else float('inf')

    return {
        'alpha': alpha.tolist(),
        'Q_NH3': round(float(Q_NH3), 2),
        'h_actual': round(float(h_actual), 2),
        'E_curtail': round(float(E_curtail), 2),
        'E_RE': round(float(E_RE), 2),
        'RE_utilization': round(float(RE_utilization), 2),
        'C_ton': round(float(C_ton), 2),
        'P_curtail': P_curtail.tolist(),
    }


def solve_offgrid_with_storage(P_wind, P_pv, P_load, P_H2NH3, C_bat):
    """子问题(2): 有储能离网运行LP
    给定储能容量C_bat, 最大化产氨量
    """
    n = 24
    P_RE = P_wind + P_pv
    surplus = P_RE - P_load
    scale_factor = 2.0

    # 决策变量: alpha(24), P_ch(24), P_dis(24) = 72维
    # SOC由动态方程确定, 不作为独立变量

    def objective(x):
        alpha = x[:n]
        return -np.sum(alpha)  # 最大化产量 = 最小化负产量

    def constraint_balance(x):
        """功率平衡: alpha*P_H2NH3 + P_load + P_ch = P_RE + P_dis"""
        alpha = x[:n]
        P_ch = x[n:2*n]
        P_dis = x[2*n:3*n]
        return P_RE + P_dis - P_load - alpha * P_H2NH3 - P_ch

    def constraint_soc(x):
        """SOC约束: 0.1*C_bat <= E(t) <= 0.9*C_bat, E(1)=E(25)=0.5*C_bat"""
        P_ch = x[n:2*n]
        P_dis = x[2*n:3*n]
        violations = []
        E = 0.5 * C_bat  # 初始SOC
        for t in range(n):
            E = (1 - BAT_SIGMA) * E + BAT_ETA_CH * P_ch[t] - P_dis[t] / BAT_ETA_DIS
            violations.append(E - 0.1 * C_bat)  # >= 0
            violations.append(0.9 * C_bat - E)  # >= 0
        violations.append(-(abs(E - 0.5 * C_bat) - 0.5 * C_bat * 0.05))  # 终末SOC约束(允许5%误差)
        return np.array(violations)

    # 初始解: 无储能时的alpha + 零充放电
    alpha_init = np.clip(surplus / P_H2NH3, 0, 1)
    alpha_init = np.where(alpha_init >= 0.1, alpha_init, 0)
    x0 = np.concatenate([alpha_init, np.zeros(n), np.zeros(n)])

    # 变量界
    P_max_ch = 0.5 * C_bat  # C-rate = 0.5C
    P_max_dis = 0.5 * C_bat
    bounds = ([(0, 1)] * n +
              [(0, P_max_ch)] * n +
              [(0, P_max_dis)] * n)

    constraints = [
        {'type': 'eq', 'fun': constraint_balance},
        {'type': 'ineq', 'fun': constraint_soc},
    ]

    res = minimize(objective, x0, method='SLSQP', bounds=bounds,
                   constraints=constraints, options={'maxiter': 2000, 'ftol': 1e-10})

    alpha = res.x[:n]
    P_ch = res.x[n:2*n]
    P_dis = res.x[2*n:3*n]

    # 计算SOC轨迹
    E_soc = np.zeros(n + 1)
    E_soc[0] = 0.5 * C_bat
    for t in range(n):
        E_soc[t+1] = (1 - BAT_SIGMA) * E_soc[t] + BAT_ETA_CH * P_ch[t] - P_dis[t] / BAT_ETA_DIS

    Q_NH3 = np.sum(alpha) * 3.0
    h_actual = np.sum(alpha)

    # 弃电
    P_curtail = P_RE - P_load - alpha * P_H2NH3 - P_ch + P_dis
    P_curtail = np.maximum(P_curtail, 0)
    E_curtail = np.sum(P_curtail)
    E_RE = np.sum(P_RE)
    RE_utilization = (E_RE - E_curtail) / E_RE * 100 if E_RE > 0 else 0

    # 成本(含储能折旧)
    E_wind = np.sum(P_wind)
    E_pv = np.sum(P_pv)
    C_RE_cost = WIND_COST * E_wind * 1000 + PV_COST * E_pv * 1000

    E_H2NH3_actual = np.sum(alpha * P_H2NH3)
    P_ALKEL = P_ALKEL_BASE * scale_factor
    P_PEMEL = P_PEMEL_BASE * scale_factor
    P_NH3_rated = P_NH3_BASE * scale_factor
    C_OM_H2 = (OM_ALKEL * P_ALKEL / P_H2NH3 * E_H2NH3_actual +
               OM_PEMEL * P_PEMEL / P_H2NH3 * E_H2NH3_actual) * 1000
    C_OM_NH3 = OM_NH3 * P_NH3_rated / P_H2NH3 * E_H2NH3_actual * 1000

    H2_capacity = (H2_RATE_ALKEL + H2_RATE_PEMEL) * scale_factor
    NH3_invest_total = H2_capacity * NH3_INVEST
    C_dep_NH3 = NH3_invest_total / (NH3_LIFE * 365)

    # 储能折旧和运维
    C_bat_dep = C_bat * 1000 / (BAT_LIFE * 365)  # 元/日
    E_ch_total = np.sum(P_ch)
    E_dis_total = np.sum(P_dis)
    C_bat_om = BAT_OM * (E_ch_total + E_dis_total) * 1000

    total_cost = C_RE_cost + C_OM_H2 + C_OM_NH3 + C_dep_NH3 + C_bat_dep + C_bat_om
    C_ton = total_cost / Q_NH3 if Q_NH3 > 0 else float('inf')

    return {
        'C_bat': C_bat,
        'Q_NH3': round(float(Q_NH3), 2),
        'h_actual': round(float(h_actual), 2),
        'E_curtail': round(float(E_curtail), 2),
        'E_RE': round(float(E_RE), 2),
        'RE_utilization': round(float(RE_utilization), 2),
        'C_ton': round(float(C_ton), 2),
        'C_bat_dep': round(float(C_bat_dep), 2),
        'C_bat_om': round(float(C_bat_om), 2),
        'E_ch_total': round(float(E_ch_total), 2),
        'E_dis_total': round(float(E_dis_total), 2),
        'SOC': E_soc.tolist(),
        'alpha': alpha.tolist(),
    }


def solve_problem4():
    print("=" * 60)
    print("问题四：离网运行及储能配置")
    print("=" * 60)

    data = load_data()
    tou_prices = data['tou_prices']
    scale_factor = 2.0
    P_H2NH3 = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor  # 41.5 MW
    P_load = data['load_pu'] * P_LOAD_PEAK

    # ===== 子问题(1): 无储能离网 =====
    print(f"\n{'='*40}")
    print("子问题(1): 无储能离网运行")
    print(f"{'='*40}")

    offgrid_results = []
    max_curtail = 0
    max_curtail_scenario = ""

    for wi in range(6):
        for pi in range(4):
            scenario_id = f"W{wi+1}_P{pi+1}"
            P_wind_s = data['wind_scenarios'][:, wi] * P_WIND_CAP
            P_pv_s = data['pv_scenarios'][:, pi] * P_PV_CAP

            result = solve_offgrid_no_storage(P_wind_s, P_pv_s, P_load, P_H2NH3)
            result['scenario'] = scenario_id
            offgrid_results.append(result)

            if result['E_curtail'] > max_curtail:
                max_curtail = result['E_curtail']
                max_curtail_scenario = scenario_id

    # 统计
    Q_all = [r['Q_NH3'] for r in offgrid_results]
    C_all = [r['C_ton'] for r in offgrid_results]
    RE_util = [r['RE_utilization'] for r in offgrid_results]

    annual_Q = np.sum(Q_all) * DAYS_PER_SCENARIO  # 全年总产氨量
    avg_utilization = np.mean([r['h_actual'] for r in offgrid_results]) / 24 * 100

    print(f"\n  全年产氨总量: {annual_Q:.1f} 吨")
    print(f"  日均产氨: {np.mean(Q_all):.2f} 吨/日")
    print(f"  产能利用率: {avg_utilization:.1f}%")
    print(f"  吨氨成本: 均值={np.mean(C_all):.2f}, 范围=[{np.min(C_all):.2f}, {np.max(C_all):.2f}]")
    print(f"  风光利用率: 均值={np.mean(RE_util):.1f}%")
    print(f"  最大弃电场景: {max_curtail_scenario}, 弃电量={max_curtail:.2f} MWh")

    # 最小风光装机估算
    # 要求最差场景下至少能维持10%负荷
    min_RE_needed = P_load.mean() + 0.1 * P_H2NH3  # MW (平均)
    # 找最差场景的平均标幺值
    min_wind_pu = np.min([np.mean(data['wind_scenarios'][:, wi]) for wi in range(6)])
    min_pv_pu = np.min([np.mean(data['pv_scenarios'][:, pi]) for pi in range(4)])
    # P_wind_cap * min_wind_pu + P_pv_cap * min_pv_pu >= min_RE_needed
    # 假设风光比例不变(40:64), 求最小装机
    ratio_wind = P_WIND_CAP / (P_WIND_CAP + P_PV_CAP)
    ratio_pv = P_PV_CAP / (P_WIND_CAP + P_PV_CAP)
    # total_cap * (ratio_wind * min_wind_pu + ratio_pv * min_pv_pu) >= min_RE_needed
    avg_pu = ratio_wind * min_wind_pu + ratio_pv * min_pv_pu
    min_total_cap = min_RE_needed / avg_pu if avg_pu > 0 else float('inf')
    min_wind_cap = min_total_cap * ratio_wind
    min_pv_cap = min_total_cap * ratio_pv

    print(f"\n  最小风光装机估算(保证最差场景10%负荷):")
    print(f"    最小风电装机: {min_wind_cap:.1f} MW")
    print(f"    最小光伏装机: {min_pv_cap:.1f} MW")

    # ===== 子问题(2): 储能配置优化 =====
    print(f"\n{'='*40}")
    print(f"子问题(2): 储能配置优化 (最大弃电场景: {max_curtail_scenario})")
    print(f"{'='*40}")

    # 找到最大弃电场景的数据
    parts = max_curtail_scenario.split('_')
    wi_max = int(parts[0][1:]) - 1
    pi_max = int(parts[1][1:]) - 1
    P_wind_max = data['wind_scenarios'][:, wi_max] * P_WIND_CAP
    P_pv_max = data['pv_scenarios'][:, pi_max] * P_PV_CAP

    # 网格搜索最优储能容量
    print("  粗搜索 (步长20 MWh)...")
    C_bat_range_coarse = np.arange(20, 401, 20)
    results_coarse = []

    for C_bat in C_bat_range_coarse:
        result = solve_offgrid_with_storage(P_wind_max, P_pv_max, P_load, P_H2NH3, C_bat)
        results_coarse.append(result)
        if len(results_coarse) % 5 == 0:
            print(f"    C_bat={C_bat} MWh: Q={result['Q_NH3']:.1f}吨, C_ton={result['C_ton']:.0f}元/吨")

    # 找最优(最小吨氨成本)
    costs_coarse = [r['C_ton'] for r in results_coarse]
    best_idx = np.argmin(costs_coarse)
    best_C_bat_coarse = C_bat_range_coarse[best_idx]

    # 细搜索
    print(f"\n  细搜索 (在{best_C_bat_coarse-20}~{best_C_bat_coarse+20} MWh, 步长5)...")
    C_bat_range_fine = np.arange(max(10, best_C_bat_coarse - 20),
                                  best_C_bat_coarse + 25, 5)
    results_fine = []
    for C_bat in C_bat_range_fine:
        result = solve_offgrid_with_storage(P_wind_max, P_pv_max, P_load, P_H2NH3, C_bat)
        results_fine.append(result)

    costs_fine = [r['C_ton'] for r in results_fine]
    best_idx_fine = np.argmin(costs_fine)
    best_C_bat = float(C_bat_range_fine[best_idx_fine])
    best_storage_result = results_fine[best_idx_fine]

    print(f"\n  最优储能容量: {best_C_bat:.0f} MWh")
    print(f"  产氨量: {best_storage_result['Q_NH3']:.2f} 吨/日")
    print(f"  吨氨成本: {best_storage_result['C_ton']:.2f} 元/吨")
    print(f"  风光利用率: {best_storage_result['RE_utilization']:.1f}%")

    # 无储能对比
    no_storage_result = [r for r in offgrid_results if r['scenario'] == max_curtail_scenario][0]
    print(f"\n  对比(最大弃电场景):")
    print(f"    无储能: Q={no_storage_result['Q_NH3']:.2f}吨, C_ton={no_storage_result['C_ton']:.2f}元/吨, RE_util={no_storage_result['RE_utilization']:.1f}%")
    print(f"    有储能: Q={best_storage_result['Q_NH3']:.2f}吨, C_ton={best_storage_result['C_ton']:.2f}元/吨, RE_util={best_storage_result['RE_utilization']:.1f}%")

    # 全场景有储能调度
    print(f"\n  全场景有储能调度 (C_bat={best_C_bat:.0f} MWh)...")
    storage_all_results = []
    for wi in range(6):
        for pi in range(4):
            scenario_id = f"W{wi+1}_P{pi+1}"
            P_wind_s = data['wind_scenarios'][:, wi] * P_WIND_CAP
            P_pv_s = data['pv_scenarios'][:, pi] * P_PV_CAP
            result = solve_offgrid_with_storage(P_wind_s, P_pv_s, P_load, P_H2NH3, best_C_bat)
            result['scenario'] = scenario_id
            storage_all_results.append(result)

    Q_storage = [r['Q_NH3'] for r in storage_all_results]
    C_storage = [r['C_ton'] for r in storage_all_results]
    RE_storage = [r['RE_utilization'] for r in storage_all_results]

    annual_Q_storage = np.sum(Q_storage) * DAYS_PER_SCENARIO
    avg_util_storage = np.mean([r['h_actual'] for r in storage_all_results]) / 24 * 100

    print(f"\n  有储能全年统计:")
    print(f"    全年产氨总量: {annual_Q_storage:.1f} 吨")
    print(f"    产能利用率: {avg_util_storage:.1f}%")
    print(f"    吨氨成本: 均值={np.mean(C_storage):.2f}")
    print(f"    风光利用率: 均值={np.mean(RE_storage):.1f}%")

    # ===== 子问题(3): 离网vs联网经济性对比 =====
    print(f"\n{'='*40}")
    print("子问题(3): 离网vs联网经济性对比")
    print(f"{'='*40}")

    import json
    with open('figures/problem_3_results.json', 'r', encoding='utf-8') as f:
        q3_results = json.load(f)

    # 联网模式: 问题三最优产量的全年平均成本
    q3_annual_cost = q3_results['annual_analysis']['annual_costs_by_Q']
    # 离网模式: 有储能的全年平均成本
    offgrid_annual_cost = np.mean(C_storage)

    # 找相同产量下的对比
    offgrid_daily_Q = np.mean(Q_storage)
    # 联网模式下最接近的产量
    closest_Q = min([36, 45, 54, 63, 72], key=lambda q: abs(q - offgrid_daily_Q))
    grid_cost_same_Q = q3_annual_cost[str(closest_Q)]

    print(f"  离网日均产量: {offgrid_daily_Q:.1f} 吨/日")
    print(f"  对比联网产量: {closest_Q} 吨/日")
    print(f"  离网吨氨成本(有储能): {offgrid_annual_cost:.2f} 元/吨")
    print(f"  联网吨氨成本(问题三): {grid_cost_same_Q} 元/吨")
    cost_diff = offgrid_annual_cost - grid_cost_same_Q
    print(f"  成本差异: {cost_diff:.2f} 元/吨 ({'离网更贵' if cost_diff > 0 else '离网更便宜'})")
    print(f"  系统支撑价值: {abs(cost_diff):.2f} 元/吨")

    # 保存结果
    results = {
        'offgrid_no_storage': {
            'scenarios': [{
                'scenario': r['scenario'],
                'Q_NH3': r['Q_NH3'],
                'C_ton': r['C_ton'],
                'RE_utilization': r['RE_utilization'],
                'E_curtail': r['E_curtail'],
            } for r in offgrid_results],
            'annual_Q': round(float(annual_Q), 1),
            'avg_daily_Q': round(float(np.mean(Q_all)), 2),
            'avg_utilization': round(float(avg_utilization), 1),
            'mean_C_ton': round(float(np.mean(C_all)), 2),
            'mean_RE_util': round(float(np.mean(RE_util)), 1),
            'max_curtail_scenario': max_curtail_scenario,
            'max_curtail_MWh': round(float(max_curtail), 2),
        },
        'min_capacity': {
            'min_wind_MW': round(float(min_wind_cap), 1),
            'min_pv_MW': round(float(min_pv_cap), 1),
        },
        'storage_optimization': {
            'best_C_bat_MWh': best_C_bat,
            'target_scenario': max_curtail_scenario,
            'best_result': {
                'Q_NH3': best_storage_result['Q_NH3'],
                'C_ton': best_storage_result['C_ton'],
                'RE_utilization': best_storage_result['RE_utilization'],
            },
            'capacity_cost_curve': {
                'C_bat_values': C_bat_range_coarse.tolist(),
                'C_ton_values': costs_coarse,
                'Q_NH3_values': [r['Q_NH3'] for r in results_coarse],
            },
        },
        'storage_all_scenarios': {
            'annual_Q': round(float(annual_Q_storage), 1),
            'avg_daily_Q': round(float(np.mean(Q_storage)), 2),
            'avg_utilization': round(float(avg_util_storage), 1),
            'mean_C_ton': round(float(np.mean(C_storage)), 2),
            'mean_RE_util': round(float(np.mean(RE_storage)), 1),
            'costs': C_storage,
            'Q_values': Q_storage,
        },
        'grid_vs_offgrid': {
            'offgrid_cost': round(float(offgrid_annual_cost), 2),
            'grid_cost': grid_cost_same_Q,
            'cost_diff': round(float(cost_diff), 2),
            'offgrid_daily_Q': round(float(offgrid_daily_Q), 1),
            'grid_Q': closest_Q,
            'system_support_value': round(float(abs(cost_diff)), 2),
        },
    }

    save_json(results, 'figures/problem_4_results.json')
    print("\n✅ 问题四求解完成")
    return results


if __name__ == '__main__':
    results = solve_problem4()
