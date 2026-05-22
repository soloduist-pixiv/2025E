exec(open('figures/_style_header.py').read())

with open('figures/problem_4_results.json') as f:
    data = json.load(f)

curve = data['storage_optimization']['capacity_cost_curve']
C_bat = np.array(curve['C_bat_values'])
C_ton = np.array(curve['C_ton_values'])
Q_NH3 = np.array(curve['Q_NH3_values'])

fig, ax1 = plt.subplots(figsize=(9, 5.5))

color1 = PALETTE[0]
color2 = PALETTE[1]

ln1 = ax1.plot(C_bat, C_ton, 'o-', color=color1, linewidth=2.5, markersize=7, label='吨氨成本')
ax1.set_xlabel('储能容量 (MWh)', fontsize=13)
ax1.set_ylabel('吨氨成本 (元/t)', fontsize=13, color=color1)
ax1.tick_params(axis='y', labelcolor=color1)

ax2 = ax1.twinx()
ln2 = ax2.plot(C_bat, Q_NH3, 's-', color=color2, linewidth=2.5, markersize=7, label='日产氨量')
ax2.set_ylabel('日产氨量 (t/d)', fontsize=13, color=color2)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.spines['right'].set_visible(True)

best_C = data['storage_optimization']['best_C_bat_MWh']
ax1.axvline(200, color=PALETTE[3], linestyle='--', linewidth=1.5, alpha=0.7)
ax1.text(210, C_ton[0] - 20, '拐点\n(200 MWh)', fontsize=10, color=PALETTE[3])

lns = ln1 + ln2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, fontsize=11, loc='center right')

fig.tight_layout()
fig.savefig('figures/fig_q4_storage_optimization.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q4_storage_optimization.pdf')
