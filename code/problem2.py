"""问题二：基于离散制氨调节的绿电直连型电氢氨园区运行优化"""
import numpy as np
import sys
sys.path.insert(0, 'code')
from utils import *

try:
    from pulp import *
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pulp', '-q'])
    from pulp import *


def solve_ilp_single(P_RE_surplus, tou_prices, P_H2NH3, h_required, Q_NH3,
                     P_wind, P_pv, P_load, scale_factor):
    """求解单个ILP问题
    由于x(t)确定后P_net(t)确定, P_buy和P_sell也确定(互补),
    直接用枚举/ILP对目标函数建模。

    关键洞察: 给定x(t), P_net(t) = P_RE_surplus(t) - x(t)*P_H2NH3
    P_buy(t) = max(-P_net(t), 0), P_sell(t) = max(P_net(t), 0)

    目标函数是x(t)的分段线性函数, 用大M法线性化。
    """
    h = int(h_required)

    # 方法: 由于24个0-1变量, 且目标函数可以分解为每个时段独立的贡献,
    # 直接计算每个时段开机vs停机的边际成本, 然后选最优h个时段

    # 计算每个时段开机(x=1)和停机(x=0)时的净成本
    cost_on = np.zeros(24)   # 开机时的购电成本-售电收入
    cost_off = np.zeros(24)  # 停机时的购电成本-售电收入

    for t in range(24):
        # 停机: P_net = P_RE_surplus[t]
        P_net_off = P_RE_surplus[t]
        if P_net_off >= 0:
            cost_off[t] = -SELL_PRICE * P_net_off * 1000
        else:
            cost_off[t] = tou_prices[t] * (-P_net_off) * 1000

        # 开机: P_net = P_RE_surplus[t] - P_H2NH3
        P_net_on = P_RE_surplus[t] - P_H2NH3
        if P_net_on >= 0:
            cost_on[t] = -SELL_PRICE * P_net_on * 1000
        else:
            cost_on[t] = tou_prices[t] * (-P_net_on) * 1000

    # 开机的边际成本增量 = cost_on - cost_off
    marginal_cost = cost_on - cost_off

    # 贪心: 选边际成本最小的h个时段开机
    sorted_indices = np.argsort(marginal_cost)
    schedule = np.zeros(24, dtype=int)
    schedule[sorted_indices[:h]] = 1

    # 这个贪心解就是ILP的全局最优(因为目标函数可分解为独立时段)

    # 计算实际功率
    P_net = P_RE_surplus - schedule * P_H2NH3
    P_sell_arr = np.maximum(P_net, 0)
    P_buy_arr = np.maximum(-P_net, 0)

    P_total_load = P_load + schedule * P_H2NH3
    E_use = np.sum(P_total_load)
    E_RE = np.sum(P_wind + P_pv)
    E_buy = np.sum(P_buy_arr)
    E_sell = np.sum(P_sell_arr)

    r1, r2, r3 = calc_green_indicators(E_use, E_RE, E_buy, E_sell)

    C_ton, cost_detail = calc_ton_cost(
        P_buy_arr, P_sell_arr, P_wind, P_pv, P_H2NH3,
        h, Q_NH3, tou_prices, scale_factor
    )

    return {
        'schedule': schedule.tolist(),
        'on_hours': list(np.where(schedule == 1)[0]),
        'h_run': h,
        'Q_NH3': Q_NH3,
        'E_use': round(float(E_use), 2),
        'E_RE': round(float(E_RE), 2),
        'E_buy': round(float(E_buy), 2),
        'E_sell': round(float(E_sell), 2),
        'r1': round(float(r1), 2),
        'r2': round(float(r2), 2),
        'r3': round(float(r3), 2),
        'compliance': check_green_compliance(r1, r2, r3),
        'C_ton': round(float(C_ton), 2),
        'utilization': round(h / 24 * 100, 1),
        'cost_detail': {k: round(float(v), 2) for k, v in cost_detail.items()},
    }

    schedule = np.array([int(value(x[t])) for t in range(24)])
    P_buy_arr = np.array([value(P_buy_vars[t]) for t in range(24)])
    P_sell_arr = np.array([value(P_sell_vars[t]) for t in range(24)])

    P_total_load = P_load + schedule * P_H2NH3
    E_use = np.sum(P_total_load)
    E_RE = np.sum(P_wind + P_pv)
    E_buy = np.sum(P_buy_arr)
    E_sell = np.sum(P_sell_arr)

    r1, r2, r3 = calc_green_indicators(E_use, E_RE, E_buy, E_sell)

    C_ton, cost_detail = calc_ton_cost(
        P_buy_arr, P_sell_arr, P_wind, P_pv, P_H2NH3,
        h, Q_NH3, tou_prices, scale_factor
    )

    return {
        'schedule': schedule.tolist(),
        'on_hours': list(np.where(schedule == 1)[0]),
        'h_run': h,
        'Q_NH3': Q_NH3,
        'E_use': round(float(E_use), 2),
        'E_RE': round(float(E_RE), 2),
        'E_buy': round(float(E_buy), 2),
        'E_sell': round(float(E_sell), 2),
        'r1': round(float(r1), 2),
        'r2': round(float(r2), 2),
        'r3': round(float(r3), 2),
        'compliance': check_green_compliance(r1, r2, r3),
        'C_ton': round(float(C_ton), 2),
        'utilization': round(h / 24 * 100, 1),
        'cost_detail': {k: round(float(v), 2) for k, v in cost_detail.items()},
    }


