import math
from mathutils import Euler, Matrix

def M(a):
    return Euler([math.radians(v) for v in a], 'XYZ').to_matrix()

f22 = (157.3, 109.6, -1.6)
f23 = (-13.1, 67.0, -161.1)

# 1) 验证「翻转族」是否严格等价（矩阵逐元素差）
alt = (f23[0] + 180.0, 180.0 - f23[1], f23[2] + 180.0)
d = max(abs(x - y) for r1, r2 in zip(M(f23), M(alt)) for x, y in zip(r1, r2))
print("翻转族矩阵最大逐元素差 =", d)

# 2) 穷举候选，选最大数值步最小者
best, best_step = None, 1e9
for base in [f23, alt]:
    for kx in (-1, 0, 1):
        for ky in (-1, 0, 1):
            for kz in (-1, 0, 1):
                c = (base[0] + 360 * kx, base[1] + 360 * ky, base[2] + 360 * kz)
                step = max(abs(x - y) for x, y in zip(f22, c))
                if step < best_step:
                    best, best_step = c, step
print("最优候选 =", ["%.1f" % v for v in best], " 最大数值步 = %.2f" % best_step)
d2 = max(abs(x - y) for r1, r2 in zip(M(f23), M(best)) for x, y in zip(r1, r2))
print("最优候选矩阵最大逐元素差 =", d2)
