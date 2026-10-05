import os, sys
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A
PRE = os.path.join(A.OUT_DIR, "previews", "anim")

# wide 视参数：ortho 3.60 作用于长边(高 1100) -> mm/px = 3.2727；中心 y=+250，cam_z 0.95
MM = 3.60 / 1100.0 * 1000.0
COL_C = 390.0
ROW_FLOOR = (3.60 / 2.0 - 0.95) / (3.60 / 1100.0)

def y2col(y):  return COL_C + (y - 250.0) / MM
def z2row(z):  return ROW_FLOOR + z / MM

# Jacket_Hem 世界包围盒（probe_c11_belt 实测，逐帧恒定）
HEM = {"Jacket_Hem": (-188.78, -121.94, 903.0, 188.78, 129.03, 926.0),
       "Jacket_Hem_Line": (-185.92, -119.96, 897.5, 185.92, 126.03, 901.5)}
for n, (x0, y0, z0, x1, y1, z1) in HEM.items():
    print("%-18s cols %.1f..%.1f  rows %.1f..%.1f" % (
        n, y2col(y0), y2col(y1), z2row(z0), z2row(z1)))

C0, C1 = int(np.floor(y2col(-121.94))), int(np.ceil(y2col(129.03)))
R0, R1 = int(np.floor(z2row(897.5))), int(np.ceil(z2row(926.0)))
print("HEM BOX cols %d..%d rows %d..%d" % (C0, C1, R0, R1))

def load(name):
    p = os.path.join(PRE, name + ".png")
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    a = px[:, :, 3]
    return (a > 0.5) if float(a.min()) < 0.5 else (px[:, :, :3].min(axis=2) < 0.92)

def ext(m):
    r = np.where(m.any(axis=1))[0]; c = np.where(m.any(axis=0))[0]
    return (int(r.min()), int(r.max()), int(c.min()), int(c.max())) if r.size else None

for f in (0, 4, 5, 12, 20, 22, 25, 34, 46):
    m = load("getupbwide_side_f%04d" % f)
    m2 = m.copy(); m2[R0:R1 + 1, C0:C1 + 1] = False
    print("f%-3d  raw=%-26s  hem_stripped=%-26s" % (f, ext(m), ext(m2)))
