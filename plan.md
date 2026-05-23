# 绿电直连型电氢氨园区优化运行——可视化与数学模型细节深度优化方案

根据您的反馈与建议，我们将在上一阶段工作的基础上，对模型深度、定量分析与论文文本进行进一步的细节雕琢与深度拓展。本计划的核心目标是将单一的成本对比提升为富有学术厚度、图文并茂的顶级学术成果。

---

## 优化方向与可行性分析

### 1. BSTS 状态分解成分的可视化对比图
* **可行性分析**：我们已经成功运行了 `code/bsts_analysis.py`，并将结构化时序分解数据保存至 `figures/bsts_results.json` 中。
* **可视化设计**：我们将编写 `figures/gen_fig_bsts_decomp.py`，生成高质量学术 PDF 矢量图 `figures/fig_bsts_decomp.pdf`。
  - **图表布局**：采用纵向4子图叠放结构（Typical 4-row Stacked Layout），完美对齐 X 轴时间（0--24时）。
  - **子图内容**：
    1. **子图 1**：原始出力曲线（Original Power）与重建出力曲线（Reconstructed Power）的叠放对比，直观展示模型的拟合完备性。
    2. **子图 2**：提取出的基准趋势项（Trend $\mu(t)$），展示全天出力的宏观背景水平。
    3. **子图 3**：提取出的24小时共享日周期季节项（Seasonal $\tau(t)$），反映显著的昼夜日周期性。
    4. **子图 4**：高频随机扰动误差项（Irregular $\epsilon(t)$），反映不确定性噪音。
  - **应用**：该图将被嵌入论文「问题分析」章节，直观论证 BSTS 提取时序结构和波动特性的强大解释力。

### 2. 严谨的 LaTeX 标准化处理公式（正向 vs 负向指标）
* **修改目的**：由于我们设计的 6 个综合评价指标中，既有极大型（效益型，如合规天数、调峰容量、自给率等），也有极小型（成本型，如吨氨成本），且它们的物理量纲与数量级差异巨大（千元量级 vs 比例数值）。
* **建模深化**：我们将在论文中详细列出数据标准化的 LaTeX 严谨公式，并说明无量纲化处理对消除量纲偏见、提升决策模型可信度的决定性价值。
  - **正向指标（极大值效益型）规范化公式**：
    $$Z_{ij} = \frac{X_{ij} - \min_i X_{ij}}{\max_i X_{ij} - \min_i X_{ij}}$$
  - **负向指标（极小值成本型）规范化公式**：
    $$Z_{ij} = \frac{\max_i X_{ij} - X_{ij}}{\max_i X_{ij} - \min_i X_{ij}}$$
  这一规范化公式将完美嵌入 `10_evaluation.tex`，与 `code/evaluation_model.py` 中的代码实现达成百分之百的精确映射。

### 3. 连续调节下限的“边际效益拐点（Elbow Point）”分析与折线图生成
* **可行性分析**：上一阶段我们运行了 `code/regulation_sensitivity.py` 并保存了敏感性数据。分析数据表明，在下限 $LB$ 从 5% 收紧到 20% 时，合规天数（全满足240天，部分满足120天）保持平稳，而平均成本单调递增，且在 10% 处存在极其明显的斜率转折。
* **可视化设计**：我们将编写 `figures/gen_fig_regulation_sensitivity.py`，生成高质量 PDF 折线图 `figures/fig_regulation_sensitivity.pdf`。
  - **图表布局**：采用双 Y 轴折线图（Dual Y-Axis Line Chart）。
  - **左 Y 轴**：平均吨氨成本（元/吨），绘制单调上升的连续曲线。
  - **右 Y 轴**：绿电合规全满足天数（天，由全满足场景数 × 15 计算），绘制代表合规水平的平坦台阶折线。
  - **拐点标注**：在 X 轴 $LB = 10.0\%$ 处，绘制一条垂直红色虚线，并以醒目的文本标注为 **“边际效益拐点（Elbow Point / 工程折中点）”**。
* **经济与工程学论证**：
  - **Elbow Point 分析**：当下限从 10% 进一步降至 5% 时，吨氨成本仅减少 1.03 元/吨（改善幅度仅为极其微弱的 0.018%），且绿电合规天数完全没有提升；然而，在工程上，将电解槽的最低出力限制从 10% 降至 5% 会面临极高的安全风险（氢氧混合越限风险陡增）及频繁的微扰运行磨损。
  - **结论**：10% 出力下限是系统在经济性、政策合规性与设备工程安全复杂性之间达成的**完美工程折中（Optimal Engineering Trade-off）**。

---

## 详细工作计划与待修改文件

### 一、 新建与运行绘图脚本 (`figures/`)

#### 1. [NEW] [gen_fig_bsts_decomp.py](file:///d:/Aaaaaaaa/电工杯 A题 _20260522/workspace/figures/gen_fig_bsts_decomp.py)
* **功能**：读取 `figures/bsts_results.json`，绘制风电典型场景（W4）和光伏典型场景（P1）的 4 纵向叠加 BSTS 状态分解对比图，直观展示成分的叠加重构过程，保存为 `figures/fig_bsts_decomp.pdf`。

#### 2. [NEW] [gen_fig_regulation_sensitivity.py](file:///d:/Aaaaaaaa/电工杯 A题 _20260522/workspace/figures/gen_fig_regulation_sensitivity.py)
* **功能**：读取 `figures/regulation_sensitivity_results.json`，绘制双轴折线图，展示平均成本与合规天数随调节下限 $LB$ 的演变趋势，并在 10% 处显著标注边际效益拐点，保存为 `figures/fig_regulation_sensitivity.pdf`。

---

### 二、 LaTeX 论文内容修订计划 (`paper/sections/`)

#### 1. [MODIFY] [2_analysis.tex](file:///d:/Aaaaaaaa/电工杯 A题 _20260522/workspace/paper/sections/2_analysis.tex)
* **修改内容**：在「风光出力不确定性的 BSTS 状态空间分解」小节中插入 BSTS 分解图（图\ref{fig:bsts_decomp}），并添加相关文字引导读者直观理解各成分如何重构出原始风光出力的物理解释。

#### 2. [MODIFY] [7_problem3.tex](file:///d:/Aaaaaaaa/电工杯 A题 _20260522/workspace/paper/sections/7_problem3.tex)
* **修改内容**：在「连续调节功率下限的灵敏度边界与合规成本探讨」小节中插入灵敏度折线图（图\ref{fig:regulation_sensitivity}），并对 10% 处的 **边际效益拐点（Elbow Point）** 进行严谨、有学术深度的工程学与经济学双重深度论证。

#### 3. [MODIFY] [10_evaluation.tex](file:///d:/Aaaaaaaa/电工杯 A题 _20260522/workspace/paper/sections/10_evaluation.tex)
* **修改内容**：重写「步骤 1：决策矩阵标准化」部分，以极其严谨美观的 LaTeX 独立公式展示正向指标（极大型）和负向指标（极小制）的规范化处理过程，说明其在消除量纲差异上的决定性作用。

---

## 验证与测试方案

### 1. 绘图脚本执行与保存
* 运行新增的绘图脚本，确保成功保存为 PDF 矢量格式，并检查图表的配色、轴标签及图例是否优雅，拐点虚线 and 标注是否醒目。

### 2. LaTeX 论文重新编译与 PDF 生成
* 在终端执行 `xelatex main.tex` 重新编译论文，确保修改后的公式（BSTS 时序分解、熵权 TOPSIS 步骤等）、表格和段落排版完美，无编译报错，生成高颜值的学术 PDF。
