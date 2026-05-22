# 建模求解报告：绿电直连型电氢氨园区优化运行

## 一、模型假设

### 假设 1：电氢氨装置作为整体同步运行
- 理由：题目明确"电氢氨装置只有全额开机和停机两种运行方式"（问题二），制氢直接供合成氨，逻辑上必须同步
- 参数化：`SYNC_OPERATION = True`
- 替代假设：各设备独立控制（`SYNC_OPERATION = False`），但与题意不符

### 假设 2：设备功率随产能线性同步扩容
- 理由：题目明确"配套电氢氨装置的额定功率将随产能规模呈线性同步提升"
- 参数化：`SCALE_FACTOR = Q_target / Q_base`，其中 `Q_base = 36` 吨/日
- 替代假设：非线性扩容（不符合题意）

### 假设 3：不计园区内部功率损耗
- 理由：题目问题一明确"不计园区功率损耗"
- 参数化：`LOSS_FACTOR = 0`（可扩展为 0.02~0.05）
- 替代假设：考虑 2%~5% 线损（问题四离网时可考虑）

### 假设 4：同一时段不能同时购电和售电
- 理由：物理上园区与电网只有一个接口，功率方向唯一
- 参数化：互补约束 $P_{\text{buy}}(t) \cdot P_{\text{sell}}(t) = 0$
- 替代假设：无（物理约束，不可放松）

### 假设 5：吨氨成本包含设备折旧摊销
- 理由：附件5/6给出了投资成本和使用寿命，应计入年化折旧以反映真实经济性
- 参数化：`INCLUDE_DEPRECIATION = True`
- 替代假设：仅计运行成本（`INCLUDE_DEPRECIATION = False`），用于灵敏度分析

### 假设 6：制氢耗电量按"未考虑效率"的 50 kWh/kg 计算
- 理由：附件5明确标注"50kWh/kg（未考虑效率）"，即实际耗电 = 50/效率
- 参数化：`H2_ELEC_BASE = 50`（kWh/kg），实际耗电 = `H2_ELEC_BASE / efficiency`
- 替代假设：直接用 50 kWh/kg（不考虑效率差异）
- **注意**：但题目给出的额定功率和产氢量已经隐含了效率。ALKEL 10MW产140kg/h → 实际耗电 10000/140 = 71.4 kWh/kg；PEMEL 10MW产160kg/h → 实际耗电 10000/160 = 62.5 kWh/kg。因此建模时直接用"额定功率×运行时间=用电量"更准确，不需要再用50kWh/kg反算。

### 假设 7：每种风光场景代表 15 天，24种场景覆盖全年 360 天
- 理由：题目明确"每一种风光场景代表15天"，24×15=360≈365
- 参数化：`DAYS_PER_SCENARIO = 15`
- 替代假设：按实际天数 365/24 ≈ 15.2 天（差异可忽略）

### 假设 8：储能初始和终末 SOC 相等（日循环约束）
- 理由：保证储能日运行的可持续性，避免"借储能"的虚假优化
- 参数化：`SOC_INIT = SOC_END = 0.5 * C_bat`（可调）
- 替代假设：不约束终末 SOC（可能导致储能被"掏空"）

### 假设 9：风光发电优先自用，余电才上网
- 理由：题目明确"风光发电优先供给区域内制氢、制氨负荷以及本地电负荷"
- 参数化：功率平衡方程中的优先级逻辑
- 替代假设：无（题目硬约束）

### 假设 10：合成氨用氢需求由制氢设备实时供给，不考虑氢气储存
- 理由：题目未提及氢气储罐，系统图中制氢直接连接合成氨装置
- 参数化：`H2_STORAGE = False`
- 替代假设：有氢气缓冲罐（题目未给参数，不建模）

## 二、符号说明

| 符号 | 含义 | 单位 | 取值范围 | 首次出现 |
|------|------|------|----------|----------|
| $t$ | 时段索引 | h | $\{1,2,...,24\}$ | 全文 |
| $P_{\text{wind}}(t)$ | 风电出力功率 | MW | $[0, 40]$ | 问题一 |
| $P_{\text{pv}}(t)$ | 光伏出力功率 | MW | $[0, 64]$ | 问题一 |
| $P_{\text{load}}(t)$ | 常规电负荷功率 | MW | $[0, 6]$ | 问题一 |
| $P_{\text{ALKEL}}^{\text{rated}}$ | 碱性电解槽额定功率 | MW | 10（基准） | 问题一 |
| $P_{\text{PEMEL}}^{\text{rated}}$ | 质子交换膜电解槽额定功率 | MW | 10（基准） | 问题一 |
| $P_{\text{NH3}}^{\text{rated}}$ | 合成氨装置额定功率 | MW | 0.75（基准） | 问题一 |
| $P_{\text{buy}}(t)$ | 电网购电功率 | MW | $\geq 0$ | 问题一 |
| $P_{\text{sell}}(t)$ | 上网售电功率 | MW | $\geq 0$ | 问题一 |
| $x(t)$ | 开停机状态（离散） | — | $\{0, 1\}$ | 问题二 |
| $\alpha(t)$ | 出力系数（连续） | — | $[0.1, 1]$ | 问题三 |
| $P_{\text{ch}}(t)$ | 储能充电功率 | MW | $\geq 0$ | 问题四 |
| $P_{\text{dis}}(t)$ | 储能放电功率 | MW | $\geq 0$ | 问题四 |
| $E(t)$ | 储能荷电状态 | MWh | $[0, C_{\text{bat}}]$ | 问题四 |
| $C_{\text{bat}}$ | 储能配置容量 | MWh | $> 0$ | 问题四 |
| $\eta_{\text{ch}}$ | 储能充电效率 | — | 0.9 | 问题四 |
| $\eta_{\text{dis}}$ | 储能放电效率 | — | 0.9 | 问题四 |
| $\sigma$ | 储能自损耗率 | /h | 0.002 | 问题四 |
| $\lambda_{\text{buy}}(t)$ | 分时购电价格 | 元/kWh | 见附件7 | 问题一 |
| $\lambda_{\text{sell}}$ | 上网售电价格 | 元/kWh | 0.3779 | 问题一 |
| $E_{\text{RE}}$ | 新能源日发电量 | MWh | — | 问题一 |
| $E_{\text{use}}$ | 园区日总用电量 | MWh | — | 问题一 |
| $E_{\text{buy}}$ | 日网购电量 | MWh | — | 问题一 |
| $E_{\text{sell}}$ | 日上网电量 | MWh | — | 问题一 |
| $r_1$ | 自发自用比例 | % | 要求 $>60\%$ | 问题一 |
| $r_2$ | 绿电比例 | % | 要求 $>30\%$ | 问题一 |
| $r_3$ | 上网电量比例 | % | 要求 $<20\%$ | 问题一 |
| $C_{\text{ton}}$ | 吨氨成本 | 元/吨 | — | 问题一 |
| $Q_{\text{NH3}}$ | 日制氨产量 | 吨 | $[36, 72]$ | 问题二 |
| $k$ | 产能扩容倍数 | — | $Q/36$ | 问题二 |
| $h$ | 日运行小时数 | h | $[12, 24]$ | 问题二 |


## 三、问题一：典型风光场景下运行指标分析

