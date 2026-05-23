import matplotlib.pyplot as plt

PALETTE = ['#7AAEC8', '#E8945A', '#7BC8A4', '#9B8EC4', '#E0A0A0', '#F0C05A']
PALETTE_LIGHT = ['#D9E8F0', '#F9E2D2', '#DDF3DE', '#ECE9F4', '#F8EBEB', '#FCF2DC']

def setup_style(style_name='science'):
    # 如果系统支持science风格则使用，否则跳过
    try:
        plt.style.use(style_name)
    except Exception:
        pass
