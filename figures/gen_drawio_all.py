#!/usr/bin/env python3
"""Generate all DrawIO XML files for the paper."""
import os

os.chdir(r'C:\Users\Bill\AppData\Roaming\MHAgent\workspaces\ea3b2e603485')

AQ = '&amp;quot;'
BR = '&lt;br&gt;'
def b(text): return f'&lt;b&gt;{text}&lt;/b&gt;'
def sub(text): return f'&lt;font style={AQ}font-size:9px;color:#888;{AQ}&gt;{text}&lt;/font&gt;'
def bsub(main, detail): return f'{b(main)}{BR}{sub(detail)}'

def cell(cid, value, style, x, y, w, h, parent="1"):
    return f'<mxCell id="{cid}" value="{value}" style="{style}" vertex="1" parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'

def edge(eid, sx, sy, tx, ty, style="rounded=1;html=1;strokeWidth=1.5;strokeColor=#999999;endArrow=block;endFill=1;"):
    return f'<mxCell id="{eid}" edge="1" parent="1" style="{style}"><mxGeometry relative="1" as="geometry"><mxPoint x="{sx}" y="{sy}" as="sourcePoint"/><mxPoint x="{tx}" y="{ty}" as="targetPoint"/></mxGeometry></mxCell>'

def wrap_diagram(name, did, content, dx=900, dy=700):
    return (f'<mxfile host="draw.io"><diagram name="{name}" id="{did}">'
            f'<mxGraphModel dx="{dx}" dy="{dy}" grid="1" gridSize="10" guides="1" '
            f'tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" '
            f'pageWidth="{dx}" pageHeight="{dy}" background="none" math="0" shadow="0">'
            f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            f'{content}</root></mxGraphModel></diagram></mxfile>')

# Styles
S_INPUT = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F4FA;strokeColor=#7B9FC0;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_PROC = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7AAA7A;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#F5F0E8;strokeColor=#B0A080;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_YES = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF5ED;strokeColor=#7AAA7A;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_NO = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5EDED;strokeColor=#B08080;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_OUTPUT = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDF5ED;strokeColor=#5A8A5A;strokeWidth=2;fontSize=11;fontStyle=1;"
S_LBL_YES = "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;strokeColor=none;fillColor=none;"
S_LBL_NO = S_LBL_YES
S_EDGE = "rounded=1;html=1;strokeWidth=1.5;strokeColor=#999999;endArrow=block;endFill=1;"
S_LOOP = "rounded=1;html=1;strokeWidth=1.5;strokeColor=#B08080;endArrow=block;endFill=1;dashed=1;"

def lbl_yes():
    return f'&lt;font style={AQ}font-size:10px;color:#7AAA7A;{AQ}&gt;{b("是")}&lt;/font&gt;'
def lbl_no():
    return f'&lt;font style={AQ}font-size:10px;color:#B08080;{AQ}&gt;{b("否")}&lt;/font&gt;'

