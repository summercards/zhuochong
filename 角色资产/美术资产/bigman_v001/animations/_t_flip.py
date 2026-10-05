import math
from mathutils import Euler, Matrix
def M(t): return Euler([math.radians(v) for v in t], 'XYZ').to_matrix()
worst = 0.0
for a in (-113.1, -30.0, 20.0, 175.0):
    for b in (-64.9, -79.6, 40.0, -120.0):
        for c in (-2.2, 100.0, -179.0):
            m0 = M((a, b, c))
            m1 = M((a + 180.0, 180.0 - b, c + 180.0))
            d = max(abs(m0[i][j] - m1[i][j]) for i in range(3) for j in range(3))
            worst = max(worst, d)
print("FLIP_MAX_ERR", worst)
# 同时验证「矩阵 -> to_euler('XYZ')」是否能还原
e = Euler([math.radians(v) for v in (-113.1, -64.9, -2.2)], 'XYZ')
back = e.to_matrix().to_euler('XYZ')
print("ROUNDTRIP", [round(math.degrees(v), 4) for v in back])
