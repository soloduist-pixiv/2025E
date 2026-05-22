exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data2 = json.load(f)
with open('figures/problem_3_results.json') as f:
    data3 = json.load(f)

costs_q2 = sorted(data2['cost_distribution']['36'])
costs_q3 = sorted(data3['cost_distribution']['36'])
n = len(costs_q2)
days_per_scene = 15
cumulative_days = np.arange(1, n+1) * days_per_scene

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(cumulative_days, costs_q2, 'o-', color=PALETTE[0], linewidth=2.0, markersize=6, label='问题二 (离散调节)')
ax.plot(cumulative_days, costs_q3, 's-', color=PALETTE[1], linewidth=2.0, markersize=6, label='问题三 (连续调节)')

ax.fill_between(cumulative_days, costs_q3, costs_q2, alpha=0.15, color=PALETTE[2], label='成本节省')

mean_q2 = np.mean(costs_q2)
mean_q3 = np.mean(costs_q3)
ax.axhline(mean_q2, color=PALETTE[0], linestyle='--', linewidth=1, alpha=0.6)
ax.axhline(mean_q3, color=PALETTE[1], linestyle='--', linewidth=1, alpha=0.6)

ax.text(350, mean_q2 + 80, f'{mean_q2:.0f}', fontsize=10, color=PALETTE[0])
ax.text(350, mean_q3 - 200, f'{mean_q3:.0f}', fontsize=10, color=PALETTE[1])

ax.set_xlabel('累计天数 (d)', fontsize=13)
ax.set_ylabel('吨氨成本 (元/t)', fontsize=13)
ax.legend(fontsize=11)
ax.set_xlim(0, 365)

fig.tight_layout()
fig.savefig('figures/fig_q3_annual_cost.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q3_annual_cost.pdf')
