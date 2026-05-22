exec(open('figures/_style_header.py').read())

with open('figures/problem_2_results.json') as f:
    data = json.load(f)

productions = ['72', '63', '54', '45', '36']
colors_map = {p: PALETTE[i] for i, p in enumerate(productions)}

fig, ax = plt.subplots(figsize=(10, 5))

for idx, prod in enumerate(productions):
    schedule = data['typical_scenario'][prod]['schedule']
    y = len(productions) - 1 - idx
    for h in range(24):
        if schedule[h] == 1:
            ax.barh(y, 1, left=h, height=0.6, color=colors_map[prod], edgecolor='white', linewidth=0.5)

ax.set_yticks(range(len(productions)))
ax.set_yticklabels([f'{p} t/d' for p in reversed(productions)], fontsize=12)
ax.set_xlabel('时刻 (h)', fontsize=13)
ax.set_xlim(0, 24)
ax.set_xticks(np.arange(0, 25, 3))

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

peak_hours = list(range(8, 12)) + list(range(17, 21))
valley_hours = list(range(0, 7)) + [23]
for h in peak_hours:
    ax.axvspan(h, h+1, alpha=0.06, color='#E53935', zorder=0)
for h in valley_hours:
    ax.axvspan(h, h+1, alpha=0.06, color='#2E9E44', zorder=0)

ax.text(9.5, -0.8, '峰时段', ha='center', fontsize=10, color='#E53935')
ax.text(3, -0.8, '谷时段', ha='center', fontsize=10, color='#2E9E44')

fig.tight_layout()
fig.savefig('figures/fig_q2_gantt.pdf', dpi=300, bbox_inches='tight')
plt.close(fig)
print('OK: fig_q2_gantt.pdf')
