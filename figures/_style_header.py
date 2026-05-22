import sys, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

sys.path.insert(0, '.')
from _utils.plot_utils import setup_style, PALETTE, PALETTE_LIGHT
setup_style('science')

plt.rcParams.update({
    'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 13,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.linewidth': 2.0,
    'legend.frameon': False,
    'svg.fonttype': 'none',
    'mathtext.fontset': 'dejavusans',
})
