"""公共工具模块：数据读取、参数定义、指标计算"""
import numpy as np
import pandas as pd
import json
import os

# ===== 基准设备参数（产能36吨/日）=====
P_ALKEL_BASE = 10.0    # MW, 碱性电解槽额定功率
P_PEMEL_BASE = 10.0    # MW, 质子交换膜电解槽额定功率
P_NH3_BASE = 0.75      # MW, 合成氨装置额定功率
P_LOAD_PEAK = 6.0      # MW, 常规电负荷峰值
P_WIND_CAP = 40.0      # MW, 风电装机容量
P_PV_CAP = 64.0        # MW, 光伏装机容量
Q_NH3_BASE = 36.0      # 吨/日, 基准产氨量
Q_NH3_RATE = 1.5       # 吨/h, 基准产氨速率
H2_RATE_ALKEL = 140.0  # kg/h, 碱性电解槽产氢速率
H2_RATE_PEMEL = 160.0  # kg/h, 质子交换膜电解槽产氢速率

# 经济参数
SELL_PRICE = 0.3779    # 元/kWh, 余电上网电价
WIND_COST = 0.15       # 元/kWh, 风电度电成本(含折旧)
PV_COST = 0.12         # 元/kWh, 光伏度电成本(含折旧)
OM_ALKEL = 0.1         # 元/kWh, 碱性电解槽运维系数
OM_PEMEL = 0.15        # 元/kWh, 质子交换膜电解槽运维系数
OM_NH3 = 0.002         # 元/kWh, 合成氨运维系数
NH3_INVEST = 60000.0   # 元/kgH2, 合成氨装置投资成本
NH3_LIFE = 30          # 年, 合成氨装置使用寿命
BAT_INVEST = 1000.0    # 元/kWh, 储能投资成本
BAT_LIFE = 15          # 年, 储能使用寿命
BAT_OM = 0.01          # 元/kWh, 储能运维系数
BAT_ETA_CH = 0.9       # 储能充电效率
BAT_ETA_DIS = 0.9      # 储能放电效率
BAT_SIGMA = 0.002      # /h, 储能自损耗率
DAYS_PER_SCENARIO = 15 # 每种场景代表天数

# 分时电价映射 (t=1..24 对应 0:00-1:00 到 23:00-24:00)
def get_tou_prices():
    """返回24时段的分时电价数组 (元/kWh)"""
    prices = np.zeros(24)
    # 低谷: 23:00-次日07:00 -> t=24(23:00-0:00), t=1~7(0:00-7:00)
    prices[0:7] = 0.3424   # t=1~7
    prices[23] = 0.3424    # t=24
    # 平时: 07:00-10:00, 15:00-18:00, 21:00-23:00
    prices[7:10] = 0.6074  # t=8~10
    prices[15:18] = 0.6074 # t=16~18
    prices[21:23] = 0.6074 # t=22~23
    # 高峰: 10:00-15:00, 18:00-21:00
    prices[10:15] = 0.8024 # t=11~15
    prices[18:21] = 0.8024 # t=19~21
    return prices


def load_data(data_dir='user_data'):
    """读取所有附件数据"""
    data = {}
    
    # 附件1: 常规电负荷标幺功率
    df1 = pd.read_excel(os.path.join(data_dir, '附件1：园区典型日常规电负荷标幺功率曲线.xlsx'))
    data['load_pu'] = df1.iloc[:, 1].values  # 24个时段标幺值
    
    # 附件2: 典型日风电、光伏标幺功率
    df2 = pd.read_excel(os.path.join(data_dir, '附件2：典型日风电、光伏标幺功率表.xlsx'))
    data['wind_typical_pu'] = df2.iloc[:, 1].values
    data['pv_typical_pu'] = df2.iloc[:, 2].values
    
    # 附件3: 6种风电场景标幺功率
    df3 = pd.read_excel(os.path.join(data_dir, '附件3：园区6种场景的风电标幺功率表.xlsx'))
    data['wind_scenarios'] = df3.iloc[:, 1:7].values  # shape (24, 6)
    
    # 附件4: 4种光伏场景标幺功率
    df4 = pd.read_excel(os.path.join(data_dir, '附件4：园区4种场景的光伏标幺功率表.xlsx'))
    data['pv_scenarios'] = df4.iloc[:, 1:5].values  # shape (24, 4)
    
    # 分时电价
    data['tou_prices'] = get_tou_prices()
    
    return data