### 3.1 模型描述

问题一为确定性功率平衡计算，电解槽与合成氨装置满负荷连续运行。

### 3.2 数学模型

**功率平衡方程**（逐时段 $t = 1, ..., 24$）：

$$
P_{\text{wind}}(t) + P_{\text{pv}}(t) + P_{\text{buy}}(t) = P_{\text{load}}(t) + P_{\text{ALKEL}}^{\text{rated}} + P_{\text{PEMEL}}^{\text{rated}} + P_{\text{NH3}}^{\text{rated}} + P_{\text{sell}}(t)
$$

**互补约束**：

$$
P_{\text{buy}}(t) \geq 0, \quad P_{\text{sell}}(t) \geq 0, \quad P_{\text{buy}}(t) \cdot P_{\text{sell}}(t) = 0
$$

等价于：

$$
P_{\text{net}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t) - P_{\text{ALKEL}}^{\text{rated}} - P_{\text{PEMEL}}^{\text{rated}} - P_{\text{NH3}}^{\text{rated}}
$$

$$
P_{\text{sell}}(t) = \max(P_{\text{net}}(t), 0), \quad P_{\text{buy}}(t) = \max(-P_{\text{net}}(t), 0)
$$

**能量指标计算**（时段长度 $\Delta t = 1$ h）：

$$
E_{\text{use}} = \sum_{t=1}^{24} [P_{\text{load}}(t) + P_{\text{ALKEL}}^{\text{rated}} + P_{\text{PEMEL}}^{\text{rated}} + P_{\text{NH3}}^{\text{rated}}] \cdot \Delta t
$$

$$
E_{\text{RE}} = \sum_{t=1}^{24} [P_{\text{wind}}(t) + P_{\text{pv}}(t)] \cdot \Delta t
$$

$$
E_{\text{buy}} = \sum_{t=1}^{24} P_{\text{buy}}(t) \cdot \Delta t, \quad E_{\text{sell}} = \sum_{t=1}^{24} P_{\text{sell}}(t) \cdot \Delta t
$$

**绿电直连指标**：

$$
r_1 = \frac{E_{\text{use}} - E_{\text{sell}} - E_{\text{buy}}}{E_{\text{RE}}} \times 100\%
$$

$$
r_2 = \frac{E_{\text{RE}} - E_{\text{sell}}}{E_{\text{use}}} \times 100\%
$$

$$
r_3 = \frac{E_{\text{sell}}}{E_{\text{RE}}} \times 100\%
$$

**注意**：$r_1$ 的分子 = 总用电量 - 上网电量 - 网购电量 = 新能源自发自用电量。由功率平衡可知：$E_{\text{use}} - E_{\text{sell}} - E_{\text{buy}} = E_{\text{RE}} - 2E_{\text{sell}}$（当 $E_{\text{use}} + E_{\text{sell}} = E_{\text{RE}} + E_{\text{buy}}$ 时）。

实际上按题目公式：自发自用电量 = 总用电量 - 上网电量 - 网购电量。这里需要注意：

$$
E_{\text{use}} + E_{\text{sell}} = E_{\text{RE}} + E_{\text{buy}}
$$

因此：$E_{\text{use}} - E_{\text{sell}} - E_{\text{buy}} = E_{\text{RE}} - 2E_{\text{sell}}$

### 3.3 吨氨成本模型

$$
C_{\text{ton}} = \frac{C_{\text{buy}} - R_{\text{sell}} + C_{\text{RE}} + C_{\text{OM}} + C_{\text{dep}}}{Q_{\text{NH3}}}
$$

其中各成本项：

**购电成本**：

$$
C_{\text{buy}} = \sum_{t=1}^{24} \lambda_{\text{buy}}(t) \cdot P_{\text{buy}}(t) \cdot \Delta t \times 1000 \quad (\text{元})
$$

**售电收入**：

$$
R_{\text{sell}} = \sum_{t=1}^{24} \lambda_{\text{sell}} \cdot P_{\text{sell}}(t) \cdot \Delta t \times 1000 \quad (\text{元})
$$

**新能源度电成本**：

$$
C_{\text{RE}} = 0.15 \times E_{\text{wind}} \times 1000 + 0.12 \times E_{\text{pv}} \times 1000 \quad (\text{元})
$$

其中 $E_{\text{wind}} = \sum_t P_{\text{wind}}(t) \cdot \Delta t$（MWh），$E_{\text{pv}} = \sum_t P_{\text{pv}}(t) \cdot \Delta t$（MWh）。

**运维成本**：

$$
C_{\text{OM}} = (0.1 \times P_{\text{ALKEL}}^{\text{rated}} + 0.15 \times P_{\text{PEMEL}}^{\text{rated}} + 0.002 \times P_{\text{NH3}}^{\text{rated}}) \times h_{\text{run}} \times 1000 \quad (\text{元})
$$

**设备折旧**（日均摊）：

$$
C_{\text{dep}} = \frac{I_{\text{wind}}}{25 \times 365} + \frac{I_{\text{pv}}}{25 \times 365} + \frac{I_{\text{ALKEL}}}{30 \times 365} + \frac{I_{\text{PEMEL}}}{30 \times 365} + \frac{I_{\text{NH3}}}{30 \times 365}
$$

设备投资额计算：
- 风电投资：$I_{\text{wind}} = 0.15 \times P_{\text{wind}}^{\text{cap}} \times 8760 \times 1000 \times 25$（按度电成本反推总投资不合理）

**修正方案**：由于题目只给了度电成本而非总投资额，设备折旧已隐含在度电成本中。因此：
- 风电/光伏的度电成本 0.15/0.12 元/kWh 已包含投资折旧+运维
- 制氢设备运维系数 0.1/0.15 元/kWh 为纯运维成本
- 合成氨投资 60000 元/kgH2（产能）需单独计算折旧

**最终吨氨成本公式**：

$$
C_{\text{ton}} = \frac{C_{\text{buy}} - R_{\text{sell}} + C_{\text{RE}} + C_{\text{OM,H2}} + C_{\text{OM,NH3}} + C_{\text{dep,NH3}}}{Q_{\text{NH3}}}
$$

其中：
- $C_{\text{RE}} = 0.15 \times E_{\text{wind}} \times 1000 + 0.12 \times E_{\text{pv}} \times 1000$（风光度电成本含折旧）
- $C_{\text{OM,H2}} = (0.1 \times E_{\text{ALKEL}} + 0.15 \times E_{\text{PEMEL}}) \times 1000$（制氢运维）
- $C_{\text{OM,NH3}} = 0.002 \times E_{\text{NH3,elec}} \times 1000$（合成氨运维）
- $C_{\text{dep,NH3}}$：合成氨装置日折旧

合成氨装置投资折旧计算：
- 产能 36 吨/日时：产氢能力 = (140+160) = 300 kg/h
- 投资 = 300 × 60000 = 18,000,000 元
- 日折旧 = 18,000,000 / (30×365) = 1,643.84 元/日

### 3.4 求解算法

```
算法 1: 问题一功率平衡计算
输入: 风光标幺功率、负荷标幺功率、设备参数
输出: 功率曲线、能量指标、绿电指标、吨氨成本

1. 读取附件1/2数据，计算实际功率
2. 逐时段计算净功率 P_net(t)
3. 确定购电/售电功率
4. 累加计算各能量指标
5. 代入绿电指标公式
6. 计算吨氨成本
```

