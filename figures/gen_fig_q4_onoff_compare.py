exec(open('figures/_style_header.py').read())

with open('figures/problem_4_results.json') as f:
    data = json.load(f)

gvs = data['grid_vs_offgrid']

categories = ['吨氨成本', '日产氨量', '产能利用率']
offgrid_vals = [gvs['offgrid_cost'], gvs['offgrid_daily_Q'], data['storage_all_scenarios']['avg_utilization']]
grid_vals = [gvs['grid_cost'], gvs['grid_Q'], 50.0]

diff_pct = [(o - g) / g * 100 for o, g in zip(offgrid_vals, grid_vals)]

fig, ax = plt.subplots(figsize=(8, 5))

colors = [PALETTE[2] if d < 0 else PALETTE[4] for d in diff_pct]
bars = ax.barh(range(len(categories)), diff_pct, color=colors, height=0.5, edgecolor='white')

ax.set_yticks(range(len(categories)))
ax.set_yticklabels(categories, fontsize=12)
ax.set_xlabel('离网相对联网变化 (%)', fontsize=13)
ax.axvline(0, color='gray', linewidth=1)

for i, (bar, val) in enumerate(zip(bars, diff_pct)):
    x_pos = val + (1 if val >= 0 else -1)
    ha = 'left' if val >= 0 else 'right'
    ax.text(x_pos, i, f'{val:+.1f}%', va='center', ha=ha, fontsize=11, fontweight='bold')

fig.tight_layout()
fig.savefig('figures/fig_q4_onoff_compare.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q4_onoff_compare.pdf')
