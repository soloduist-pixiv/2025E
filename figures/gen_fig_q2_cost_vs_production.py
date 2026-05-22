exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data = json.load(f)

productions = [72, 63, 54, 45, 36]
costs = [data['typical_scenario'][str(p)]['C_ton'] for p in productions]
compliances = [data['typical_scenario'][str(p)]['compliance'] for p in productions]

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(productions, costs, 'o-', color=PALETTE[0], linewidth=2.5, markersize=10, zorder=5)

for i, (p, c, comp) in enumerate(zip(productions, costs, compliances)):
    color = '#2E9E44' if comp == 'all_pass' else '#E53935'
    label = '达标' if comp == 'all_pass' else '部分达标'
    ax.scatter(p, c, color=color, s=120, zorder=6, edgecolors='white', linewidth=1.5)
    offset = 200 if i < 3 else -300
    ax.annotate(f'{c:.0f}', (p, c), textcoords='offset points',
                xytext=(0, 12), ha='center', fontsize=10, color=PALETTE[0])

best_idx = np.argmin(costs)
ax.annotate(f'最低: {costs[best_idx]:.0f} 元/t\n({productions[best_idx]} t/d)',
            (productions[best_idx], costs[best_idx]),
            textcoords='offset points', xytext=(-60, -35), fontsize=11,
            arrowprops=dict(arrowstyle='->', color=PALETTE[3]),
            color=PALETTE[3], fontweight='bold')

ax.set_xlabel('日产氨量 (t/d)', fontsize=13)
ax.set_ylabel('吨氨成本 (元/t)', fontsize=13)
ax.set_xticks(productions)
ax.invert_xaxis()

fig.tight_layout()
fig.savefig('figures/fig_q2_cost_vs_production.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q2_cost_vs_production.pdf')
