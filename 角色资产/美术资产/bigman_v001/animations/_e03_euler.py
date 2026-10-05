import math
from mathutils import Euler

def show(tag, a, b):
    ea = Euler([math.radians(v) for v in a], 'XYZ')
    eb = Euler([math.radians(v) for v in b], 'XYZ')
    q = (ea.to_matrix().inverted() @ eb.to_matrix()).to_quaternion()
    print("%s  真实旋转步 = %.3f deg" % (tag, math.degrees(abs(q.angle))))
    e = Euler([math.radians(v) for v in b], 'XYZ')
    e.make_compatible(Euler([math.radians(v) for v in a], 'XYZ'))
    got = [math.degrees(v) for v in e]
    step = max(min(abs(x - y) % 360.0, 360.0 - abs(x - y) % 360.0)
               for x, y in zip(a, got))
    print("   make_compatible -> %s   最大数值步 = %.2f" % (
        ["%.1f" % v for v in got], step))

print("--- L 手 f22 -> f23 ---")
show("f22->f23", (157.3, 109.6, -1.6), (-13.1, 67.0, -161.1))
print("--- L 手 f23 -> f24 (参考：已知小步段) ---")
show("f23->f24", (-13.1, 67.0, -161.1), (-21.1, 54.6, -141.2))
