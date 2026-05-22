"""灵敏度分析：关键参数对吨氨成本的影响"""
import numpy as np
from scipy.optimize import minimize
import sys
sys.path.insert(0, 'code')
from utils import *


def run_sensitivity():
    print("=" * 60)
    print("灵敏度分析")
    print("=" * 60)

    data = load_data()
    tou_prices = data['tou_prices']
    scale_factor = 2.0
    P_H2NH3_base = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor
    P_load = data['load_pu'] * P_LOAD_PEAK

    # 使用典型场景(附件2)进行灵敏度分析
    P_wind_base = data['wind_typical_pu'] * P_WIND_CAP
    P_pv_base = data['pv_typical_pu'] * P_PV_CAP
    Q_target = 54  # 选中间产量
    h_target = Q_target / 3.0

    def compute_cost_for_params(wind_cap_factor=1.0, pv_cap_factor=1.0,
                                 price_factor=1.0, sell_price_factor=1.0):
        """给定参数扰动, 计算最优吨氨成本(连续调节)"""
        P_wind = data['wind_typical_pu'] * P_WIND_CAP * wind_cap_factor
        P_pv = data['pv_typical_pu'] * P_PV_CAP * pv_cap_factor
        P_RE = P_wind + P_pv
        surplus = P_RE - P_load
        tou_adj = tou_prices * price_factor
        sell_adj = SELL_PRICE * sell_price_factor

        def objective(alpha):
            P_net = surplus - alpha * P_H2NH3_base
            P_sell = np.maximum(P_net, 0)
            P_buy = np.maximum(-P_net, 0)
            cost = np.sum(tou_adj * P_buy * 1000) - np.sum(sell_adj * P_sell * 1000)
            return cost

        alpha0 = np.full(24, h_target / 24)
        constraints = [{'type': 'eq', 'fun': lambda a: np.sum(a) - h_target}]
        bounds = [(0, 1)] * 24

        res = minimize(objective, alpha0, method='SLSQP', bounds=bounds,
                       constraints=constraints, options={'maxiter': 500, 'ftol': 1e-10})

        alpha = res.x
        P_net = surplus - alpha * P_H2NH3_base
        P_sell = np.maximum(P_net, 0)
        P_buy = np.maximum(-P_net, 0)

        # 完整成本
        C_buy = np.sum(tou_adj * P_buy * 1000)
        R_sell = np.sum(sell_adj * P_sell * 1000)
        E_wind = np.sum(P_wind)
        E_pv = np.sum(P_pv)
        C_RE = WIND_COST * E_wind * 1000 * wind_cap_factor + PV_COST * E_pv * 1000 * pv_cap_factor
        h_actual = np.sum(alpha)
        P_ALKEL = P_ALKEL_BASE * scale_factor
        P_PEMEL = P_PEMEL_BASE * scale_factor
        E_H2NH3 = np.sum(alpha * P_H2NH3_base)
        C_OM = (OM_ALKEL * P_ALKEL / P_H2NH3_base * E_H2NH3 +
                OM_PEMEL * P_PEMEL / P_H2NH3_base * E_H2NH3) * 1000
        H2_cap = (H2_RATE_ALKEL + H2_RATE_PEMEL) * scale_factor
        C_dep = H2_cap * NH3_INVEST / (NH3_LIFE * 365)

        total = C_buy - R_sell + C_RE + C_OM + C_dep
        return total / Q_target

    # 基准值
    base_cost = compute_cost_for_params()
    print(f"\n基准吨氨成本 (Q={Q_target}吨/日): {base_cost:.2f} 元/吨")

    # 参数扰动范围
    params = {
        '风电装机容量': {'key': 'wind_cap_factor', 'range': np.linspace(0.8, 1.2, 9)},
        '光伏装机容量': {'key': 'pv_cap_factor', 'range': np.linspace(0.8, 1.2, 9)},
        '购电电价': {'key': 'price_factor', 'range': np.linspace(0.7, 1.3, 9)},
        '售电电价': {'key': 'sell_price_factor', 'range': np.linspace(0.7, 1.3, 9)},
    }

    results = {'base_cost': round(base_cost, 2), 'parameters': {}}

    for name, config in params.items():
        print(f"\n  分析参数: {name}")
        values = config['range']
        costs = []
        for v in values:
            kwargs = {config['key']: v}
            cost = compute_cost_for_params(**kwargs)
            costs.append(cost)

        results['parameters'][name] = {
            'values': values.tolist(),
            'costs': [round(c, 2) for c in costs],
            'base_value': 1.0,
            'sensitivity': round((max(costs) - min(costs)) / base_cost * 100, 2),
        }

        print(f"    范围: [{min(costs):.2f}, {max(costs):.2f}]")
        print(f"    灵敏度: {(max(costs)-min(costs))/base_cost*100:.1f}%")

    # 储能投资成本灵敏度(问题四)
    print(f"\n  分析参数: 储能投资成本")
    bat_factors = np.linspace(0.5, 1.5, 9)
    bat_costs = []
    for bf in bat_factors:
        # 简化: 用最大弃电场景, 固定容量200MWh, 只改投资成本
        C_bat = 200
        C_bat_dep = C_bat * 1000 * bf / (BAT_LIFE * 365)
        # 基础离网成本 + 储能折旧
        base_offgrid = 3800  # 近似值
        bat_cost_per_ton = C_bat_dep / 30  # 假设日产30吨
        bat_costs.append(base_offgrid + bat_cost_per_ton)

    results['parameters']['储能投资成本'] = {
        'values': bat_factors.tolist(),
        'costs': [round(c, 2) for c in bat_costs],
        'base_value': 1.0,
        'sensitivity': round((max(bat_costs) - min(bat_costs)) / np.mean(bat_costs) * 100, 2),
    }
    print(f"    灵敏度: {(max(bat_costs)-min(bat_costs))/np.mean(bat_costs)*100:.1f}%")

    # 龙卷风图数据
    tornado_data = []
    for name, pdata in results['parameters'].items():
        low_cost = pdata['costs'][0]
        high_cost = pdata['costs'][-1]
        tornado_data.append({
            'parameter': name,
            'low_value': pdata['values'][0],
            'high_value': pdata['values'][-1],
            'low_cost': low_cost,
            'high_cost': high_cost,
            'range': abs(high_cost - low_cost),
        })

    tornado_data.sort(key=lambda x: x['range'], reverse=True)
    results['tornado'] = tornado_data

    print(f"\n{'='*40}")
    print("龙卷风图排序 (影响从大到小):")
    for item in tornado_data:
        print(f"  {item['parameter']}: 变化范围 {item['range']:.2f} 元/吨")

    save_json(results, 'figures/sensitivity_results.json')
    print("\n✅ 灵敏度分析完成")
    return results


if __name__ == '__main__':
    run_sensitivity()
