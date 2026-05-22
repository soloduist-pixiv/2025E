exec(open('figures/_style_header.py').read())

with open('figures/problem_3_results.json') as f:
    data = json.load(f)

comp = data['comparison_with_q2']
productions = ['72', '63', '54', '45', '36']

q2_costs = [comp[p]['Q2_cost'] for p in productions]
q3_costs = [comp[p]['Q3_cost'] for p in productions]
improvements = [comp[p]['improvement_pct'] for p in productions]

fig, ax = plt.subplots(figsize=(8, 5.5))

for i, p in enumerate(productions):
    ax.plot([0, 1], [q2_costs[i], q3_costs[i]], 'o-', color=PALETTE[i],
            linewidth=2, markersize=10, label=f'{p} t/d')
    mid_y = (q2_costs[i] + q3_costs[i]) / 2
    ax.text(1.05, q3_costs[i], f'-{improvements[i]:.1f}%', fontsize=10,
            va='center', color=PALETTE[i], fontweight='bold')

ax.set_xticks([0, 1])
ax.set_xticklabels(['问题二\n(离散调节)', '问题三\n(连续调节)'], fontsize=12)
ax.set_ylabel('年均吨氨成本 (元/t)', fontsize=13)
ax.set_xlim(-0.2, 1.4)
ax.legend(fontsize=10, loc='upper right')

fig.tight_layout()
fig.savefig('figures/fig_q3_compare_q2.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q3_compare_q2.pdf')
