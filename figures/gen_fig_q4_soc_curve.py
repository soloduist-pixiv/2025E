exec(open('figures/_style_header.py').read())

with open('figures/problem_4_results.json') as f:
    data = json.load(f)

best_C_bat = data['storage_optimization']['best_C_bat_MWh']
curve = data['storage_optimization']['capacity_cost_curve']
C_bat_values = curve['C_bat_values']
Q_values = curve['Q_NH3_values']

best_idx = -1
best_Q = Q_values[best_idx]
P_H2NH3_base = 41.5
alpha_base = best_Q / 72.0

hours = np.arange(24)
np.random.seed(42)
P_RE_typical = np.array([10.9, 15.2, 13.3, 15.1, 18.7, 10.9, 30.5, 35.8, 43.1, 49.0,
                         50.6, 53.4, 60.6, 49.6, 48.3, 38.9, 24.3, 11.5, 5.7, 3.8,
                         3.7, 4.9, 2.5, 3.2])
P_load_base = np.array([1.4, 1.1, 0.8, 1.0, 1.2, 1.6, 2.5, 3.4, 4.0, 4.2,
                         4.1, 3.9, 3.3, 2.7, 3.6, 3.8, 3.8, 3.1, 2.6, 2.1,
                         1.9, 1.6, 1.6, 1.5])
P_H2NH3_load = P_H2NH3_base * alpha_base
P_total_load = P_load_base + P_H2NH3_load
P_net = P_RE_typical - P_total_load

soc = np.zeros(25)
soc[0] = 0.5 * best_C_bat
eta = 0.92
for h in range(24):
    if P_net[h] > 0:
        charge = min(P_net[h], (best_C_bat - soc[h]) / eta)
        soc[h+1] = soc[h] + charge * eta
    else:
        discharge = min(-P_net[h], soc[h] * eta)
        soc[h+1] = soc[h] - discharge / eta

soc_pct = soc / best_C_bat * 100

fig, ax = plt.subplots(figsize=(9, 5))

ax.fill_between(np.arange(25), 0, soc_pct, alpha=0.3, color=PALETTE[0])
ax.plot(np.arange(25), soc_pct, color=PALETTE[0], linewidth=2.5)

ax.axhline(90, color=PALETTE[4], linestyle='--', linewidth=1, alpha=0.7, label='SOC上限 (90%)')
ax.axhline(10, color=PALETTE[4], linestyle='--', linewidth=1, alpha=0.7, label='SOC下限 (10%)')

ax.set_xlabel('时刻 (h)', fontsize=13)
ax.set_ylabel('SOC (%)', fontsize=13)
ax.set_xlim(0, 24)
ax.set_ylim(0, 100)
ax.set_xticks(np.arange(0, 25, 3))
ax.legend(fontsize=11)

fig.tight_layout()
fig.savefig('figures/fig_q4_soc_curve.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q4_soc_curve.pdf')
