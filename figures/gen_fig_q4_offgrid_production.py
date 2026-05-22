exec(open('figures/_style_header.py').read())

with open('figures/problem_4_results.json') as f:
    data = json.load(f)

scenarios = data['offgrid_no_storage']['scenarios']
names = [s['scenario'] for s in scenarios]
q_nh3 = [s['Q_NH3'] for s in scenarios]

fig, ax = plt.subplots(figsize=(12, 5))

colors = []
for i, s in enumerate(scenarios):
    wind_idx = int(s['scenario'].split('_')[0][1:]) - 1
    colors.append(PALETTE[wind_idx % len(PALETTE)])

bars = ax.bar(range(len(names)), q_nh3, color=colors, edgecolor='white', linewidth=0.8)

ax.axhline(72, color='#E53935', linestyle='--', linewidth=1.5, label='额定产能 72 t/d')
ax.axhline(np.mean(q_nh3), color=PALETTE[3], linestyle=':', linewidth=1.5, label=f'平均产量 {np.mean(q_nh3):.1f} t/d')

ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, fontsize=8, rotation=45, ha='right')
ax.set_ylabel('日产氨量 (t/d)', fontsize=13)
ax.set_xlabel('风光场景', fontsize=13)
ax.legend(fontsize=11)

fig.tight_layout()
fig.savefig('figures/fig_q4_offgrid_production.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q4_offgrid_production.pdf')