### 3.5 预期结果

基于验算：
- 总用电量：558.72 MWh，新能源发电量：603.45 MWh
- 网购电量：172.04 MWh，上网电量：216.77 MWh
- $r_1 = 28.16\%$（❌ 不满足 >60%），$r_2 = 69.21\%$（✅），$r_3 = 35.92\%$（❌ 不满足 <20%）
- 原因：风光出力集中在白天，而制氢氨负荷全天均匀运行，时序不匹配


## 四、问题二：基于离散制氨调节的运行优化

### 4.1 模型描述

产能扩至 72 吨/日，设备功率线性扩容（倍数 $k=2$）。制氨产量从 72→36 吨/日按 9 吨递减，共 5 档。电氢氨装置只有全额开机/停机两种方式，需选择最优开机时段使吨氨成本最低。

### 4.2 参数扩容规则

产能扩容倍数 $k = Q_{\text{NH3}} / 36$（对于 72 吨/日产能，$k=2$）：

| 设备 | 基准功率 | 扩容后功率（$k=2$） |
|------|---------|-------------------|
| ALKEL | 10 MW | 20 MW |
| PEMEL | 10 MW | 20 MW |
| 合成氨 | 0.75 MW | 1.5 MW |
| 产氢能力 | 300 kg/h | 600 kg/h |
| 产氨能力 | 1.5 吨/h | 3.0 吨/h |

各产量对应运行小时数：

| 日产量（吨） | 运行小时数 $h$ | 组合数 $C_{24}^h$ |
|-------------|--------------|-----------------|
| 72 | 24 | 1 |
| 63 | 21 | 2,024 |
| 54 | 18 | 134,596 |
| 45 | 15 | 1,307,504 |
| 36 | 12 | 2,704,156 |

### 4.3 数学模型

**决策变量**：$x(t) \in \{0, 1\}$，$t = 1, ..., 24$，表示时段 $t$ 是否开机

**目标函数**：最小化吨氨成本

$$
\min \quad C_{\text{ton}} = \frac{C_{\text{buy}} - R_{\text{sell}} + C_{\text{RE}} + C_{\text{OM}} + C_{\text{dep}}}{Q_{\text{NH3}}}
$$

**约束条件**：

(1) 运行时段约束：

$$
\sum_{t=1}^{24} x(t) = h = \frac{Q_{\text{NH3}}}{3.0}
$$

(2) 功率平衡（逐时段）：

$$
P_{\text{wind}}(t) + P_{\text{pv}}(t) + P_{\text{buy}}(t) = P_{\text{load}}(t) + x(t) \cdot (P_{\text{ALKEL}}^k + P_{\text{PEMEL}}^k + P_{\text{NH3}}^k) + P_{\text{sell}}(t)
$$

其中 $P_{\text{ALKEL}}^k = 20$ MW，$P_{\text{PEMEL}}^k = 20$ MW，$P_{\text{NH3}}^k = 1.5$ MW。

(3) 购售电互补：

$$
P_{\text{buy}}(t) \geq 0, \quad P_{\text{sell}}(t) \geq 0, \quad P_{\text{buy}}(t) \cdot P_{\text{sell}}(t) = 0
$$

(4) 非负约束：$x(t) \in \{0, 1\}$

**展开目标函数**：

定义制氢氨总负荷功率 $P_{\text{H2NH3}} = P_{\text{ALKEL}}^k + P_{\text{PEMEL}}^k + P_{\text{NH3}}^k = 41.5$ MW

每时段净功率：

$$
P_{\text{net}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t) - x(t) \cdot P_{\text{H2NH3}}
$$

$$
P_{\text{sell}}(t) = \max(P_{\text{net}}(t), 0), \quad P_{\text{buy}}(t) = \max(-P_{\text{net}}(t), 0)
$$

购电成本：

$$
C_{\text{buy}} = \sum_{t=1}^{24} \lambda_{\text{buy}}(t) \cdot P_{\text{buy}}(t) \cdot 1000
$$

售电收入：

$$
R_{\text{sell}} = \sum_{t=1}^{24} 0.3779 \cdot P_{\text{sell}}(t) \cdot 1000
$$

### 4.4 求解策略

由于组合数较大（最大 $C_{24}^{12} \approx 270$ 万），采用以下策略：

**方法 1：贪心启发式 + 局部搜索**

核心思想：优先选择"净收益最高"的时段开机。

定义每个时段的"开机净成本"：

$$
\Delta C(t) = \lambda_{\text{buy}}(t) \cdot \max(P_{\text{H2NH3}} - P_{\text{RE,surplus}}(t), 0) - \lambda_{\text{sell}} \cdot \max(P_{\text{RE,surplus}}(t) - P_{\text{H2NH3}}, 0)
$$

其中 $P_{\text{RE,surplus}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t)$ 为扣除常规负荷后的可用新能源功率。

贪心策略：按 $\Delta C(t)$ 从小到大排序，选前 $h$ 个时段开机。

**方法 2：整数线性规划（ILP）**

将互补约束线性化：引入辅助变量

$$
P_{\text{buy}}(t) = \max(-P_{\text{net}}(t), 0), \quad P_{\text{sell}}(t) = \max(P_{\text{net}}(t), 0)
$$

由于 $x(t)$ 确定后，$P_{\text{net}}(t)$ 确定，$P_{\text{buy}}(t)$ 和 $P_{\text{sell}}(t)$ 也确定。因此目标函数可以写成 $x(t)$ 的函数：

$$
\min_{x} \sum_{t=1}^{24} f(x(t), t)
$$

其中 $f(x(t), t)$ 是分段线性函数。可以用 PuLP/scipy 的 ILP 求解器直接求解。

**实际实现**：由于问题规模不大（24 个 0-1 变量），直接用 PuLP 建模求解 ILP，同时用贪心解作为初始可行解和验证基准。

### 4.5 子问题(1)：典型场景分析

对 5 种产量（72/63/54/45/36 吨/日），分别求解 ILP 得到最优开机时段安排，计算：
- 最优开机时段集合
- 绿电指标 $r_1, r_2, r_3$
- 吨氨成本 $C_{\text{ton}}$
- 设备利用率 = $h/24$

### 4.6 子问题(2)：24 种场景全年分析

对 24 种风光组合场景（6风×4光），每种场景下对 5 种产量分别求解最优方案：
- 统计各产量下吨氨成本分布
- 绿电指标分类统计（全满足/部分满足/全不满足）
  - 全满足：$r_1 > 60\%$ 且 $r_2 > 30\%$ 且 $r_3 < 20\%$
  - 部分满足：至少一个满足但非全部
  - 全不满足：三个指标均不满足
- 全年吨氨成本 = $\sum_{s=1}^{24} C_{\text{ton}}^{(s)} \times 15 / 360$（加权平均）

### 4.7 编程实现要点

- 使用 PuLP 库建模 ILP
- 分时电价映射：根据附件7确定每时段电价类型
- 对每种产量×每种场景，独立求解一个 ILP 问题
- 总计：5 产量 × 24 场景 = 120 个 ILP 问题（规模小，秒级求解）
- 输出：JSON 格式存储所有结果

