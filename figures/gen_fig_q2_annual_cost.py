exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data = json.load(f)

costs_36 = sorted(data['cost_distribution']['36'])
n = len(costs_36)
days_per_scene = 15
cumulative_days = np.arange(1, n+1) * days_per_scene

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(cumulative_days, costs_36, 'o-', color=PALETTE[0], linewidth=2.0, markersize=7, label='问题二 (离散调节)')
ax.fill_between(cumulative_days, costs_36, alpha=0.15, color=PALETTE[0])

mean_cost = np.mean(costs_36)
ax.axhline(mean_cost, color=PALETTE[3], linestyle='--', linewidth=1.5, label=f'年均吨氨成本: {mean_cost:.0f} 元/t')

ax.set_xlabel('累计天数 (d)', fontsize=13)
ax.set_ylabel('吨氨成本 (元/t)', fontsize=13)
ax.legend(fontsize=11)
ax.set_xlim(0, 365)

fig.tight_layout()
fig.savefig('figures/fig_q2_annual_cost.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q2_annual_cost.pdf')