def solve_problem2():
    print("=" * 60)
    print("问题二：基于离散制氨调节的运行优化")
    print("=" * 60)

    data = load_data()
    tou_prices = data['tou_prices']
    scale_factor = 2.0
    P_H2NH3 = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor  # 41.5 MW

    print(f"\n产能扩容: 72吨/日, 倍数={scale_factor}")
    print(f"制氢氨总负荷: {P_H2NH3:.1f} MW")

    quantities = [72, 63, 54, 45, 36]

    # ===== 子问题(1): 典型场景 =====
    print(f"\n{'='*40}")
    print("子问题(1): 典型风光场景下各产量最优方案")
    print(f"{'='*40}")

    wind_pu = data['wind_typical_pu']
    pv_pu = data['pv_typical_pu']
    P_wind = wind_pu * P_WIND_CAP
    P_pv = pv_pu * P_PV_CAP
    P_load = data['load_pu'] * P_LOAD_PEAK
    P_RE_surplus = P_wind + P_pv - P_load

    typical_results = {}
    best_cost = float('inf')
    best_Q = None

    for Q in quantities:
        h = Q / 3.0
        result = solve_ilp_single(P_RE_surplus, tou_prices, P_H2NH3, h, Q,
                                  P_wind, P_pv, P_load, scale_factor)
        if result:
            typical_results[str(Q)] = result
            print(f"\n  产量 {Q}吨/日 (运行{int(h)}h):")
            print(f"    开机时段: {result['on_hours']}")
            print(f"    r1={result['r1']:.1f}%, r2={result['r2']:.1f}%, r3={result['r3']:.1f}%")
            print(f"    合规: {result['compliance']}")
            print(f"    吨氨成本: {result['C_ton']:.2f} 元/吨")
            print(f"    设备利用率: {result['utilization']}%")

            if result['C_ton'] < best_cost:
                best_cost = result['C_ton']
                best_Q = Q

    print(f"\n  >>> 最低吨氨成本: {best_cost:.2f} 元/吨 (产量={best_Q}吨/日)")
    best_result = typical_results[str(best_Q)]
    print(f"  >>> 绿电指标: r1={best_result['r1']:.1f}%, r2={best_result['r2']:.1f}%, r3={best_result['r3']:.1f}%")
    print(f"  >>> 合规状态: {best_result['compliance']}, 利用率: {best_result['utilization']}%")

    # ===== 子问题(2): 24种场景全年分析 =====
    print(f"\n{'='*40}")
    print("子问题(2): 24种风光场景全年分析")
    print(f"{'='*40}")

    all_scenarios_results = {}

    for Q in quantities:
        h = Q / 3.0
        scenario_results = []

        for wi in range(6):
            for pi in range(4):
                scenario_id = f"W{wi+1}_P{pi+1}"
                P_wind_s = data['wind_scenarios'][:, wi] * P_WIND_CAP
                P_pv_s = data['pv_scenarios'][:, pi] * P_PV_CAP
                P_RE_surplus_s = P_wind_s + P_pv_s - P_load

                result = solve_ilp_single(P_RE_surplus_s, tou_prices, P_H2NH3, h, Q,
                                         P_wind_s, P_pv_s, P_load, scale_factor)
                if result:
                    result['scenario'] = scenario_id
                    scenario_results.append(result)

        all_scenarios_results[str(Q)] = scenario_results

        costs = [r['C_ton'] for r in scenario_results]
        compliances = [r['compliance'] for r in scenario_results]
        n_all_pass = compliances.count('all_pass')
        n_partial = compliances.count('partial')
        n_all_fail = compliances.count('all_fail')

        print(f"\n  产量 {Q}吨/日:")
        print(f"    吨氨成本: 均值={np.mean(costs):.2f}, 最小={np.min(costs):.2f}, 最大={np.max(costs):.2f}")
        print(f"    绿电指标: 全满足={n_all_pass}, 部分满足={n_partial}, 全不满足={n_all_fail}")

    # 全年吨氨成本
    print(f"\n{'='*40}")
    print("全年吨氨成本分析")
    print(f"{'='*40}")

    annual_costs_by_Q = {}
    for Q in quantities:
        costs = [r['C_ton'] for r in all_scenarios_results[str(Q)]]
        annual_cost = np.mean(costs)
        annual_costs_by_Q[Q] = annual_cost
        print(f"  产量{Q}吨/日: 全年平均吨氨成本 = {annual_cost:.2f} 元/吨")

    best_annual_Q = min(annual_costs_by_Q, key=annual_costs_by_Q.get)
    print(f"\n  >>> 全年最优产量: {best_annual_Q}吨/日, 成本={annual_costs_by_Q[best_annual_Q]:.2f} 元/吨")

    best_Q_results = all_scenarios_results[str(best_annual_Q)]
    n_all = sum(1 for r in best_Q_results if r['compliance'] == 'all_pass')
    n_partial = sum(1 for r in best_Q_results if r['compliance'] == 'partial')
    n_fail = sum(1 for r in best_Q_results if r['compliance'] == 'all_fail')
    print(f"  全年绿电指标(产量{best_annual_Q}): 全满足={n_all}x15={n_all*15}天, "
          f"部分满足={n_partial}x15={n_partial*15}天, 全不满足={n_fail}x15={n_fail*15}天")

    # 保存结果
    results = {
        'typical_scenario': typical_results,
        'best_typical': {
            'Q_NH3': best_Q,
            'C_ton': best_cost,
            'compliance': typical_results[str(best_Q)]['compliance'],
            'utilization': typical_results[str(best_Q)]['utilization'],
        },
        'all_scenarios': {
            str(Q): {
                'costs': [r['C_ton'] for r in all_scenarios_results[str(Q)]],
                'r1_values': [r['r1'] for r in all_scenarios_results[str(Q)]],
                'r2_values': [r['r2'] for r in all_scenarios_results[str(Q)]],
                'r3_values': [r['r3'] for r in all_scenarios_results[str(Q)]],
                'compliances': [r['compliance'] for r in all_scenarios_results[str(Q)]],
                'mean_cost': round(float(np.mean([r['C_ton'] for r in all_scenarios_results[str(Q)]])), 2),
                'min_cost': round(float(np.min([r['C_ton'] for r in all_scenarios_results[str(Q)]])), 2),
                'max_cost': round(float(np.max([r['C_ton'] for r in all_scenarios_results[str(Q)]])), 2),
                'n_all_pass': sum(1 for r in all_scenarios_results[str(Q)] if r['compliance'] == 'all_pass'),
                'n_partial': sum(1 for r in all_scenarios_results[str(Q)] if r['compliance'] == 'partial'),
                'n_all_fail': sum(1 for r in all_scenarios_results[str(Q)] if r['compliance'] == 'all_fail'),
            }
            for Q in quantities
        },
        'annual_analysis': {
            'best_Q': best_annual_Q,
            'annual_costs_by_Q': {str(k): round(float(v), 2) for k, v in annual_costs_by_Q.items()},
            'green_stats': {
                'all_pass_days': n_all * 15,
                'partial_days': n_partial * 15,
                'all_fail_days': n_fail * 15,
            },
        },
        'cost_distribution': {
            str(Q): [r['C_ton'] for r in all_scenarios_results[str(Q)]]
            for Q in quantities
        },
    }

    save_json(results, 'figures/problem_2_results.json')
    print("\n✅ 问题二求解完成")
    return results


if __name__ == '__main__':
    results = solve_problem2()