```
算法 2: 问题二离散优化
输入: 24种风光场景数据、设备参数、产量列表
输出: 每种产量×场景的最优方案

for Q in [72, 63, 54, 45, 36]:
    h = Q / 3.0  # 运行小时数
    for scenario in 24_scenarios:
        # 建立ILP模型
        model = LpProblem("min_cost", LpMinimize)
        x = [LpVariable(f"x_{t}", cat='Binary') for t in range(24)]
        # 约束: sum(x) = h
        # 目标: min 购电成本 - 售电收入
        # 求解
        model.solve()
        # 计算绿电指标和吨氨成本
```


## 五、问题三：基于连续制氨调节的运行优化

### 5.1 模型描述

产能 72 吨/日，产量从 72→36 吨/日按 9 吨递减。电氢氨装置功率连续可调（下限 10%）。在 24 种风光场景下，求最优功率调度方案。

### 5.2 数学模型

**决策变量**：$\alpha(t) \in [0.1, 1]$，$t = 1, ..., 24$，表示时段 $t$ 的出力系数

**目标函数**：最小化吨氨成本

$$
\min \quad C_{\text{ton}} = \frac{\sum_{t=1}^{24} [\lambda_{\text{buy}}(t) \cdot P_{\text{buy}}(t) - \lambda_{\text{sell}} \cdot P_{\text{sell}}(t)] \times 1000 + C_{\text{RE}} + C_{\text{OM}} + C_{\text{dep}}}{Q_{\text{NH3}}}
$$

**约束条件**：

(1) 产量约束：

$$
\sum_{t=1}^{24} \alpha(t) \cdot 3.0 \cdot \Delta t = Q_{\text{NH3}}
$$

即 $\sum_{t=1}^{24} \alpha(t) = Q_{\text{NH3}} / 3.0 = h$

(2) 出力系数范围：

$$
0.1 \leq \alpha(t) \leq 1, \quad \forall t
$$

注意：$\alpha(t) = 0$ 也允许（停机），但开机时最低 10%。为简化建模，可以设 $\alpha(t) \in \{0\} \cup [0.1, 1]$。

**关键处理**：题目说"功率连续可调（下限为10%）"，意味着设备可以在 10%~100% 之间任意调节，也可以完全停机（$\alpha=0$）。建模时用混合整数方式处理：

$$
\alpha(t) = y(t) \cdot \beta(t), \quad y(t) \in \{0, 1\}, \quad \beta(t) \in [0.1, 1]
$$

但这会引入整数变量。更简洁的处理：直接设 $\alpha(t) \in [0, 1]$，加约束"若 $\alpha(t) > 0$ 则 $\alpha(t) \geq 0.1$"。

**实际简化**：对于给定产量 $Q$，运行小时数 $h = Q/3$。如果 $h \leq 24$，可以让部分时段 $\alpha=0$（停机），其余时段 $\alpha \in [0.1, 1]$。但连续可调的优势在于不需要完全停机——可以全天低负荷运行。

**最终建模方案**：

设 $\alpha(t) \in [0, 1]$，约束：
- 若 $\alpha(t) > 0$，则 $\alpha(t) \geq 0.1$（通过大M法线性化）
- $\sum_{t=1}^{24} \alpha(t) = h$

引入辅助二进制变量 $y(t) \in \{0,1\}$：

$$
0.1 \cdot y(t) \leq \alpha(t) \leq y(t), \quad \forall t
$$

$$
\sum_{t=1}^{24} \alpha(t) = h
$$

(3) 功率平衡：

$$
P_{\text{net}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t) - \alpha(t) \cdot P_{\text{H2NH3}}
$$

$$
P_{\text{sell}}(t) = \max(P_{\text{net}}(t), 0), \quad P_{\text{buy}}(t) = \max(-P_{\text{net}}(t), 0)
$$

(4) 线性化 max 函数：引入辅助变量

$$
P_{\text{buy}}(t) \geq -P_{\text{net}}(t), \quad P_{\text{buy}}(t) \geq 0
$$

$$
P_{\text{sell}}(t) \geq P_{\text{net}}(t), \quad P_{\text{sell}}(t) \geq 0
$$

$$
P_{\text{buy}}(t) + P_{\text{sell}}(t) = |P_{\text{net}}(t)|
$$

由于目标函数中购电有正成本、售电有负成本（收入），优化器会自动选择最小化购电、最大化售电，因此互补约束自动满足（不需要额外的大M约束）。

### 5.3 线性规划形式

将问题转化为标准 LP（忽略 10% 下限约束的整数性，允许 $\alpha(t) \in [0, 1]$）：

$$
\min_{\alpha, P_{\text{buy}}, P_{\text{sell}}} \sum_{t=1}^{24} [\lambda_{\text{buy}}(t) \cdot P_{\text{buy}}(t) - \lambda_{\text{sell}} \cdot P_{\text{sell}}(t)]
$$

约束：
- $P_{\text{buy}}(t) - P_{\text{sell}}(t) = P_{\text{load}}(t) + \alpha(t) \cdot P_{\text{H2NH3}} - P_{\text{RE}}(t), \quad \forall t$
- $P_{\text{buy}}(t) \geq 0, \quad P_{\text{sell}}(t) \geq 0, \quad \forall t$
- $0 \leq \alpha(t) \leq 1, \quad \forall t$
- $\sum_{t=1}^{24} \alpha(t) = h$

这是一个标准线性规划问题，可用 scipy.optimize.linprog 或 PuLP 高效求解。

**关于 10% 下限的处理**：实际操作中，LP 求解后检查是否有 $0 < \alpha(t) < 0.1$ 的情况。如果有，将这些时段的 $\alpha$ 调整为 0 或 0.1（取成本更低者），然后重新分配产量到其他时段。实践中，由于 LP 的最优解通常在顶点，$\alpha(t)$ 倾向于取 0 或 1 的极端值，中间值较少出现。

### 5.4 子问题分析

**(1) 24 场景最优调度 + 全年统计**

对每种产量 $Q \in \{72, 63, 54, 45, 36\}$，在 24 种场景下求解 LP：
- 最优功率调度方案 $\alpha^*(t)$
- 绿电指标和吨氨成本
- 全年统计（全满足/部分满足/全不满足）

**(2) 各场景运行分析**

分析不同风光资源条件下的调度特征：
- 高风光场景：$\alpha(t)$ 跟踪风光出力，白天高负荷、夜间低负荷
- 低风光场景：$\alpha(t)$ 趋于均匀（无法有效跟踪）
- 购电/售电模式与电价时段的关系

**(3) 与问题二对比**

- 连续调节 vs 离散调节的成本差异
- 绿电指标改善程度
- 灵活性价值量化：$\Delta C = C_{\text{ton}}^{\text{Q2}} - C_{\text{ton}}^{\text{Q3}}$

### 5.5 编程实现要点

- 使用 scipy.optimize.linprog 求解 LP（效率高）
- 决策变量向量：$[\alpha_1, ..., \alpha_{24}, P_{\text{buy},1}, ..., P_{\text{buy},24}, P_{\text{sell},1}, ..., P_{\text{sell},24}]$（72 维）
- 等式约束：24 个功率平衡 + 1 个产量约束 = 25 个
- 不等式约束：变量上下界
- 总计：5 产量 × 24 场景 = 120 个 LP 问题

