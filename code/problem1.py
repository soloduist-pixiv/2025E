"""问题一：典型风光场景下的绿电直连电氢氨园区运行指标分析"""
import numpy as np
import sys
sys.path.insert(0, 'code')
from utils import *

def solve_problem1():
    print("=" * 60)
    print("问题一：典型风光场景下运行指标分析")
    print("=" * 60)
    
    # 读取数据
    data = load_data()
    wind_pu = data['wind_typical_pu']
    pv_pu = data['pv_typical_pu']
    tou_prices = data['tou_prices']
    
    # 计算实际功率 (满负荷运行, scale_factor=1)
    powers = calc_actual_power(data, wind_pu, pv_pu, scale_factor=1.0)
    P_wind = powers['P_wind']
    P_pv = powers['P_pv']
    P_load = powers['P_load']
    P_H2NH3 = powers['P_H2NH3']  # 20.75 MW
    
    print(f"\n设备参数:")
    print(f"  ALKEL: {P_ALKEL_BASE} MW, PEMEL: {P_PEMEL_BASE} MW, NH3: {P_NH3_BASE} MW")
    print(f"  制氢氨总负荷: {P_H2NH3:.2f} MW")
    print(f"  风电装机: {P_WIND_CAP} MW, 光伏装机: {P_PV_CAP} MW")
    print(f"  常规负荷峰值: {P_LOAD_PEAK} MW")
    
    # (1) 逐时段功率平衡计算
    # 总用电负荷 = 常规负荷 + 制氢氨负荷(满负荷24h)
    P_total_load = P_load + P_H2NH3  # (24,)
    
    # 风光总发电
    P_RE = P_wind + P_pv  # (24,)
    
    # 净功率 (正=余电, 负=缺电)
    P_net = P_RE - P_total_load  # (24,)
    
    # 购电/售电
    P_sell = np.maximum(P_net, 0)
    P_buy = np.maximum(-P_net, 0)
    
    # (2) 能量指标计算 (每时段1h)
    E_use = np.sum(P_total_load) * 1  # MWh
    E_RE = np.sum(P_RE) * 1           # MWh
    E_buy = np.sum(P_buy) * 1         # MWh
    E_sell = np.sum(P_sell) * 1       # MWh
    
    # 能量守恒验证
    balance_err = abs(E_RE + E_buy - E_use - E_sell)
    print(f"\n能量守恒验证: |E_RE + E_buy - E_use - E_sell| = {balance_err:.6f} MWh")
    assert balance_err < 0.01, f"能量不守恒! 误差={balance_err}"
    
    # 绿电指标
    r1, r2, r3 = calc_green_indicators(E_use, E_RE, E_buy, E_sell)
    
    print(f"\n=== 问题一(1) 功率计算结果 ===")
    print(f"  风电日发电量: {np.sum(P_wind):.2f} MWh")
    print(f"  光伏日发电量: {np.sum(P_pv):.2f} MWh")
    print(f"  新能源总发电量 E_RE: {E_RE:.2f} MWh")
    print(f"  园区总用电量 E_use: {E_use:.2f} MWh")
    print(f"  网购电量 E_buy: {E_buy:.2f} MWh")
    print(f"  上网电量 E_sell: {E_sell:.2f} MWh")
    
    print(f"\n=== 问题一(2) 绿电直连指标 ===")
    print(f"  r1 (自发自用比例): {r1:.2f}% {'✅>60%' if r1>60 else '❌<60%'}")
    print(f"  r2 (绿电比例): {r2:.2f}% {'✅>30%' if r2>30 else '❌<30%'}")
    print(f"  r3 (上网电量比例): {r3:.2f}% {'✅<20%' if r3<20 else '❌>20%'}")
    
    # 吨氨成本
    Q_NH3 = Q_NH3_BASE  # 36吨/日
    h_run = 24  # 满负荷24h
    C_ton, cost_detail = calc_ton_cost(
        P_buy, P_sell, P_wind, P_pv, P_H2NH3,
        h_run, Q_NH3, tou_prices, scale_factor=1.0
    )
    
    print(f"\n=== 吨氨成本分析 ===")
    print(f"  购电成本: {cost_detail['C_buy']:.2f} 元")
    print(f"  售电收入: {cost_detail['R_sell']:.2f} 元")
    print(f"  风光度电成本: {cost_detail['C_RE']:.2f} 元")
    print(f"  制氢运维: {cost_detail['C_OM_H2']:.2f} 元")
    print(f"  合成氨运维: {cost_detail['C_OM_NH3']:.2f} 元")
    print(f"  合成氨折旧: {cost_detail['C_dep_NH3']:.2f} 元")
    print(f"  总成本: {cost_detail['total_cost']:.2f} 元")
    print(f"  吨氨成本: {C_ton:.2f} 元/吨")
    
    # 不满足指标的原因分析
    print(f"\n=== 指标不满足原因分析 ===")
    if r1 <= 60:
        print(f"  r1不满足: 风光出力集中在白天(光伏仅6:00-18:00有出力),")
        print(f"  而制氢氨负荷全天均匀运行, 夜间必须大量购电, 导致自发自用比例低")
    if r3 >= 20:
        print(f"  r3不满足: 白天风光出力高峰时段(10:00-15:00)发电远超负荷,")
        print(f"  大量余电上网, 导致上网比例过高")
    
    # 保存结果
    results = {
        'power_curves': {
            'P_wind': P_wind.tolist(),
            'P_pv': P_pv.tolist(),
            'P_load': P_load.tolist(),
            'P_H2NH3': float(P_H2NH3),
            'P_total_load': P_total_load.tolist(),
            'P_RE': P_RE.tolist(),
            'P_net': P_net.tolist(),
            'P_buy': P_buy.tolist(),
            'P_sell': P_sell.tolist(),
        },
        'energy_indicators': {
            'E_use': round(E_use, 2),
            'E_RE': round(E_RE, 2),
            'E_buy': round(E_buy, 2),
            'E_sell': round(E_sell, 2),
            'E_wind': round(float(np.sum(P_wind)), 2),
            'E_pv': round(float(np.sum(P_pv)), 2),
        },
        'green_indicators': {
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            'r3': round(r3, 2),
            'r1_pass': bool(r1 > 60),
            'r2_pass': bool(r2 > 30),
            'r3_pass': bool(r3 < 20),
            'compliance': check_green_compliance(r1, r2, r3),
        },
        'cost': {
            'C_ton': round(C_ton, 2),
            'C_buy': round(cost_detail['C_buy'], 2),
            'R_sell': round(cost_detail['R_sell'], 2),
            'C_RE': round(cost_detail['C_RE'], 2),
            'C_OM_H2': round(cost_detail['C_OM_H2'], 2),
            'C_OM_NH3': round(cost_detail['C_OM_NH3'], 2),
            'C_dep_NH3': round(cost_detail['C_dep_NH3'], 2),
            'total_cost': round(cost_detail['total_cost'], 2),
            'Q_NH3': Q_NH3,
        },
    }
    
    save_json(results, 'figures/problem_1_results.json')
    
    # 约束验证
    constraints = {
        'r1': (0, 100, '自发自用比例(%)'),
        'r2': (0, 100, '绿电比例(%)'),
        'r3': (0, 100, '上网电量比例(%)'),
    }
    results_check = {'r1': r1, 'r2': r2, 'r3': r3}
    violations = []
    for key, (lo, hi, desc) in constraints.items():
        val = results_check[key]
        if val < lo or val > hi:
            violations.append(f"❌ {desc}: {val:.2f} 超出范围 [{lo}, {hi}]")
    if violations:
        for v in violations:
            print(v)
        raise ValueError("约束验证失败")
    else:
        print("\n✅ 约束验证通过")
    
    return results


if __name__ == '__main__':
    results = solve_problem1()
