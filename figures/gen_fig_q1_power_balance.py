import sys, os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, '.')
from _utils.plot_utils import setup_style, PALETTE, PALETTE_LIGHT
setup_style('science')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 14
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.linewidth'] = 2.0
plt.rcParams['legend.frameon'] = False

with open('figures/problem_1_results.json') as f:
    data = json.load(f)

hours = np.arange(24)
P_wind = np.array(data['power_curves']['P_wind'])
P_pv = np.array(data['power_curves']['P_pv'])
P_RE = np.array(data['power_curves']['P_RE'])
P_total_load = np.array(data['power_curves']['P_total_load'])
P_buy = np.array(data['power_curves']['P_buy'])
P_sell = np.array(data['power_curves']['P_sell'])

fig, ax = plt.subplots(figsize=(10, 5.5))

ax.fill_between(hours, 0, P_wind, alpha=0.45, color=PALETTE[0], label='风电功率')
ax.fill_between(hours, P_wind, P_wind + P_pv, alpha=0.45, color=PALETTE[1], label='光伏功率')
ax.plot(hours, P_total_load, color=PALETTE[3], linewidth=2.5, label='总用电负荷', zorder=5)
ax.plot(hours, P_RE, color=PALETTE[2], linewidth=2.0, linestyle='--', label='新能源总发电', zorder=4)

bar_w = 0.35
ax.bar(hours - bar_w/2, P_buy, width=bar_w, alpha=0.7, color=PALETTE[4], label='购电功率')
ax.bar(hours + bar_w/2, -P_sell, width=bar_w, alpha=0.7, color=PALETTE[5], label='售电功率')

ax.set_xlabel('时刻 (h)', fontsize=14)
ax.set_ylabel('功率 (MW)', fontsize=14)
ax.set_xlim(-0.5, 23.5)
ax.set_xticks(np.arange(0, 24, 3))
ax.legend(loc='upper right', fontsize=11, ncol=2)
ax.axhline(0, color='gray', linewidth=0.5, linestyle='-')

fig.tight_layout()
fig.savefig('figures/fig_q1_power_balance.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q1_power_balance.pdf')