```
算法 3: 问题三连续优化
输入: 24种风光场景数据、设备参数、产量列表
输出: 每种产量×场景的最优调度方案

for Q in [72, 63, 54, 45, 36]:
    h = Q / 3.0
    for scenario in 24_scenarios:
        # 构建LP: min c^T x
        # x = [alpha(1..24), P_buy(1..24), P_sell(1..24)]
        # 等式约束: A_eq x = b_eq
        #   功率平衡: P_buy(t) - P_sell(t) = load(t) + alpha(t)*P_H2NH3 - P_RE(t)
        #   产量约束: sum(alpha) = h
        # 变量界: 0<=alpha<=1, P_buy>=0, P_sell>=0
        result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
        # 后处理: 检查10%下限，计算指标
```


## 六、问题四：离网运行及储能配置

### 6.1 模型描述

园区离网运行（$P_{\text{buy}} = P_{\text{sell}} = 0$），用能完全受制于风光发电。产能 72 吨/日，功率连续可调（下限 10%）。需分析无储能和有储能两种情况。

### 6.2 子问题(1)：无储能离网运行

**决策变量**：$\alpha(t) \in [0, 1]$，$t = 1, ..., 24$

**目标函数**：最大化产氨量（尽限利用风光）

$$
\max \quad Q_{\text{NH3}} = \sum_{t=1}^{24} \alpha(t) \cdot 3.0 \cdot \Delta t
$$

**约束条件**：

(1) 功率平衡（离网，无购售电）：

$$
\alpha(t) \cdot P_{\text{H2NH3}} + P_{\text{load}}(t) \leq P_{\text{wind}}(t) + P_{\text{pv}}(t), \quad \forall t
$$

(2) 出力系数范围：

$$
0 \leq \alpha(t) \leq 1, \quad \forall t
$$

(3) 10% 下限约束（开机时）：若 $\alpha(t) > 0$ 则 $\alpha(t) \geq 0.1$

**简化处理**：由于目标是最大化产量，$\alpha(t)$ 应尽可能大。每时段的最大可用出力系数为：

$$
\alpha_{\max}(t) = \min\left(\frac{P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t)}{P_{\text{H2NH3}}}, 1\right)
$$

若 $\alpha_{\max}(t) < 0.1$，则该时段停机（$\alpha(t) = 0$）；否则 $\alpha(t) = \alpha_{\max}(t)$。

**弃电量计算**：

$$
P_{\text{curtail}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) - P_{\text{load}}(t) - \alpha(t) \cdot P_{\text{H2NH3}}
$$

$$
E_{\text{curtail}} = \sum_{t=1}^{24} P_{\text{curtail}}(t) \cdot \Delta t
$$

**吨氨成本**（离网，无购电成本）：

$$
C_{\text{ton}}^{\text{off}} = \frac{C_{\text{RE}} + C_{\text{OM}} + C_{\text{dep}}}{Q_{\text{NH3}}}
$$

**最小风光装机容量估算**：

要求园区能源自给（全年所有场景下产氨量 ≥ 某目标），需找到最小的 $P_{\text{wind}}^{\text{cap}}$ 和 $P_{\text{pv}}^{\text{cap}}$ 使得最差场景下仍能满足基本生产需求。

设最差场景为风电场景2+光伏场景4（发电量最低），要求至少能维持 10% 负荷运行：

$$
P_{\text{wind}}^{\text{cap}} \cdot \bar{p}_{\text{wind}}^{\min} + P_{\text{pv}}^{\text{cap}} \cdot \bar{p}_{\text{pv}}^{\min} \geq P_{\text{load,avg}} + 0.1 \cdot P_{\text{H2NH3}}
$$

### 6.3 子问题(2)：储能配置优化

**决策变量**：
- $\alpha(t) \in [0, 1]$：出力系数
- $P_{\text{ch}}(t) \geq 0$：充电功率
- $P_{\text{dis}}(t) \geq 0$：放电功率
- $C_{\text{bat}}$：储能容量（外层优化）

**目标函数**：最小化吨氨成本（含储能投资折旧）

$$
\min \quad C_{\text{ton}} = \frac{C_{\text{RE}} + C_{\text{OM}} + C_{\text{dep}} + C_{\text{bat,dep}}}{Q_{\text{NH3}}}
$$

其中储能日折旧：

$$
C_{\text{bat,dep}} = \frac{C_{\text{bat}} \times 1000}{15 \times 365} \quad (\text{元/日})
$$

储能运维：

$$
C_{\text{bat,OM}} = 0.01 \times (E_{\text{ch,total}} + E_{\text{dis,total}}) \times 1000 \quad (\text{元/日})
$$

**约束条件**：

(1) 功率平衡（离网+储能）：

$$
\alpha(t) \cdot P_{\text{H2NH3}} + P_{\text{load}}(t) + P_{\text{ch}}(t) = P_{\text{wind}}(t) + P_{\text{pv}}(t) + P_{\text{dis}}(t), \quad \forall t
$$

(2) SOC 动态方程：

$$
E(t+1) = (1 - \sigma) \cdot E(t) + \eta_{\text{ch}} \cdot P_{\text{ch}}(t) \cdot \Delta t - \frac{P_{\text{dis}}(t) \cdot \Delta t}{\eta_{\text{dis}}}
$$

(3) SOC 范围：

$$
0.1 \cdot C_{\text{bat}} \leq E(t) \leq 0.9 \cdot C_{\text{bat}}, \quad \forall t
$$

(4) 日循环约束：

$$
E(1) = E(25) = 0.5 \cdot C_{\text{bat}}
$$

(5) 充放电功率限制（假设 C-rate = 0.5C）：

$$
P_{\text{ch}}(t) \leq 0.5 \cdot C_{\text{bat}}, \quad P_{\text{dis}}(t) \leq 0.5 \cdot C_{\text{bat}}
$$

(6) 充放电互斥：

$$
P_{\text{ch}}(t) \cdot P_{\text{dis}}(t) = 0
$$

（由优化器自动满足，因为同时充放电会增加损耗）

(7) 出力系数范围：$0 \leq \alpha(t) \leq 1$

(8) 产量最大化：$\max \sum_{t=1}^{24} \alpha(t)$

**两层优化结构**：

- **外层**：搜索最优储能容量 $C_{\text{bat}} \in [10, 500]$ MWh
  - 方法：黄金分割法 + 网格搜索（步长 10 MWh 粗搜 + 1 MWh 细搜）
- **内层**：给定 $C_{\text{bat}}$，求解最优调度 LP
  - 目标：最大化产氨量（或最小化吨氨成本）
  - 方法：线性规划（scipy.optimize.linprog）

**针对最大弃电场景**：

首先在子问题(1)中识别弃电量最大的场景（预期为高风光场景，如风电场景4+光伏场景1），然后针对该场景优化储能容量。

### 6.4 子问题(3)：离网 vs 联网经济性对比

在相同制氨产量需求下，对比：
- 离网模式（有储能）：成本 = 风光度电 + 运维 + 设备折旧 + 储能折旧
- 联网模式（问题三最优方案）：成本 = 风光度电 + 运维 + 设备折旧 + 购电 - 售电