# ===== Q1 Flow =====
c = ''
c += cell('n1', bsub('读取附件数据','风光标幺功率/负荷曲线/设备参数'), S_INPUT, 170, 10, 260, 42)
c += edge('e1', 235, 52, 135, 75, S_EDGE+"exitX=0.25;exitY=1;entryX=0.5;entryY=0;")
c += edge('e2', 365, 52, 465, 75, S_EDGE+"exitX=0.75;exitY=1;entryX=0.5;entryY=0;")
c += cell('n2', bsub('风光发电功率计算','风电40MW+光伏64MW标幺换算'), S_PROC, 20, 75, 230, 50)
c += cell('n3', bsub('用电负荷功率计算','ALKEL+PEMEL+合成氨+常规负荷'), S_PROC, 350, 75, 230, 50)
c += edge('e3', 135, 125, 235, 153, S_EDGE+"exitX=0.5;exitY=1;entryX=0.25;entryY=0;")
c += edge('e4', 465, 125, 365, 153, S_EDGE+"exitX=0.5;exitY=1;entryX=0.75;entryY=0;")
c += cell('n4', bsub('逐时段功率平衡计算','净功率 = 风光发电 - 总用电负荷'), S_INPUT, 130, 153, 340, 42)
c += edge('e5', 300, 195, 300, 218, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n5', b('净功率是否为正?'), S_DIAMOND, 230, 218, 140, 80)
c += edge('e6', 230, 258, 100, 320, S_EDGE+"exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
c += cell('ly', lbl_yes(), S_LBL_YES, 185, 275, 25, 18)
c += edge('e7', 370, 258, 500, 320, S_EDGE+"exitX=1;exitY=0.5;entryX=0.5;entryY=0;")
c += cell('ln', lbl_no(), S_LBL_NO, 375, 248, 25, 18)
c += cell('n6', bsub('余电上网','上网电量累加'), S_YES, 20, 320, 160, 42)
c += cell('n7', bsub('电网购电','网购电量累加'), S_NO, 420, 320, 160, 42)
c += edge('e8', 100, 362, 225, 395, S_EDGE+"exitX=0.5;exitY=1;entryX=0.25;entryY=0;")
c += edge('e9', 500, 362, 375, 395, S_EDGE+"exitX=0.5;exitY=1;entryX=0.75;entryY=0;")
c += cell('n8', bsub('计算绿电直连三项指标','自用率/绿电比/上网比 合规判定'), S_INPUT, 130, 395, 340, 48)
c += edge('e10', 300, 443, 300, 466, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n9', bsub('计算吨氨成本','(购电费-售电收益)/日产氨量'), S_INPUT, 130, 466, 340, 42)
c += edge('e11', 300, 508, 300, 531, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n10', bsub('输出结果','功率曲线/指标值/合规判定'), S_OUTPUT, 170, 531, 260, 42)
with open('figures/fig_flow_q1.drawio', 'w', encoding='utf-8') as f:
    f.write(wrap_diagram('问题一求解流程','fq1', c))
print('fig_flow_q1.drawio OK')

# ===== Q2 Flow =====
c = ''
c += cell('n1', bsub('设定产能参数','72t/d按9t递减至36t/d'), S_INPUT, 170, 10, 260, 42)
c += edge('e1', 300, 52, 300, 75, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n2', bsub('枚举日产量水平','72/63/54/45/36 吨/日'), S_PROC, 130, 75, 340, 42)
c += edge('e2', 300, 117, 300, 140, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n3', bsub('计算所需运行时段数','产量/额定产能=运行小时'), S_PROC, 130, 140, 340, 42)
c += edge('e3', 300, 182, 300, 208, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n4', bsub('遍历所有连续时段组合','C(24,h)种开机方案'), S_INPUT, 130, 208, 340, 42)
c += edge('e4', 300, 250, 300, 276, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n5', bsub('计算各方案购售电成本','分时电价加权计算'), S_PROC, 130, 276, 340, 42)
c += edge('e5', 300, 318, 300, 344, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n6', b('绿电指标是否满足?'), S_DIAMOND, 220, 344, 160, 80)
c += edge('e6', 300, 424, 300, 450, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('ly2', lbl_yes(), S_LBL_YES, 305, 426, 25, 18)
c += edge('e7', 380, 384, 480, 384, S_EDGE+"exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
c += cell('ln2', lbl_no(), S_LBL_NO, 390, 370, 25, 18)
c += cell('n7a', bsub('标记为不合规方案','记录但不选为最优'), S_NO, 480, 362, 160, 42)
c += cell('n7', bsub('选取吨氨成本最低方案','记录最优生产时段'), S_YES, 130, 450, 340, 42)
c += edge('e8', 300, 492, 300, 518, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n8', bsub('24场景遍历统计','全满足/部分满足/全不满足分类'), S_INPUT, 130, 518, 340, 48)
c += edge('e9', 300, 566, 300, 592, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n9', bsub('输出全年吨氨成本分布','最优产量/调度方案/利用率'), S_OUTPUT, 130, 592, 340, 42)
with open('figures/fig_flow_q2.drawio', 'w', encoding='utf-8') as f:
    f.write(wrap_diagram('问题二求解流程','fq2', c))
print('fig_flow_q2.drawio OK')

# ===== Q3 Flow =====
c = ''
c += cell('n1', bsub('设定连续调节参数','功率下限10%, 产能72t/d'), S_INPUT, 170, 10, 260, 42)
c += edge('e1', 300, 52, 300, 75, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n2', bsub('构建线性规划模型','目标: 最小化吨氨成本'), S_PROC, 130, 75, 340, 42)
c += edge('e2', 300, 117, 300, 143, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n3', bsub('设定约束条件','功率平衡/设备上下限/绿电指标'), S_INPUT, 130, 143, 340, 48)
c += edge('e3', 300, 191, 300, 217, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n4', bsub('逐时段功率优化','LP求解24时段制氢氨功率'), S_PROC, 130, 217, 340, 42)
c += edge('e4', 300, 259, 300, 285, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n5', b('绿电指标是否满足?'), S_DIAMOND, 230, 285, 140, 80)
c += edge('e5', 300, 365, 300, 391, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('ly3', lbl_yes(), S_LBL_YES, 305, 367, 25, 18)
c += edge('e6', 370, 325, 480, 325, S_EDGE+"exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
c += cell('ln3', lbl_no(), S_LBL_NO, 385, 310, 25, 18)
c += cell('n5a', bsub('调整产量水平','降低日产量重新优化'), S_NO, 480, 303, 150, 42)
c += edge('eloop', 555, 303, 480, 217, S_LOOP+"exitX=0.5;exitY=0;entryX=1;entryY=0.5;")
c += cell('n6', bsub('记录最优调度方案','各时段制氢氨功率分配'), S_YES, 130, 391, 340, 42)
c += edge('e7', 300, 433, 300, 459, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n7', bsub('24场景遍历','计算全年成本分布'), S_INPUT, 130, 459, 340, 42)
c += edge('e8', 300, 501, 300, 527, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n8', bsub('与问题二结果对比分析','吨氨成本/绿电指标变化'), S_PROC, 130, 527, 340, 42)
c += edge('e9', 300, 569, 300, 595, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n9', bsub('输出结果','最优调度/成本对比/改善分析'), S_OUTPUT, 170, 595, 260, 42)
with open('figures/fig_flow_q3.drawio', 'w', encoding='utf-8') as f:
    f.write(wrap_diagram('问题三求解流程','fq3', c))
print('fig_flow_q3.drawio OK')

# ===== Q4 Flow =====
c = ''
c += cell('n1', bsub('设定离网运行条件','无外部电网, 风光自给'), S_INPUT, 170, 10, 260, 42)
c += edge('e1', 300, 52, 300, 78, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n2', bsub('计算风光可用功率','24场景逐时段发电能力'), S_PROC, 130, 78, 340, 42)
c += edge('e2', 300, 120, 300, 146, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n3', bsub('功率约束下最大制氨','负荷不超过风光发电'), S_INPUT, 130, 146, 340, 42)
c += edge('e3', 300, 188, 300, 214, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n4', b('是否存在弃电?'), S_DIAMOND, 230, 214, 140, 80)
c += edge('e4', 230, 254, 100, 316, S_EDGE+"exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
c += cell('ly4', lbl_yes(), S_LBL_YES, 175, 260, 25, 18)
c += edge('e5', 370, 254, 500, 316, S_EDGE+"exitX=1;exitY=0.5;entryX=0.5;entryY=0;")
c += cell('ln4', lbl_no(), S_LBL_NO, 380, 244, 25, 18)
c += cell('n5', bsub('配置储能系统','优化容量/功率/SOC管理'), S_YES, 20, 316, 165, 48)
c += cell('n5b', bsub('直接记录产量','无弃电场景'), S_PROC, 420, 316, 165, 42)
c += edge('e6', 100, 364, 225, 400, S_EDGE+"exitX=0.5;exitY=1;entryX=0.25;entryY=0;")
c += edge('e7', 500, 358, 375, 400, S_EDGE+"exitX=0.5;exitY=1;entryX=0.75;entryY=0;")
c += cell('n6', bsub('储能参与调度优化','充放电策略+制氨功率协调'), S_INPUT, 130, 400, 340, 48)
c += edge('e8', 300, 448, 300, 474, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n7', bsub('计算各场景吨氨成本','全年总量和利用率'), S_PROC, 130, 474, 340, 42)
c += edge('e9', 300, 516, 300, 542, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n8', bsub('离网vs联网经济性对比','系统支撑成本价值分析'), S_INPUT, 130, 542, 340, 48)
c += edge('e10', 300, 590, 300, 616, S_EDGE+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += cell('n9', bsub('输出结果','储能方案/成本对比/改善分析'), S_OUTPUT, 170, 616, 260, 42)
with open('figures/fig_flow_q4.drawio', 'w', encoding='utf-8') as f:
    f.write(wrap_diagram('问题四求解流程','fq4', c))
print('fig_flow_q4.drawio OK')

# ===== System Architecture =====
c = ''
S_SYS = "rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6c8ebf;strokeWidth=2;fontSize=11;fontStyle=1;"
S_H2 = "rounded=1;whiteSpace=wrap;html=1;fillColor=#D5E8D4;strokeColor=#82b366;strokeWidth=2;fontSize=11;fontStyle=1;"
S_NH3 = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;strokeWidth=2;fontSize=11;fontStyle=1;"
S_GRID = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;strokeWidth=2;fontSize=11;fontStyle=1;"
S_STORE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#E1D5E7;strokeColor=#9673a6;strokeWidth=2;fontSize=11;fontStyle=1;"
S_LOAD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F8CECC;strokeColor=#b85450;strokeWidth=1.5;fontSize=11;fontStyle=1;"
S_EARROW = "rounded=1;html=1;strokeWidth=2;strokeColor=#6c8ebf;endArrow=block;endFill=1;"
S_HARROW = "rounded=1;html=1;strokeWidth=2;strokeColor=#82b366;endArrow=block;endFill=1;"
S_NARROW = "rounded=1;html=1;strokeWidth=2;strokeColor=#D6B656;endArrow=block;endFill=1;"

c += cell('wind', bsub('风力发电','装机40MW'), S_SYS, 20, 50, 140, 50)
c += cell('pv', bsub('光伏发电','装机64MW'), S_SYS, 20, 140, 140, 50)
c += cell('bus', b('电力母线'), "rounded=0;whiteSpace=wrap;html=1;fillColor=#F0F4FA;strokeColor=#7B9FC0;strokeWidth=2;fontSize=12;fontStyle=1;", 210, 30, 40, 220)
c += cell('grid', bsub('外部电网','购电/售电'), S_GRID, 180, -40, 100, 50)
c += cell('alkel', bsub('碱性电解槽ALKEL','10MW, 140kg-H2/h'), S_H2, 310, 40, 180, 50)
c += cell('pemel', bsub('质子交换膜PEMEL','10MW, 160kg-H2/h'), S_H2, 310, 110, 180, 50)
c += cell('nh3', bsub('合成氨装置','0.75MW, 1.5t-NH3/h'), S_NH3, 560, 70, 160, 55)
c += cell('store', bsub('储电设备','充放电调节'), S_STORE, 310, 190, 150, 45)
c += cell('eload', bsub('常规电负荷','峰值6MW'), S_LOAD, 310, 255, 150, 42)
c += cell('nh3load', bsub('氨负荷','36-72 t/d'), S_LOAD, 560, 155, 130, 42)
c += edge('ew', 160, 75, 210, 100, S_EARROW+"exitX=1;exitY=0.5;entryX=0;entryY=0.3;")
c += edge('ep', 160, 165, 210, 180, S_EARROW+"exitX=1;exitY=0.5;entryX=0;entryY=0.6;")
c += edge('eg', 230, 10, 230, 30, S_EARROW+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
c += edge('ea', 250, 80, 310, 65, S_EARROW+"exitX=1;exitY=0.2;entryX=0;entryY=0.5;")
c += edge('ep2', 250, 135, 310, 135, S_EARROW+"exitX=1;exitY=0.4;entryX=0;entryY=0.5;")
c += edge('es', 250, 200, 310, 212, S_EARROW+"exitX=1;exitY=0.7;entryX=0;entryY=0.5;")
c += edge('el', 250, 240, 310, 276, S_EARROW+"exitX=1;exitY=0.85;entryX=0;entryY=0.5;")
c += edge('ha', 490, 65, 560, 88, S_HARROW+"exitX=1;exitY=0.5;entryX=0;entryY=0.3;")
c += edge('hp', 490, 135, 560, 108, S_HARROW+"exitX=1;exitY=0.5;entryX=0;entryY=0.7;")
c += edge('na', 640, 125, 625, 155, S_NARROW+"exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

with open('figures/fig_system_arch.drawio', 'w', encoding='utf-8') as f:
    f.write(wrap_diagram('园区系统架构','arch', c, 800, 350))
print('fig_system_arch.drawio OK')

# Verify
import glob
for f in sorted(glob.glob('figures/fig_*.drawio')):
    sz = os.path.getsize(f)
    print(f'  {f} ({sz} bytes)')
print('ALL DRAWIO FILES GENERATED')
