"""问题三：基于连续制氨调节的绿电直连型电氢氨园区运行分析"""
import numpy as np
from scipy.optimize import linprog
import sys
sys.path.insert(0, 'code')
from utils import *


def solve_lp_continuous(P_wind, P_pv, P_load, tou_prices, P_H2NH3, h_target, Q_NH3, scale_factor):
    """求解连续调节LP问题
    由于给定alpha后P_buy和P_sell由互补条件唯一确定,
    目标函数是alpha的分段线性函数。

    使用标准LP技巧: 引入P_buy和P_sell但加互补约束的等价形式。
    关键: 对于最小化问题, 如果buy_price > sell_price (始终成立),
    则优化器不会同时选择buy和sell, 互补自动满足。

    但如果sell_price > buy_price(某些时段), 需要显式处理。
    这里sell_price=0.3779 < 所有buy_price(0.3424/0.6074/0.8024),
    除了低谷时段0.3424 < 0.3779! 这导致低谷时段可以"套利"。

    修正方案: 用分段线性目标函数, 只用alpha作为决策变量。
    """
    n = 24
    P_RE = P_wind + P_pv

    # 方法: 将目标函数写成alpha的分段线性函数
    # P_net(t) = P_RE(t) - P_load(t) - alpha(t)*P_H2NH3
    # 当P_net(t) >= 0: cost(t) = -sell_price * P_net(t) * 1000
    # 当P_net(t) < 0: cost(t) = buy_price(t) * (-P_net(t)) * 1000

    # 定义: surplus(t) = P_RE(t) - P_load(t) (不含制氢氨负荷的余电)
    # P_net(t) = surplus(t) - alpha(t)*P_H2NH3
    # 临界点: alpha_crit(t) = surplus(t) / P_H2NH3

    surplus = P_RE - P_load
    alpha_crit = surplus / P_H2NH3  # 临界alpha值

    # 使用LP标准形式: 引入辅助变量处理分段线性
    # 对每个时段t, 定义:
    #   P_buy(t) >= surplus(t) - alpha(t)*P_H2NH3 的负部分
    #   P_sell(t) >= surplus(t) - alpha(t)*P_H2NH3 的正部分
    # 但需要互补约束。

    # 正确的LP形式(利用buy_price >= sell_price的性质):
    # 当buy_price(t) >= sell_price时, 互补自动满足
    # 当buy_price(t) < sell_price时(低谷时段), 需要额外处理

    # 实际上对于本题: 低谷电价0.3424 < 售电价0.3779
    # 这意味着低谷时段如果同时购电和售电可以套利
    # 但物理上不允许! 必须加互补约束。

    # 最简方案: 由于alpha确定后P_net确定, 直接用非线性优化
    # 但为保持LP, 用大M法加互补约束

    # 更好的方案: 分段线性LP
    # 对每个时段, cost(t) = max(buy_price(t), sell_price) * |P_net(t)| 的某种形式
    # 实际上: cost(t) = buy_price(t) * max(-P_net(t), 0) - sell_price * max(P_net(t), 0)

    # 用标准LP技巧: P_net(t) = u(t) - v(t), u(t)>=0, v(t)>=0
    # cost(t) = buy_price(t)*v(t) - sell_price*u(t)
    # 当buy_price > sell_price时, 优化器自动让u*v=0
    # 当buy_price < sell_price时, 需要加约束

    # 对低谷时段(buy_price=0.3424 < sell_price=0.3779):
    # 加二进制变量约束太复杂。
    # 简化: 直接用scipy.optimize.minimize (SLSQP) 求解非线性问题

    # 最终方案: 由于alpha确定后成本确定, 用scipy的linprog但正确建模
    # 技巧: 将P_sell的系数改为 -min(sell_price, buy_price(t))
    # 这样即使低谷时段也不会套利

    # 实际最简方案: 直接枚举alpha的分段线性结构
    # 由于目标函数关于alpha是凸的(分段线性), 用LP求解

    # 正确LP建模(避免套利):
    # 变量: alpha(1..24), P_pos(1..24), P_neg(1..24)
    # P_pos(t) = max(P_net(t), 0), P_neg(t) = max(-P_net(t), 0)
    # P_net(t) = P_pos(t) - P_neg(t)
    # surplus(t) - alpha(t)*P_H2NH3 = P_pos(t) - P_neg(t)
    # P_pos(t) >= 0, P_neg(t) >= 0
    # 目标: min sum(buy_price(t)*P_neg(t) - sell_price*P_pos(t)) * 1000
    # 当buy_price(t) > sell_price: 自动互补
    # 当buy_price(t) < sell_price: 不自动互补!

    # 对低谷时段的处理: 由于物理上不能同时购售电,
    # 且P_net是确定的(给定alpha), P_pos和P_neg不能同时>0
    # 加约束: P_pos(t) + P_neg(t) = |P_net(t)| = |surplus(t) - alpha(t)*P_H2NH3|
    # 但这是非线性的...

    # 最终采用: scipy.optimize.minimize with bounds
    from scipy.optimize import minimize, LinearConstraint

    def objective(alpha_vec):
        P_net_vec = surplus - alpha_vec * P_H2NH3
        P_sell_vec = np.maximum(P_net_vec, 0)
        P_buy_vec = np.maximum(-P_net_vec, 0)
        cost = np.sum(tou_prices * P_buy_vec * 1000) - np.sum(SELL_PRICE * P_sell_vec * 1000)
        return cost

    # 约束: sum(alpha) = h_target
    constraints = [{'type': 'eq', 'fun': lambda a: np.sum(a) - h_target}]
    bounds_alpha = [(0, 1)] * n

    # 初始解: 均匀分配
    alpha0 = np.full(n, h_target / n)
    alpha0 = np.clip(alpha0, 0, 1)

    # 用SLSQP求解(目标函数是凸的分段线性, SLSQP可以处理)
    res = minimize(objective, alpha0, method='SLSQP', bounds=bounds_alpha,
                   constraints=constraints, options={'maxiter': 1000, 'ftol': 1e-10})

    if not res.success and abs(np.sum(res.x) - h_target) > 0.01:
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

    # 计算结果
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

    C_ton, cost_detail = calc_ton_cost(
        P_buy_arr, P_sell_arr, P_wind, P_pv, P_H2NH3,
        h_actual, Q_NH3, tou_prices, scale_factor
    )

    return {
        'alpha': alpha.tolist(),
        'h_actual': round(float(h_actual), 2),
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
        'P_buy': P_buy_arr.tolist(),
        'P_sell': P_sell_arr.tolist(),
        'cost_detail': {k: round(float(v), 2) for k, v in cost_detail.items()},
    }


