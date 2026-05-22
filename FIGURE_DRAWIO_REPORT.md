# DrawIO/TikZ 图表生成报告

## 生成清单

| # | 文件名 | 类型 | 大小 | 状态 |
|---|--------|------|------|------|
| 1 | fig_roadmap.drawio/.pdf | 技术路线图 | 375 KB | ✅ 通过 |
| 2 | fig_flow_q1.drawio/.pdf | 问题一求解流程图 | 123 KB | ✅ 通过 |
| 3 | fig_flow_q2.drawio/.pdf | 问题二求解流程图 | 139 KB | ✅ 通过 |
| 4 | fig_flow_q3.drawio/.pdf | 问题三求解流程图 | 143 KB | ✅ 通过 |
| 5 | fig_flow_q4.drawio/.pdf | 问题四求解流程图 | 153 KB | ✅ 通过 |
| 6 | fig_system_arch.drawio/.pdf | 园区系统架构图 | 82 KB | ✅ 通过 |

## 结构自检结果

- **技术路线图**: 模板 A 三栏结构，通过 drawio_check.py roadmap 检查
- **求解流程图 x4**: 0 CRITICAL，通过 drawio_check.py flow 检查
- **系统架构图**: 能量流向拓扑，节点+连线结构

## 技术路线图内容

采用模板 A 三栏布局（研究框架 | 研究内容 | 研究方法）：
- 第一阶段（提出问题）：双碳战略背景 + 问题拆解（Q1-Q4）+ 约束条件
- 第二阶段（分析问题）：功率平衡建模 + 经济性分析
- 第三阶段（解决问题）：优化调度模型（离散/连续/离网/储能）+ 多场景验证
- 第四阶段（研究结论）：最优方案 + 储能配置 + 政策建议

## latex_includes.tex 更新

已在文件头部追加 6 个 DrawIO 图的 LaTeX include 片段，包含：
- fig_roadmap（技术路线图，问题重述章节）
- fig_system_arch（系统架构图，问题重述章节）
- fig_flow_q1 ~ fig_flow_q4（各子问题求解流程图）

所有图片使用 `keepaspectratio` + 双约束（width + height）防止占满整页。
