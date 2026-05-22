exec(open('figures/_style_header.py').read())

with open('figures/sensitivity_results.json') as f:
    data = json.load(f)

tornado = data['tornado']
base_cost = data['base_cost']

params = [t['parameter'] for t in tornado]
low_costs = [t['low_cost'] for t in tornado]
high_costs = [t['high_cost'] for t in tornado]

fig, ax = plt.subplots(figsize=(9, 5))

y_pos = np.arange(len(params))

for i, t in enumerate(tornado):
    low_delta = t['low_cost'] - base_cost
    high_delta = t['high_cost'] - base_cost
    left = min(low_delta, high_delta)
    right = max(low_delta, high_delta)
    
    ax.barh(i, right - left, left=left, height=0.5, color=PALETTE[i], edgecolor='white', linewidth=0.8)
    
    ax.text(left - 20, i, f'{t["low_cost"]:.0f}', va='center', ha='right', fontsize=10)
    ax.text(right + 20, i, f'{t["high_cost"]:.0f}', va='center', ha='left', fontsize=10)

ax.axvline(0, color='gray', linewidth=1.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(params, fontsize=12)
ax.set_xlabel('吨氨成本变化 (元/t)', fontsize=13)

ax.text(0, len(params) + 0.3, f'基准值: {base_cost:.0f} 元/t', ha='center', fontsize=11, color=PALETTE[3])

fig.tight_layout()
fig.savefig('figures/fig_sensitivity.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_sensitivity.pdf')