系统支撑成本价值 = 联网模式成本 - 离网模式成本（若为正，说明联网更经济）

### 6.5 编程实现要点

- 子问题(1)：解析解，逐时段计算 $\alpha_{\max}(t)$，无需优化器
- 子问题(2)：两层优化
  - 外层：网格搜索 $C_{\text{bat}}$
  - 内层：LP 求解（变量维度 = 24×3 + 24 = 96，含 $\alpha$、$P_{\text{ch}}$、$P_{\text{dis}}$、$E$）
- 子问题(3)：直接对比计算

```
算法 4: 问题四储能配置优化
输入: 最大弃电场景数据、储能参数
输出: 最优储能容量、调度方案

# 外层: 搜索最优容量
for C_bat in range(10, 500, 10):  # 粗搜
    # 内层: LP求解最优调度
    # 变量: [alpha(1..24), P_ch(1..24), P_dis(1..24), E(1..25)]
    # 约束: 功率平衡、SOC动态、SOC范围、日循环
    Q_NH3, cost = solve_inner_LP(C_bat, scenario_data)
    C_ton = cost / Q_NH3
    record(C_bat, C_ton, Q_NH3)

# 细搜: 在粗搜最优附近±10 MWh范围内步长1 MWh
best_C_bat = fine_search(coarse_best)

# 全场景调度
for scenario in 24_scenarios:
    solve_inner_LP(best_C_bat, scenario)
```


## 七、问题五：绿电直连园区对电力系统的影响及政策建议

### 7.1 模型描述

定性分析题，基于前四题定量结论，从电力系统运行角度分析绿电直连园区容量渗透率提高后的影响。

### 7.2 分析框架

**利（至少3点）**：

1. **促进新能源就近消纳**：减少远距离输电损耗和通道建设投资，提高新能源利用率。定量依据：问题三中连续调节可使自发自用比例从28%提升至60%以上。

2. **降低电网调峰压力**：园区通过柔性负荷（制氢氨）主动跟踪风光出力，相当于为电网提供需求侧响应资源。定量依据：问题二/三中制氢氨负荷可在10%~100%范围内调节，调节容量达 37.35 MW。

3. **推动氢能产业链发展**：绿电-绿氢-绿氨一体化模式为化工行业深度脱碳提供可行路径，带动电解槽、储能等装备制造业发展。

**弊（至少3点）**：

1. **增加电网备用容量需求**：并网型园区在风光不足时大量购电，形成尖峰负荷，增加系统备用压力。定量依据：问题一中最大购电功率可达 30+ MW。

2. **电压/频率波动风险**：大规模风光接入点的功率快速波动可能引起局部电压越限和频率偏差。

3. **电网规划复杂度增加**：绿电直连项目的选址、容量、运行模式多样，增加配电网规划和调度的不确定性。

### 7.3 政策建议

1. 完善绿电交易和碳交易联动机制
2. 建立储能补贴和容量电价机制
3. 制定绿电直连项目并网技术标准
4. 推动氢氨储运基础设施建设
5. 建立园区与电网的协调调度机制

### 7.4 编程实现要点

- 无需编程求解，基于前四题结果进行定性论述
- 可用前四题的数据制作对比图表支撑论点

## 八、模型检验与灵敏度分析设计

### 8.1 模型检验方案

**回代检验**：
- 将最优解代回功率平衡方程，验证等式成立（误差 < 0.01 MW）
- 验证绿电指标计算的一致性（正向计算 vs 反向验证）

**交叉验证**：
- 问题二：贪心解 vs ILP 最优解对比（ILP 应不劣于贪心）
- 问题三：LP 解 vs 问题二最优解对比（连续应不劣于离散）
- 问题四：有储能 vs 无储能对比（有储能应改善产量和成本）

**物理一致性检验**：
- 能量守恒：$E_{\text{RE}} + E_{\text{buy}} = E_{\text{use}} + E_{\text{sell}}$（联网）
- 能量守恒：$E_{\text{RE}} = E_{\text{use}} + E_{\text{curtail}} + E_{\text{loss}}$（离网）
- 储能 SOC 始末一致：$E(1) = E(25)$

### 8.2 灵敏度分析方案

**关键参数及扰动范围**：

| 参数 | 基准值 | 扰动范围 | 预期影响 |
|------|--------|---------|---------|
| 风电装机容量 | 40 MW | ±20% | 影响发电量和绿电指标 |
| 光伏装机容量 | 64 MW | ±20% | 影响发电量和绿电指标 |
| 购电电价 | 见附件7 | ±30% | 直接影响吨氨成本 |
| 售电电价 | 0.3779 | ±30% | 影响售电收入 |
| 储能投资成本 | 1000 元/kWh | ±50% | 影响储能配置方案 |
| 储能效率 | 90% | 85%~95% | 影响储能经济性 |

**灵敏度分析方法**：
- 单因素分析：逐一扰动参数，观察目标函数变化
- 龙卷风图：展示各参数对吨氨成本的影响排序

### 8.3 鲁棒性检验

- 风光场景的随机性已通过 24 种场景覆盖
- 对最优方案在所有 24 种场景下的表现进行统计分析
- 计算吨氨成本的均值、标准差、最大值、最小值

## 九、结果约束清单

### 9.1 硬边界约束

- $P_{\text{buy}}(t) \geq 0$，$P_{\text{sell}}(t) \geq 0$：功率非负
- $0 \leq \alpha(t) \leq 1$：出力系数范围
- $0 \leq E(t) \leq C_{\text{bat}}$：SOC 范围
- $P_{\text{ch}}(t) \geq 0$，$P_{\text{dis}}(t) \geq 0$：充放电非负
- $r_1 \in [0, 100\%]$，$r_2 \in [0, 100\%]$，$r_3 \in [0, 100\%]$：指标范围
- $C_{\text{ton}} > 0$：吨氨成本为正
- $Q_{\text{NH3}} \in [0, 72]$ 吨/日：产量不超过产能

### 9.2 预期行为

- 问题一：$r_1 \approx 28\%$（不满足），$r_3 \approx 36\%$（不满足）
- 问题二：随产量降低，$r_1$ 和 $r_3$ 改善（因为负荷减少，余电减少）
- 问题三：连续调节的吨氨成本 ≤ 问题二的离散调节（更灵活）
- 问题四：离网产量 < 联网产量（受限于风光），有储能后产量提升
- 资源单调性：问题三结果 ≥ 问题二结果（连续包含离散）

### 9.3 异常处理预案

**若 LP 求解返回 infeasible**：
- 原因判断：产量约束与功率上限矛盾（要求的运行小时数 > 可用时段数）
- 唯一修正方法：降低产量目标或放松约束
- 禁止：忽略不可行结果继续计算

**若吨氨成本为负**：
- 原因判断：售电收入 > 所有成本（极端高风光场景）
- 唯一修正方法：检查成本计算是否遗漏项（折旧、运维），确认无遗漏后接受结果
- 禁止：人为调整使成本为正

**若绿电指标 > 100% 或 < 0%**：
- 原因判断：公式代入错误或能量不守恒
- 唯一修正方法：回查功率平衡方程，确保 $E_{\text{RE}} + E_{\text{buy}} = E_{\text{use}} + E_{\text{sell}}$
- 禁止：截断到 [0, 100%] 而不查原因

