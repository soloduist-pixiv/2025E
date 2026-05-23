exec(open('figures/_style_header.py').read())

# 读取下限灵敏度结果
with open('figures/regulation_sensitivity_results.json') as f:
    res = json.load(f)

LBs = [0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20]
costs = []
compliance_days = []

for lb in LBs:
    key = str(lb)
    costs.append(res[key]['mean_cost'])
    # 全满足场景数 * 15天/场景 = 全满足天数
    compliance_days.append(res[key]['all_pass'] * 15)

fig, ax1 = plt.subplots(figsize=(9, 5.5))

# 绘制左轴：吨氨成本
color_cost = PALETTE[0]
ax1.set_xlabel('装置出力下限 ($LB$)', fontsize=13)
ax1.set_ylabel('平均吨氨成本 (元/吨)', color=color_cost, fontsize=13)
line1 = ax1.plot([lb*100 for lb in LBs], costs, 'o-', color=color_cost, linewidth=2.5, markersize=8, label='平均吨氨成本')
ax1.tick_params(axis='y', labelcolor=color_cost, labelsize=11)
ax1.set_ylim(5715, 5735)
ax1.grid(True, linestyle='--', alpha=0.5)

# 绘制右轴：全满足合规天数
ax2 = ax1.twinx()
color_comp = '#2E9E44'
ax2.set_ylabel('全年绿电指标全满足天数 (天)', color=color_comp, fontsize=13)
line2 = ax2.plot([lb*100 for lb in LBs], compliance_days, 's--', color=color_comp, linewidth=2, markersize=8, label='合规天数')
ax2.tick_params(axis='y', labelcolor=color_comp, labelsize=11)
ax2.set_ylim(0, 365)

# 标注边际效益拐点 (Elbow Point) 10%
elbow_x = 10.0
elbow_y = costs[2]  # costs at 0.10
ax1.axvline(x=elbow_x, color='#E53935', linestyle='--', linewidth=2.0)
ax1.plot(elbow_x, elbow_y, 'ro', markersize=12, fillstyle='none', markeredgewidth=2)
ax1.annotate('边际效益拐点 (Elbow Point / 工程折中点)\n下限=10.0%, 成本=5719.16元/吨', 
             xy=(elbow_x, elbow_y), 
             xytext=(elbow_x + 1.2, elbow_y + 4.0),
             arrowprops=dict(facecolor='#E53935', shrink=0.08, width=1.5, headwidth=7),
             fontsize=10.5, color='#E53935', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.2))

# 合并图例
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', fontsize=11)

plt.title('连续调节出力下限对系统吨氨成本与合规天数的灵敏度分析', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()

# 保存高质量PDF矢量图
fig.savefig('figures/fig_regulation_sensitivity.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_regulation_sensitivity.pdf')
