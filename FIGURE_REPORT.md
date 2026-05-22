# 图表生成报告

## 生成概况

共生成 **17 张 PDF 数据图**，覆盖问题一至问题四及灵敏度分析全部章节。

## 图表清单

| 编号 | 文件名 | 图表类型 | 对应章节 |
|------|--------|----------|----------|
| 1 | fig_q1_power_balance.pdf | 面积图+折线图 | 问题一 |
| 2 | fig_q1_indicators.pdf | 分组柱状图 | 问题一 |
| 3 | fig_q2_gantt.pdf | 甘特图 | 问题二(1) |
| 4 | fig_q2_cost_vs_production.pdf | 折线图+标注 | 问题二(1) |
| 5 | fig_q2_24scenes_cost.pdf | 箱线图 | 问题二(2) |
| 6 | fig_q2_annual_cost.pdf | 折线图 | 问题二(2) |
| 7 | fig_q2_indicator_stats.pdf | 堆叠柱状图 | 问题二(2) |
| 8 | fig_q3_dispatch.pdf | 热力图 | 问题三(1) |
| 9 | fig_q3_alpha_heatmap.pdf | 热力图 | 问题三(1) |
| 10 | fig_q3_compare_q2.pdf | 配对点图 | 问题三(3) |
| 11 | fig_q3_annual_cost.pdf | 折线图 | 问题三(1) |
| 12 | fig_q4_offgrid_production.pdf | 分组柱状图 | 问题四(1) |
| 13 | fig_q4_storage_optimization.pdf | 双轴图 | 问题四(2) |
| 14 | fig_q4_soc_curve.pdf | 面积图 | 问题四(2) |
| 15 | fig_q4_curtail_compare.pdf | 柱状图 | 问题四(2) |
| 16 | fig_q4_onoff_compare.pdf | 发散柱状图 | 问题四(3) |
| 17 | fig_sensitivity.pdf | 龙卷风图 | 灵敏度分析 |

## 图表多样性

| 图表类型 | 使用次数 |
|---------|---------|
| 折线图 | 3 |
| 面积图 | 2 |
| 柱状图/分组柱状图 | 3 |
| 堆叠柱状图 | 1 |
| 双轴图 | 1 |
| 箱线图 | 1 |
| 配对点图 | 1 |
| 发散柱状图 | 1 |
| 热力图 | 2 |
| 甘特图 | 1 |
| 龙卷风图 | 1 |

无重复超过3次，满足多样性要求。

## 配色方案

使用 `setup_style('science')` 配色方案，统一全文风格：
- PALETTE: ['#7AAEC8', '#E8945A', '#7BC8A4', '#9B8EC4', '#E0A0A0', '#F0C05A']

## LaTeX 引用

所有图表的 LaTeX 引用代码已写入 `figures/latex_includes.tex`，可直接 `\input{figures/latex_includes.tex}` 使用。

## 注意事项

- 所有图表使用 SimHei 字体渲染中文标签
- 输出格式为 PDF（矢量图），DPI=300
- 图表无标题（标题由 LaTeX \caption 提供）
- 配色统一，无 matplotlib 默认色
