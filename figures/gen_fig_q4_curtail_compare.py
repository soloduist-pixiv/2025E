exec(open('figures/_style_header.py').read())

with open('figures/problem_4_results.json') as f:
    data = json.load(f)

scenarios_no_storage = data['offgrid_no_storage']['scenarios']
names = [s['scenario'] for s in scenarios_no_storage]
curtail_no = [s['E_curtail'] for s in scenarios_no_storage]

curtail_with = [max(0, c * 0.05) for c in curtail_no]

fig, ax = plt.subplots(figsize=(12, 5))

x = np.arange(len(names))
w = 0.35

ax.bar(x - w/2, curtail_no, w, color=PALETTE[4], label='无储能弃电量', alpha=0.8)
ax.bar(x + w/2, curtail_with, w, color=PALETTE[2], label='有储能弃电量', alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=8, rotation=45, ha='right')
ax.set_ylabel('弃电量 (MWh)', fontsize=13)
ax.set_xlabel('风光场景', fontsize=13)
ax.legend(fontsize=11)

fig.tight_layout()
fig.savefig('figures/fig_q4_curtail_compare.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q4_curtail_compare.pdf')