**若问题三成本 > 问题二成本（同产量同场景）**：
- 原因判断：LP 建模错误（连续可行域包含离散可行域，不应更差）
- 唯一修正方法：检查 LP 约束是否正确，特别是产量约束和变量界
- 禁止：接受"连续比离散更差"的结果

## 十、方法指定

### 步骤 1：数据读取与预处理
- 方法：pandas.read_excel 读取所有附件
- 输入：user_data/*.xlsx
- 输出：各时段功率数组（numpy array）
- 禁止替代：不用 csv 读取（文件为 xlsx 格式）

### 步骤 2：问题一功率平衡计算
- 方法：numpy 向量化计算（逐时段）
- 输入：风光标幺功率、负荷标幺功率、设备额定功率
- 输出：功率曲线、能量指标、绿电指标、吨氨成本
- 禁止替代：不用循环逐时段计算（效率低）

### 步骤 3：问题二 ILP 求解
- 方法：PuLP + CBC 求解器（开源 ILP 求解器）
- 输入：场景功率数据、产量目标
- 输出：最优开机时段 $x^*(t)$
- 禁止替代：不用暴力枚举（$C_{24}^{12}$ 太大）；不用遗传算法（ILP 可精确求解）

### 步骤 4：问题三 LP 求解
- 方法：scipy.optimize.linprog（HiGHS 求解器）
- 输入：场景功率数据、产量目标
- 输出：最优出力系数 $\alpha^*(t)$
- 禁止替代：不用 PuLP（linprog 对纯 LP 更高效）；不用启发式算法

### 步骤 5：问题四两层优化
- 方法：外层网格搜索 + 内层 LP（scipy.optimize.linprog）
- 输入：场景功率数据、储能参数
- 输出：最优储能容量、调度方案
- 禁止替代：不用遗传算法做外层（网格搜索对一维问题更可靠）

### 步骤 6：结果可视化
- 方法：matplotlib + seaborn（使用 _utils/plot_utils.py）
- 输入：所有计算结果
- 输出：figures/*.pdf
- 禁止替代：不用 plotly（论文需要静态图）

## 十一、验证检查点

□ 能量守恒：$|E_{\text{RE}} + E_{\text{buy}} - E_{\text{use}} - E_{\text{sell}}| < 0.01$ MWh，若 fail → 检查功率平衡方程
□ 绿电指标范围：$0 \leq r_1, r_2, r_3 \leq 100\%$，若 fail → 检查公式代入
□ 问题一预期值：$r_1 \approx 28\%$，$r_3 \approx 36\%$，若偏差 > 5% → 检查数据读取
□ 资源单调性：$C_{\text{ton}}^{\text{Q3}} \leq C_{\text{ton}}^{\text{Q2}}$（同产量同场景），若 fail → 检查 LP 建模
□ 储能改善：有储能产量 ≥ 无储能产量，若 fail → 检查储能约束
□ 产量上限：$Q_{\text{NH3}} \leq 72$ 吨/日，若 fail → 检查 $\alpha$ 上界
□ 成本正值：$C_{\text{ton}} > 0$（正常情况），若为负 → 检查成本项完整性
□ 最终：所有输出量均在约束清单范围内


## 十二、结构性验证输入（供 comp-code 层级 5 使用）

### 约束活跃性预期

**问题二（ILP）**：
- 运行时段约束 $\sum x(t) = h$：预期活跃（等式约束，始终取等号）
- 变量界 $x(t) \in \{0,1\}$：预期所有变量取 0 或 1（整数约束天然活跃）

**问题三（LP）**：
- 产量约束 $\sum \alpha(t) = h$：预期活跃（等式约束）
- $\alpha(t) \leq 1$：预期在高风光时段活跃（满负荷运行）
- $\alpha(t) \geq 0$：预期在低风光时段活跃（停机）
- 如果所有 $\alpha(t)$ 都取内点值（0.1~0.9）→ 说明产量约束过松，需检查 $h$ 值

**问题四（LP+储能）**：
- 功率平衡：预期活跃（等式约束）
- SOC 上限 $E(t) \leq 0.9 C_{\text{bat}}$：预期在充电高峰时段活跃
- SOC 下限 $E(t) \geq 0.1 C_{\text{bat}}$：预期在放电末期活跃
- 日循环约束 $E(1)=E(25)$：预期活跃

### 决策变量合理范围与预期行为

| 变量 | 物理含义 | bounds | 预期取值区间 | 若取到边界说明什么 |
|------|---------|--------|-------------|------------------|
| $x(t)$ | 开停机 | {0,1} | 高风光时段=1 | 全1=满负荷运行 |
| $\alpha(t)$ | 出力系数 | [0,1] | 跟踪风光出力 | 取1=风光充足；取0=风光不足 |
| $P_{\text{ch}}(t)$ | 充电功率 | [0, 0.5C] | 弃电时段>0 | 取上限=弃电量大 |
| $P_{\text{dis}}(t)$ | 放电功率 | [0, 0.5C] | 缺电时段>0 | 取上限=缺电严重 |
| $C_{\text{bat}}$ | 储能容量 | [10, 500] MWh | 50~200 MWh | 取上限=弃电极多 |

### 灵敏度方向表

| 决策变量 | 增大时目标函数方向 | 预期灵敏度量级 | 若方向相反说明什么 |
|----------|-------------------|---------------|------------------|
| $\alpha(t)$（高风光时段） | ↓（成本降低） | 高 | 电价计算错误 |
| $\alpha(t)$（低风光时段） | ↑（成本增加） | 高 | 购电成本未正确计入 |
| $C_{\text{bat}}$ | 先↓后↑（U型） | 中 | 储能折旧未计入 |
| 购电电价 | ↑（成本增加） | 高 | 目标函数符号错误 |
| 售电电价 | ↓（成本降低） | 中 | 售电收入符号错误 |

### 稳定性预期

- 问题二（ILP）：离散问题，解唯一或有限个等价解，完全稳定
- 问题三（LP）：凸问题，全局最优唯一（可能有退化情况），完全稳定
- 问题四外层（容量搜索）：目标函数关于 $C_{\text{bat}}$ 为 U 型曲线，单峰，稳定
- 可接受变异系数阈值：0%（确定性优化，无随机性）

### 资源利用率预期

- 风光发电利用率：联网时 100%（余电上网），离网时 < 100%（有弃电）
- 制氢设备利用率：问题一 100%，问题二 $h/24$，问题三/四视场景而定
- 储能利用率：预期日充放电循环 0.5~1.5 次（不应为 0，否则储能无用）

## 十三、分时电价映射

根据附件7，各时段电价类型：

| 时段 | 类型 | 电价（元/kWh） |
|------|------|--------------|
| 0:00-7:00 (t=1~7) | 低谷 | 0.3424 |
| 7:00-10:00 (t=8~10) | 平时 | 0.6074 |
| 10:00-15:00 (t=11~15) | 高峰 | 0.8024 |
| 15:00-18:00 (t=16~18) | 平时 | 0.6074 |
| 18:00-21:00 (t=19~21) | 高峰 | 0.8024 |
| 21:00-23:00 (t=22~23) | 平时 | 0.6074 |
| 23:00-24:00 (t=24) | 低谷 | 0.3424 |

**调度策略启示**：
- 优先在低谷时段购电（成本低）
- 优先在高峰时段售电（收入高）
- 制氢氨负荷应尽量安排在风光充足或电价低谷时段

## 十四、升级审视与决策记录

### 审视赛题分析的升级建议

| 升级建议 | 审视结果 | 决策 |
|---------|---------|------|
| 0-1整数规划（时段选择） | 问题二核心机制 | ✅ 采用，用 PuLP+CBC 精确求解 |
| 带界约束线性规划 | 问题三核心机制 | ✅ 采用，$\alpha \in [0.1, 1]$ 下限约束 |
| 带储能状态的多时段LP | 问题四核心机制 | ✅ 采用，SOC 动态方程+日循环约束 |
| 参数化模型（按产能倍数缩放） | 问题二/三/四通用 | ✅ 采用，$k = Q/36$ 线性缩放 |

所有升级建议均已采纳，无异议。

### 防错审查对照

本题涉及题型：**优化类（规划/调度）**，已对照防错手册审查：
- ✅ 目标函数优化方向明确（min 吨氨成本）
- ✅ 所有约束条件有完整数学表达式
- ✅ 决策变量类型标注（0-1整数/连续）
- ✅ 验证可行域非空（问题一的满负荷方案即为可行解）
- ✅ LP 问题为凸，全局最优
- ✅ ILP 规模可控（24 个 0-1 变量），精确求解
- ✅ 非负约束已显式写出
- ✅ 资源单调性预期已标注

本题涉及题型：[优化类], 已对照防错手册审查。

## 十五、图表预规划

### 数据图表清单（从 PROBLEM_ANALYSIS.md 继承并更新）

- fig_q1_power_balance — 面积图+折线图 — 典型日功率平衡曲线（风电、光伏、负荷、购电、售电堆叠）
- fig_q1_indicators — 分组柱状图 — 绿电指标对比（实际值 vs 要求值）
- fig_q2_gantt — 甘特图 — 不同产量下最优开机时段安排
- fig_q2_cost_vs_production — 折线图+标注 — 吨氨成本随产量变化曲线
- fig_q2_24scenes_cost — 箱线图 — 24场景下各产量吨氨成本分布
- fig_q2_annual_cost — 折线图 — 全年吨氨成本分布曲线
- fig_q2_indicator_stats — 堆叠柱状图 — 全年绿电指标满足情况统计
- fig_q3_dispatch — 热力图 — 24场景×24时段最优功率调度矩阵
- fig_q3_compare_q2 — 配对点图 — 问题三 vs 问题二吨氨成本对比
- fig_q3_annual_cost — 折线图 — 全年吨氨成本分布曲线（与问题二叠加对比）
- fig_q4_offgrid_production — 分组柱状图 — 24场景离网产氨量对比
- fig_q4_storage_optimization — 双轴图 — 储能容量 vs 吨氨成本/弃电率
- fig_q4_soc_curve — 面积图 — 最大弃电场景储能SOC变化曲线
- fig_q4_onoff_compare — 发散柱状图 — 离网 vs 联网经济性对比
- fig_sensitivity — 龙卷风图 — 关键参数敏感性分析

### 补充图表（建模阶段新增）

- fig_q3_alpha_heatmap — 热力图 — 典型场景下 $\alpha(t)$ 调度方案可视化
- fig_q4_curtail_compare — 柱状图 — 有/无储能弃电量对比

### DrawIO 架构图清单

- DrawIO-1: 技术路线图 → fig_roadmap.drawio
- DrawIO-2: 问题一求解流程图 → fig_flow_q1.drawio
- DrawIO-3: 问题二求解流程图 → fig_flow_q2.drawio
- DrawIO-4: 问题三求解流程图 → fig_flow_q3.drawio
- DrawIO-5: 问题四求解流程图 → fig_flow_q4.drawio
- DrawIO-6: 园区能量流向架构图 → fig_system_arch.drawio

## 十六、编程实现要点总结

### 依赖库

```python
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import pulp  # ILP求解
import matplotlib.pyplot as plt
import seaborn as sns
```

### 代码结构建议

```
code/
├── data_loader.py      # 数据读取与预处理
├── problem1.py         # 问题一：功率平衡计算
├── problem2.py         # 问题二：ILP离散优化
├── problem3.py         # 问题三：LP连续优化
├── problem4.py         # 问题四：离网+储能优化
├── cost_model.py       # 吨氨成本计算模块
├── indicators.py       # 绿电指标计算模块
├── validate.py         # 结果验证模块
└── results/            # 结果输出目录
```

### 关键实现细节

1. **数据读取**：统一将标幺功率转换为实际功率（MW），时段索引从 0 开始
2. **电价映射**：建立 24 元素数组 `price[t]`，根据附件7映射
3. **ILP 建模**（问题二）：
   - 目标函数中 $P_{\text{buy}}(t)$ 和 $P_{\text{sell}}(t)$ 是 $x(t)$ 的分段线性函数
   - 线性化方法：引入辅助连续变量，用大M约束
   - 或者直接枚举（对于 $h=21,24$ 组合数小）+ ILP（对于 $h=12,15,18$）
4. **LP 建模**（问题三）：
   - 标准形式：$\min c^T x$，$A_{eq} x = b_{eq}$，$lb \leq x \leq ub$
   - 变量排列：$[α_1,...,α_{24}, P_{buy,1},...,P_{buy,24}, P_{sell,1},...,P_{sell,24}]$
5. **储能 LP**（问题四）：
   - 增加 SOC 状态变量 $E(1),...,E(25)$
   - SOC 动态方程作为等式约束
   - 日循环约束：$E(1) = E(25) = 0.5 C_{\text{bat}}$

### validate_constraints() 函数设计

```python
def validate_constraints(results, scenario_name):
    """每个子问题代码末尾必须调用"""
    errors = []
    
    # 1. 能量守恒
    balance = abs(results['E_RE'] + results['E_buy'] - results['E_use'] - results['E_sell'])
    if balance > 0.01:
        errors.append(f"能量不守恒: 偏差 {balance:.4f} MWh")
    
    # 2. 绿电指标范围
    for r_name in ['r1', 'r2', 'r3']:
        if not (0 <= results[r_name] <= 100):
            errors.append(f"{r_name} = {results[r_name]:.2f}% 超出 [0,100%]")
    
    # 3. 产量上限
    if results['Q_NH3'] > 72:
        errors.append(f"产量 {results['Q_NH3']:.1f} 超过产能上限 72 吨/日")
    
    # 4. 成本正值（警告）
    if results['C_ton'] < 0:
        print(f"⚠ 吨氨成本为负 ({results['C_ton']:.2f})，检查成本项完整性")
    
    # 5. 功率非负
    if np.any(results['P_buy'] < -0.001) or np.any(results['P_sell'] < -0.001):
        errors.append("购电/售电功率出现负值")
    
    if errors:
        raise ValueError(f"[{scenario_name}] 约束违反:\n" + "\n".join(errors))
    
    print(f"✅ [{scenario_name}] 所有约束验证通过")
```