def solve_problem3():
    print("=" * 60)
    print("问题三：基于连续制氨调节的运行优化")
    print("=" * 60)

    data = load_data()
    tou_prices = data['tou_prices']
    scale_factor = 2.0
    P_H2NH3 = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor  # 41.5 MW
    P_load = data['load_pu'] * P_LOAD_PEAK

    quantities = [72, 63, 54, 45, 36]

    # ===== 子问题(1): 24种场景最优调度 =====
    print(f"\n{'='*40}")
    print("子问题(1): 24种场景最优调度方案")
    print(f"{'='*40}")

    all_results = {}

    for Q in quantities:
        h_target = Q / 3.0
        scenario_results = []

        for wi in range(6):
            for pi in range(4):
                scenario_id = f"W{wi+1}_P{pi+1}"
                P_wind_s = data['wind_scenarios'][:, wi] * P_WIND_CAP
                P_pv_s = data['pv_scenarios'][:, pi] * P_PV_CAP

                result = solve_lp_continuous(
                    P_wind_s, P_pv_s, P_load, tou_prices,
                    P_H2NH3, h_target, Q, scale_factor
                )
                if result:
                    result['scenario'] = scenario_id
                    scenario_results.append(result)

        all_results[str(Q)] = scenario_results

        costs = [r['C_ton'] for r in scenario_results]
        compliances = [r['compliance'] for r in scenario_results]
        n_all_pass = compliances.count('all_pass')
        n_partial = compliances.count('partial')
        n_all_fail = compliances.count('all_fail')

        print(f"\n  产量 {Q}吨/日:")
        print(f"    吨氨成本: 均值={np.mean(costs):.2f}, 最小={np.min(costs):.2f}, 最大={np.max(costs):.2f}")
        print(f"    绿电指标: 全满足={n_all_pass}, 部分满足={n_partial}, 全不满足={n_all_fail}")

    # 全年统计
    print(f"\n{'='*40}")
    print("全年吨氨成本分析")
    print(f"{'='*40}")

    annual_costs_by_Q = {}
    for Q in quantities:
        costs = [r['C_ton'] for r in all_results[str(Q)]]
        annual_cost = np.mean(costs)
        annual_costs_by_Q[Q] = annual_cost
        print(f"  产量{Q}吨/日: 全年平均吨氨成本 = {annual_cost:.2f} 元/吨")

    best_annual_Q = min(annual_costs_by_Q, key=annual_costs_by_Q.get)
    print(f"\n  >>> 全年最优产量: {best_annual_Q}吨/日, 成本={annual_costs_by_Q[best_annual_Q]:.2f} 元/吨")

    best_Q_results = all_results[str(best_annual_Q)]
    n_all = sum(1 for r in best_Q_results if r['compliance'] == 'all_pass')
    n_partial = sum(1 for r in best_Q_results if r['compliance'] == 'partial')
    n_fail = sum(1 for r in best_Q_results if r['compliance'] == 'all_fail')
    print(f"  全年绿电指标(产量{best_annual_Q}): 全满足={n_all}x15={n_all*15}天, "
          f"部分满足={n_partial}x15={n_partial*15}天, 全不满足={n_fail}x15={n_fail*15}天")

    # ===== 子问题(3): 与问题二对比 =====
    print(f"\n{'='*40}")
    print("子问题(3): 与问题二对比")
    print(f"{'='*40}")

    import json
    with open('figures/problem_2_results.json', 'r', encoding='utf-8') as f:
        q2_results = json.load(f)

    comparison = {}
    for Q in quantities:
        q2_cost = q2_results['all_scenarios'][str(Q)]['mean_cost']
        q3_cost = annual_costs_by_Q[Q]
        improvement = (q2_cost - q3_cost) / q2_cost * 100
        comparison[str(Q)] = {
            'Q2_cost': q2_cost,
            'Q3_cost': round(q3_cost, 2),
            'improvement_pct': round(improvement, 2),
        }
        print(f"  产量{Q}吨/日: Q2={q2_cost:.2f}, Q3={q3_cost:.2f}, 改善={improvement:.2f}%")

    # 保存结果
    results = {
        'all_scenarios': {
            str(Q): {
                'costs': [r['C_ton'] for r in all_results[str(Q)]],
                'r1_values': [r['r1'] for r in all_results[str(Q)]],
                'r2_values': [r['r2'] for r in all_results[str(Q)]],
                'r3_values': [r['r3'] for r in all_results[str(Q)]],
                'compliances': [r['compliance'] for r in all_results[str(Q)]],
                'mean_cost': round(float(np.mean([r['C_ton'] for r in all_results[str(Q)]])), 2),
                'min_cost': round(float(np.min([r['C_ton'] for r in all_results[str(Q)]])), 2),
                'max_cost': round(float(np.max([r['C_ton'] for r in all_results[str(Q)]])), 2),
                'n_all_pass': sum(1 for r in all_results[str(Q)] if r['compliance'] == 'all_pass'),
                'n_partial': sum(1 for r in all_results[str(Q)] if r['compliance'] == 'partial'),
                'n_all_fail': sum(1 for r in all_results[str(Q)] if r['compliance'] == 'all_fail'),
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
        'comparison_with_q2': comparison,
        'cost_distribution': {
            str(Q): [r['C_ton'] for r in all_results[str(Q)]]
            for Q in quantities
        },
        'sample_alpha_profiles': {
            str(Q): all_results[str(Q)][0]['alpha'] if all_results[str(Q)] else []
            for Q in quantities
        },
    }

    save_json(results, 'figures/problem_3_results.json')

    # 验证: 连续调节应不劣于离散调节
    print(f"\n{'='*40}")
    print("交叉验证: Q3 <= Q2 (连续不劣于离散)")
    print(f"{'='*40}")
    all_pass = True
    for Q in quantities:
        q2_cost = q2_results['all_scenarios'][str(Q)]['mean_cost']
        q3_cost = annual_costs_by_Q[Q]
        if q3_cost > q2_cost * 1.01:  # 允许1%数值误差
            print(f"  ❌ 产量{Q}: Q3({q3_cost:.2f}) > Q2({q2_cost:.2f})")
            all_pass = False
        else:
            print(f"  ✅ 产量{Q}: Q3({q3_cost:.2f}) <= Q2({q2_cost:.2f})")

    if all_pass:
        print("\n✅ 问题三求解完成, 资源单调性验证通过")
    else:
        print("\n⚠ 部分产量下连续调节未优于离散调节, 需检查")

    return results


if __name__ == '__main__':
    results = solve_problem3()