def calc_actual_power(data, wind_pu, pv_pu, scale_factor=1.0):
    """计算实际功率
    Args:
        data: 数据字典
        wind_pu: 风电标幺功率 (24,)
        pv_pu: 光伏标幺功率 (24,)
        scale_factor: 产能扩容倍数
    Returns:
        dict with P_wind, P_pv, P_load, P_H2NH3
    """
    P_wind = wind_pu * P_WIND_CAP          # MW
    P_pv = pv_pu * P_PV_CAP               # MW
    P_load = data['load_pu'] * P_LOAD_PEAK  # MW
    P_H2NH3 = (P_ALKEL_BASE + P_PEMEL_BASE + P_NH3_BASE) * scale_factor  # MW
    
    return {
        'P_wind': P_wind,
        'P_pv': P_pv,
        'P_load': P_load,
        'P_H2NH3': P_H2NH3
    }


def calc_green_indicators(E_use, E_RE, E_buy, E_sell):
    """计算绿电直连指标
    r1: 自发自用比例 (要求>60%)
    r2: 绿电比例 (要求>30%)
    r3: 上网电量比例 (要求<20%)
    """
    r1 = (E_use - E_sell - E_buy) / E_RE * 100 if E_RE > 0 else 0
    r2 = (E_RE - E_sell) / E_use * 100 if E_use > 0 else 0
    r3 = E_sell / E_RE * 100 if E_RE > 0 else 0
    return r1, r2, r3


def check_green_compliance(r1, r2, r3):
    """检查绿电指标是否满足要求"""
    c1 = r1 > 60
    c2 = r2 > 30
    c3 = r3 < 20
    if c1 and c2 and c3:
        return 'all_pass'
    elif not c1 and not c2 and not c3:
        return 'all_fail'
    else:
        return 'partial'


def calc_ton_cost(E_buy_arr, E_sell_arr, P_wind, P_pv, P_H2NH3, 
                  h_run, Q_NH3, tou_prices, scale_factor=1.0):
    """计算吨氨成本 (元/吨)
    Args:
        E_buy_arr: 各时段购电量 MWh (24,)
        E_sell_arr: 各时段售电量 MWh (24,)
        P_wind: 各时段风电功率 MW (24,)
        P_pv: 各时段光伏功率 MW (24,)
        P_H2NH3: 制氢氨总功率 MW (标量)
        h_run: 运行小时数
        Q_NH3: 日产氨量 (吨)
        tou_prices: 分时电价 (24,)
        scale_factor: 扩容倍数
    """
    # 购电成本 (元) - 功率MW × 时间1h = MWh, ×1000 = kWh
    C_buy = np.sum(tou_prices * E_buy_arr * 1000)
    
    # 售电收入 (元)
    R_sell = np.sum(SELL_PRICE * E_sell_arr * 1000)
    
    # 风光度电成本 (元) - 含折旧
    E_wind = np.sum(P_wind) * 1  # MWh (每时段1h)
    E_pv = np.sum(P_pv) * 1      # MWh
    C_RE = WIND_COST * E_wind * 1000 + PV_COST * E_pv * 1000
    
    # 制氢运维成本 (元)
    P_ALKEL = P_ALKEL_BASE * scale_factor
    P_PEMEL = P_PEMEL_BASE * scale_factor
    P_NH3_rated = P_NH3_BASE * scale_factor
    E_ALKEL = P_ALKEL * h_run  # MWh
    E_PEMEL = P_PEMEL * h_run  # MWh
    E_NH3_elec = P_NH3_rated * h_run  # MWh
    C_OM_H2 = (OM_ALKEL * E_ALKEL + OM_PEMEL * E_PEMEL) * 1000
    C_OM_NH3 = OM_NH3 * E_NH3_elec * 1000
    
    # 合成氨装置折旧 (元/日)
    H2_capacity = (H2_RATE_ALKEL + H2_RATE_PEMEL) * scale_factor  # kg/h
    NH3_invest_total = H2_capacity * NH3_INVEST  # 元
    C_dep_NH3 = NH3_invest_total / (NH3_LIFE * 365)
    
    # 吨氨成本
    total_cost = C_buy - R_sell + C_RE + C_OM_H2 + C_OM_NH3 + C_dep_NH3
    C_ton = total_cost / Q_NH3 if Q_NH3 > 0 else float('inf')
    
    return C_ton, {
        'C_buy': C_buy,
        'R_sell': R_sell,
        'C_RE': C_RE,
        'C_OM_H2': C_OM_H2,
        'C_OM_NH3': C_OM_NH3,
        'C_dep_NH3': C_dep_NH3,
        'total_cost': total_cost
    }


def save_json(data, filepath):
    """保存结果为JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=convert)
    print(f"  Saved: {filepath}")
