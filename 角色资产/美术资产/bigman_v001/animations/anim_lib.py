"""anim_lib —— bigman_v001 动画基础库：姿态 / 打帧 / 节奏 / 测量 / 门禁 / 导出。

=============================================================================
一、坐标与轴向语义（全部来自 `probe_axes.py` / `probe_translate.py` 实测，
   表在 `doc/rig_axis_map.md`。**不要凭直觉改，改之前先重跑探针。**）
=============================================================================

世界：+X = 角色左，+Y = 角色身后，+Z = 上，角色正面朝 −Y。
静止身高 1.803 m，鞋底 z = 0，臂轴 z = 1.420。

旋转通道 `rotation_euler = (rx, ry, rz)`，单位**度**：

    躯干/头 (root, pelvis, spine_01, spine_02, chest, neck, head)
        rx > 0   前屈 / 前倾          rx < 0   后仰
        ry       绕纵轴扭转（扭腰 / 转头）
        rz > 0   向角色右侧倾        rz < 0   向左

    双臂 (shoulder / upperarm / forearm / hand)  —— **两侧 rx 同号**
        rx > 0   抬起                rx < 0   落下
        ry       绕臂轴自转（掌心翻转）
        rz       水平前后摆：**左臂 rz>0 = 向后，右臂 rz>0 = 向前**（镜像）

    双腿 (thigh / shin)  —— **两侧 rx 同号**
        rx > 0   向后摆（thigh = 髋后伸；shin = **屈膝**）
        rz > 0   末端向角色右侧 → 左腿 = 内收，右腿 = 外展（同号不同义）

    足   foot:  rx > 0 踮脚（压脚背） / rx < 0 勾脚；rz 内外翻
    趾   toe:   rx > 0 翘趾  / rx < 0 压趾
    手指        rx < 0 握拳（0 = 张开）

平移通道 `location`（骨骼局部空间，**不是世界空间**）：

    实测 root / pelvis：局部 X → 世界 +X，局部 Y → 世界 **+Z**，局部 Z → 世界 **−Y**。
    所以"想让他升高 5 cm"要写 `location = (0, 0.05, 0)`，不是 `(0, 0, 0.05)`。
    本库用 `wloc(dx, dy, dz)` 代为换算，动画脚本一律写**世界位移**。
    （spine_01 及以上的骨是 use_connect=True，**不能平移**，实测 chest.location 无效。）

=============================================================================
二、姿态格式
=============================================================================

    pose = {
        "chest": (6, 0, 0),                 # 骨名 -> (rx, ry, rz) 度
        "shin.L": (26, 0, 0),
        "@loc": {"pelvis": wloc(0, 0, -0.05)},   # 世界位移（米）
    }

`@loc` 的值由 `apply_pose` 内部换算成骨骼 local。**每个关键帧都是完整姿态** ——
库会在打帧前把全部骨归零，所以未列出的骨 = 静止值。这样不会出现
"上一帧的残留值漏进这一帧"。

=============================================================================
三、一个动画的完整流程（见 anim_idle_01.py 的写法）
=============================================================================

    build_action(arm, "Idle_01", keyframes, meta)   # 生成 Action + 元数据
    metrics = sample_animation(arm, action, range)  # 逐帧实测
    report  = run_common_assertions(metrics, meta)  # 通用门禁
    render_pose_sheet(...)                          # 出图给人看
    export_glb(arm, ANIM_GLB)                       # 全 action 导出
"""

import json
import math
import os

import bpy
from mathutils import Vector

OUT_DIR = os.path.abspath(
    r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001")
TPOSE_BLEND = os.path.join(OUT_DIR, "bigman_tpose_v001.blend")
ANIM_BLEND = os.path.join(OUT_DIR, "bigman_anim_v001.blend")
ANIM_GLB = os.path.join(OUT_DIR, "bigman_anim_v001.glb")
PREVIEW_DIR = os.path.join(OUT_DIR, "previews", "anim")
DOC_DIR = os.path.join(OUT_DIR, "doc")

FPS = 60
ARM_NAME = "Character_Rig"

# 腿长（取自 bigman_rig.rig_definition 的 thigh / shin / foot 关节 z）
L_THIGH = 0.900 - 0.490
L_SHIN = 0.490 - 0.078
Z_ANKLE_REST = 0.078
HIP_X = 0.090
ANKLE_X_REST = 0.084


# =============================================================== 基础工具
def wloc(dx, dy, dz):
    """世界位移（米）→ 竖直骨链（root/pelvis）的骨骼局部 location。"""
    return (dx, dz, -dy)


def reset_pose(arm):
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def apply_pose(arm, pose):
    """把姿态写进 pose bone（不打帧）。未列出的骨 = 静止值。"""
    reset_pose(arm)
    locations = pose.get("@loc", {})
    for name, angles in pose.items():
        if name.startswith("@"):
            continue
        pose_bone = arm.pose.bones.get(name)
        if pose_bone is None:
            raise KeyError("姿态引用了不存在的骨：%s" % name)
        pose_bone.rotation_euler = [math.radians(v) for v in angles]
    for name, offset in locations.items():
        pose_bone = arm.pose.bones.get(name)
        if pose_bone is None:
            raise KeyError("位移引用了不存在的骨：%s" % name)
        pose_bone.location = offset
    bpy.context.view_layer.update()


def merge(*poses):
    """后写的覆盖先写的（`@loc` 逐骨合并）。"""
    out = {}
    for pose in poses:
        for key, value in pose.items():
            if key == "@loc":
                out.setdefault("@loc", {}).update(value)
            else:
                out[key] = value
    return out


def blend(pose_a, pose_b, t):
    """两个姿态的线性插值（用于在关键帧之间造中间姿态）。"""
    out = {}
    keys = set(pose_a) | set(pose_b)
    for key in keys:
        if key == "@loc":
            locs = {}
            for bone in set(pose_a.get("@loc", {})) | set(pose_b.get("@loc", {})):
                va = pose_a.get("@loc", {}).get(bone, (0.0, 0.0, 0.0))
                vb = pose_b.get("@loc", {}).get(bone, (0.0, 0.0, 0.0))
                locs[bone] = tuple(a + (b - a) * t for a, b in zip(va, vb))
            out["@loc"] = locs
        else:
            va = pose_a.get(key, (0.0, 0.0, 0.0))
            vb = pose_b.get(key, (0.0, 0.0, 0.0))
            out[key] = tuple(a + (b - a) * t for a, b in zip(va, vb))
    return out


# =============================================================== 两骨 IK
def leg_ik(hip_y, hip_z, ankle_y, ankle_z, tilt_deg=0.0,
           thigh=L_THIGH, shin=L_SHIN):
    """在 YZ 平面内解腿部两骨 IK，返回 (thigh_rx_deg, shin_rx_deg)。

    参数化依据实测语义：thigh 绕 rx 正转时末端向 **+Y（身后）**，
    所以大腿方向 = (sin a, −cos a)，小腿方向 = (sin(a+b), −cos(a+b))，
    b > 0 即小腿相对大腿更向后 = **屈膝**（人腿只能往这个方向弯）。

    `tilt_deg` 是**父链绕世界 X 轴的累计前倾**（`pelvis.rx`，站架里一定要传）。

    为什么非传不可：pose 的 rx 是**父链空间**里的角度，而 IK 的目标点在世界空间。
    pelvis 前倾 3° 会把整条腿一起带转 3°，脚就跟着往前挪 —— 首次试算时
    骨盆多转了 3°，前脚踝被推前 41 mm、鞋底陷进地面 12.75 mm。
    这里把"髋→踝"向量绕 X 反转 tilt，换算进父链空间再解，角度自然抵消。
    （只处理绕 X 的倾角；若以后给 pelvis 加 ry/rz，需要扩成完整旋转矩阵。）
    """
    dy = ankle_y - hip_y
    dz = ankle_z - hip_z
    t = math.radians(tilt_deg)
    dy, dz = dy * math.cos(t) + dz * math.sin(t), -dy * math.sin(t) + dz * math.cos(t)
    q = math.hypot(dy, dz)
    q = max(1e-4, min(q, (thigh + shin) * 0.9995))
    cos_knee = (thigh * thigh + shin * shin - q * q) / (2.0 * thigh * shin)
    knee_inner = math.acos(max(-1.0, min(1.0, cos_knee)))
    bend = math.pi - knee_inner
    delta = math.atan2(shin * math.sin(bend), thigh + shin * math.cos(bend))
    phi = math.atan2(dy, -dz)
    return math.degrees(phi - delta), math.degrees(bend)


# =============================================================== 定向摆骨
def aim_bone(arm, name, direction, twist_deg=0.0):
    """让某根骨的骨长方向（世界）指向 `direction`，返回解出的 euler 角。

    为什么需要它：手臂的欧拉三通道跟"手要落到哪里"之间没有直观映射 ——
    上臂 rx 是**额状面内**的抬落、rz 是水平前后摆、ry 是绕臂轴自转，
    三者复合后想把拳头摆到胸前某点，靠试角度是撞运气。
    先定方向、再让 Blender 反解 euler，是把"造型问题"变成"几何问题"。

    做法：清掉这根骨自身的旋转 → 读它当前的 armature 空间矩阵（父链已经摆好）
    → 用 rotation_difference 求"当前朝向 → 目标方向"的最小旋转 → 设回 matrix。
    `pose_bone.matrix` 的 setter 会自动把它折算成 rotation_euler。

    `twist_deg` 是附加的绕骨轴自转（控制掌心朝向 / 肘窝朝向）。
    """
    pose_bone = arm.pose.bones[name]
    pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    current = pose_bone.matrix.copy()
    basis = current.to_3x3()
    current_dir = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
    want = Vector(direction).normalized()
    quaternion = current_dir.rotation_difference(want)

    target = quaternion.to_matrix().to_4x4() @ current
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()

    if abs(twist_deg) > 1e-9:
        pose_bone.rotation_euler.rotate_axis("Y", math.radians(twist_deg))
        bpy.context.view_layer.update()

    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def bone_direction(arm, name):
    """该骨当前的世界朝向（单位向量）。"""
    basis = arm.pose.bones[name].matrix.to_3x3()
    return (basis @ Vector((0.0, 1.0, 0.0))).normalized()


def keep_world_orientation(arm, name):
    """把该骨的世界朝向钉回 **rest 朝向**（只允许平移），返回解出的 euler。

    用途：支撑脚贴地。

    为什么不用"foot.rx = −(thigh.rx + shin.rx)"这种角度补偿：那个等式只在
    腿的旋转轴恰好是世界 X 轴时成立。站架给 thigh 加了外展 rz，整条下肢绕
    世界 Y 轴偏了 3.4°，shin / foot 的旋转轴跟着偏，于是补偿差 4.3°，
    0.13 m 长的脚掌末端下沉约 10 mm —— 实测鞋底陷地 6.9 mm。
    钉朝向没有这种累积误差：直接令骨的世界 3×3 = rest 的 3×3。
    """
    pose_bone = arm.pose.bones[name]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    current = pose_bone.matrix.copy()
    target = rest_basis.to_4x4()
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


FIST = {}
for _digit in ("index", "middle", "ring", "pinky"):
    for _seg, _angle in ((1, -78), (2, -88), (3, -62)):
        FIST["%s_%02d.L" % (_digit, _seg)] = (_angle, 0.0, 0.0)
        FIST["%s_%02d.R" % (_digit, _seg)] = (_angle, 0.0, 0.0)
for _seg, _angle in ((1, -34), (2, -26), (3, -22)):
    FIST["thumb_%02d.L" % _seg] = (_angle, 0.0, 0.0)
    FIST["thumb_%02d.R" % _seg] = (_angle, 0.0, 0.0)


# =============================================================== 打帧
def build_action(arm, name, keyframes, meta=None, default_interp="BEZIER"):
    """由 [(frame, pose), ...] 生成 Action；通道取并集，保证每帧都有完整通道。

    为什么要取并集：如果某一帧漏掉了某根骨，F-Curve 上就没有那个键，
    Blender 会用**前一个键的值**外推——于是"这帧忘了写 chest"会静默地
    变成"chest 保持上一帧姿态"，动作看起来"卡住了"，但脚本不报错。
    取并集后每帧都显式写入，漏写 = 归零，问题立刻可见。
    """
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True

    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    _bind_slot(arm, action)

    rot_channels = set()
    loc_channels = set()
    for _frame, pose in keyframes:
        for key, value in pose.items():
            if key == "@loc":
                loc_channels.update(value.keys())
            else:
                rot_channels.add(key)
    rot_channels = sorted(rot_channels)
    loc_channels = sorted(loc_channels)

    for frame, pose in keyframes:
        apply_pose(arm, pose)
        for bone_name in rot_channels:
            arm.pose.bones[bone_name].keyframe_insert("rotation_euler",
                                                      frame=frame)
        for bone_name in loc_channels:
            arm.pose.bones[bone_name].keyframe_insert("location", frame=frame)

    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            point.interpolation = default_interp
            point.easing = "AUTO"

    meta = dict(meta or {})
    meta.setdefault("anim_id", name)
    meta.setdefault("fps", FPS)
    meta.setdefault("loop", False)
    meta["frames"] = [int(keyframes[0][0]), int(keyframes[-1][0])]
    for key, value in meta.items():
        try:
            action[key] = value
        except (TypeError, AttributeError):
            pass
    reset_pose(arm)
    return action, meta


def _bind_slot(arm, action):
    """Blender 4.4+ 的 slotted action：把 action 绑定到骨架的默认 slot。"""
    data = arm.animation_data
    if not hasattr(data, "action_slot"):
        return
    try:
        if not action.slots:
            slot = action.slots.new(id_type="OBJECT", name=arm.name)
        else:
            slot = action.slots[0]
        data.action_slot = slot
    except (AttributeError, TypeError, RuntimeError):
        pass


def set_hitstop(action, start_frame, end_frame):
    """打击停顿：把 [start, end] 区间内所有键设成 CONSTANT，姿态完全冻结。

    格斗动画的"命中顿感"靠这个 —— 命中帧与保持帧姿态完全相同，
    且插值设为 CONSTANT，中间不产生任何数值漂移。
    """
    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            if start_frame <= point.co.x <= end_frame:
                point.interpolation = "CONSTANT"


def set_ease(action, frame, mode):
    """调整某一帧上所有键缓动（重击的"爆发"靠 EASE_IN 前蓄、EASE_OUT 后甩）。"""
    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            if abs(point.co.x - frame) < 1e-4:
                point.interpolation = "BEZIER"
                point.easing = mode


# =============================================================== 标记
def add_markers(action, markers):
    """markers: {"ANTIC": 12, "HIT": 26, ...} —— 在时间轴上打帧标记。"""
    for name, frame in markers.items():
        marker = action.pose_markers.new(name)
        marker.frame = frame


# =============================================================== 测量
def mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == "MESH"]


def _object_names():
    return sorted(obj.name for obj in mesh_objects())


def lowest_z_by_side(meshes=None):
    """左右两半的最低点世界 z —— 用它判"脚贴地 / 陷地 / 悬空"。

    按**顶点世界 x 的符号**分左右，而不是按对象名：这样躺倒、跳跃、
    单脚离地等任何姿态都能量，不依赖"鞋叫 Shoe_L"这种命名假设。
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low = {1: 1e9, -1: 1e9}
    for obj in (meshes if meshes is not None else mesh_objects()):
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            side = 1 if point.x >= 0.0 else -1
            low[side] = min(low[side], point.z)
        evaluated.to_mesh_clear()
    return {"L": low[1], "R": low[-1]}


def lowest_point_by_side(meshes=None):
    """左右两半各自**最低的那个顶点**（世界坐标，返回 (x, y, z)）。

    `lowest_z_by_side` 只回答"最低多少"，回答不了"最低点在前还是在后"——
    而"脚尖先落 / 脚跟先落"这类判据问的正是后者（A04 `toe_first_contact_ok`）。
    分左右同样按**顶点世界 x 的符号**，不依赖对象命名。
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low = {1: None, -1: None}
    for obj in (meshes if meshes is not None else mesh_objects()):
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            side = 1 if point.x >= 0.0 else -1
            current = low[side]
            if current is None or point.z < current[2]:
                low[side] = (point.x, point.y, point.z)
        evaluated.to_mesh_clear()
    return {"L": low[1], "R": low[-1]}


FOOT_MESHES = {
    "L": ("Shoe_Heel_L", "Shoe_Sole_L", "Shoe_Toe_Cap_L", "Shoe_Upper_L"),
    "R": ("Shoe_Heel_R", "Shoe_Sole_R", "Shoe_Toe_Cap_R", "Shoe_Upper_R"),
}


def lowest_point_of(objects):
    """一组网格对象里**最低的那个顶点**（世界坐标，返回 (x, y, z)）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    best = None
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            if best is None or point.z < best[2]:
                best = (point.x, point.y, point.z)
        evaluated.to_mesh_clear()
    return best


def foot_lowest_by_side():
    """按**鞋对象**分左右测脚底最低点，返回 {"L": (x,y,z), "R": (x,y,z)}。

    为什么不能用 `lowest_z_by_side`：它按**顶点世界 x 的符号**分左右，两只脚
    靠近时（Run 的踏宽只有 ±85 mm、鞋宽 ~90 mm，两侧网格在 x≈0 附近**重叠**）
    左右会**串门**。实测 `Run@48`：`lowest_z_by_side` 给出 R = 8.98 mm，
    而 R 鞋的真值是 **108.18 mm** —— 那个 8.98 是**左鞋**的内侧边缘。
    差 99 mm 足以让"哪只脚落地"判错（A06 要按脚判落地窗口，必须精确）。
    """
    low = {}
    for side, names in FOOT_MESHES.items():
        objects = [bpy.data.objects[name] for name in names
                   if name in bpy.data.objects]
        low[side] = lowest_point_of(objects)
    return low


def world_tip_deg(arm, name):
    """骨相对 **rest** 绕世界 X 轴的转角（度，带符号）。

    + = 骨末端朝下转（脚：压脚背 / 踮脚 / 脚尖先落）
    − = 骨末端朝上转（脚：勾脚尖 / 脚跟先落）
    在 YZ 平面里量"rest 前向轴 → 当前前向轴"的有符号夹角，与 `add_world_rx`
    施加的角度是同一口径（armature 空间 = 世界，验证用）。
    """
    pose_bone = arm.pose.bones[name]

    def forward(basis):
        return basis @ Vector((0.0, 1.0, 0.0))

    rest = forward(pose_bone.bone.matrix_local.to_3x3())
    current = forward(pose_bone.matrix.to_3x3())
    return math.degrees(math.atan2(
        rest.y * current.z - rest.z * current.y,
        rest.y * current.y + rest.z * current.z))


def bone_world(arm, name, which="head"):
    pose_bone = arm.pose.bones[name]
    point = pose_bone.head if which == "head" else pose_bone.tail
    return arm.matrix_world @ point


def bone_head_map(arm, names):
    return {name: bone_world(arm, name, "head") for name in names}


PROBE_BONES = ("pelvis", "chest", "neck", "head", "hand.L", "hand.R",
               "forearm.L", "forearm.R", "upperarm.L", "upperarm.R",
               "foot.L", "foot.R", "toe.L", "toe.R",
               "shoulder.L", "shoulder.R")

# 骨**末端**才是要看的量：肩的起伏在肩峰（= upperarm.head），
# 胸腔的起伏在胸骨顶（= chest.tail = neck.head），拳头在 hand.tail。
# 早期门禁量的是各骨的 head —— 那是关节根部，绕着它转多久它都不动，
# 于是"呼吸幅度 1.67 mm（不可见）"这种假红就出来了。
PROBE_TAILS = ("hand.L", "hand.R", "upperarm.L", "upperarm.R", "chest",
               "head", "foot.L", "foot.R", "toe.L", "toe.R")

PROBE_KEYS = PROBE_BONES + tuple(name + ".tail" for name in PROBE_TAILS)


def sample_animation(arm, action, frame_start, frame_end, meshes=None):
    """逐帧实测：骨骼世界坐标 + 左右最低点。返回可直接做门禁的字典列表。"""
    scene = bpy.context.scene
    previous_action = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    _bind_slot(arm, action)

    samples = []
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        record = {"frame": frame}
        for name in PROBE_BONES:
            if name in arm.pose.bones:
                record[name] = tuple(bone_world(arm, name, "head"))
        for name in PROBE_TAILS:
            if name in arm.pose.bones:
                record[name + ".tail"] = tuple(bone_world(arm, name, "tail"))
        record["low"] = lowest_z_by_side(meshes)
        record["euler"] = {
            name: tuple(math.degrees(v) for v in pose_bone.rotation_euler)
            for name, pose_bone in arm.pose.bones.items()
            if any(abs(v) > 1e-9 for v in pose_bone.rotation_euler)
            or any(abs(v) > 1e-9 for v in pose_bone.location)
        }
        samples.append(record)

    if previous_action is not None:
        arm.animation_data.action = previous_action
    return samples


# =============================================================== 通用门禁
def run_common_assertions(samples, meta, foot_probe=("toe.L", "toe.R"),
                          slide_tolerance_mm=3.0):
    """通用门禁：循环闭合 / 脚位移 / 贴地 / 无跳变 / 无瞬停。"""
    result = {}
    first, last = samples[0], samples[-1]

    if meta.get("loop"):
        worst_angle = 0.0
        worst_move = 0.0
        for name in set(first["euler"]) | set(last["euler"]):
            ea = first["euler"].get(name, (0.0, 0.0, 0.0))
            eb = last["euler"].get(name, (0.0, 0.0, 0.0))
            worst_angle = max(worst_angle, max(abs(a - b) for a, b in zip(ea, eb)))
        for name in PROBE_KEYS:
            if name in first and name in last:
                worst_move = max(worst_move,
                                 (Vector(first[name]) - Vector(last[name])).length)
        result["loop_seamless"] = worst_angle <= 0.5 and worst_move <= 0.0005
        result["loop_angle_deg"] = round(worst_angle, 4)
        result["loop_move_mm"] = round(worst_move * 1000.0, 3)
    else:
        result["loop_seamless"] = None

    for name in foot_probe:
        if name not in first:
            continue
        xs = [Vector(sample[name]).x for sample in samples]
        ys = [Vector(sample[name]).y for sample in samples]
        zs = [Vector(sample[name]).z for sample in samples]
        travel = max(math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0,
                     (max(zs) - min(zs)) * 1000.0)
        result["foot_travel_mm_" + name] = round(travel, 2)
        result["no_foot_slide_" + name] = travel <= slide_tolerance_mm

    lows = [min(sample["low"]["L"], sample["low"]["R"]) for sample in samples]
    result["ground_min_mm"] = round(min(lows) * 1000.0, 2)
    result["ground_contact_ok"] = -2.0 <= min(lows) * 1000.0 <= 6.0

    worst_step = 0.0
    worst_step_at = None
    for index in range(1, len(samples)):
        for name in set(samples[index]["euler"]) | set(samples[index - 1]["euler"]):
            ea = samples[index - 1]["euler"].get(name, (0.0, 0.0, 0.0))
            eb = samples[index]["euler"].get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step = step
                worst_step_at = (samples[index]["frame"], name)
    result["max_frame_step_deg"] = round(worst_step, 3)
    result["max_frame_step_at"] = worst_step_at
    result["no_teleport"] = worst_step <= 25.0

    move_span = {}
    for name in ("pelvis", "chest", "head", "hand.L", "hand.R"):
        if name not in first:
            continue
        points = [Vector(sample[name]) for sample in samples]
        move_span[name] = round(max(
            (p - points[0]).length for p in points) * 1000.0, 2)
    result["bone_travel_mm"] = move_span
    return result


# =============================================================== 渲染
def setup_scene():
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    return scene


def render_still(camera, path, location, target, ortho_scale, res=(780, 1200)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = res
    camera.location = Vector(location)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (
        Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


VIEW_SIDE = ("side", (4.2, 0.0, 0.92), (0.0, 0.0, 0.92), 2.10, (780, 1100))
VIEW_FRONT = ("front", (0.0, -4.6, 0.92), (0.0, 0.0, 0.92), 2.10, (780, 1100))
VIEW_3Q = ("three_quarter", (3.0, -3.4, 1.10), (0.0, 0.0, 1.00), 2.10,
           (780, 1100))


def render_pose_sheet(arm, action, frames, prefix, views=(VIEW_SIDE,),
                      out_dir=None):
    """把指定帧在指定视角渲成静帧，文件名 `{prefix}_{view}_f{frame:04d}.png`。"""
    out_dir = out_dir or PREVIEW_DIR
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    camera = bpy.data.objects.get("Presentation_Camera")
    if camera is None:
        raise RuntimeError("展示相机不见了：Presentation_Camera")
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    _bind_slot(arm, action)

    outputs = []
    for frame in frames:
        scene.frame_set(frame)
        for name, location, target, scale, res in views:
            path = os.path.join(out_dir, "%s_%s_f%04d.png"
                                % (prefix, name, frame))
            outputs.append(render_still(camera, path, location, target, scale,
                                        res))
    return outputs


def render_animation_mp4(arm, action, path, view=VIEW_SIDE, samples=2):
    """把整段动作渲成 mp4（给主人过目用）。samples 越高越慢。"""
    scene = bpy.context.scene
    camera = bpy.data.objects.get("Presentation_Camera")
    name, location, target, scale, res = view
    scene.render.resolution_x, scene.render.resolution_y = res
    camera.location = Vector(location)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    camera.rotation_euler = (
        Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.fps = FPS
    scene.render.filepath = path

    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    _bind_slot(arm, action)
    start, end = action.frame_range
    scene.frame_start, scene.frame_end = int(start), int(end)
    bpy.ops.render.render(animation=True)
    scene.render.image_settings.file_format = "PNG"
    return path


# =============================================================== 工程与导出
def open_animation_project():
    """打开动画工程（不存在则从 T-pose 定稿复制一份），返回 (arm, meshes)。

    **绝不写回 `bigman_tpose_v001.blend`** —— 那是已通过门禁的角色定稿，
    动画产生的任何数据都只落在 `bigman_anim_v001.blend` 里。
    """
    if not os.path.exists(ANIM_BLEND):
        bpy.ops.wm.open_mainfile(filepath=TPOSE_BLEND)
        bpy.ops.wm.save_as_mainfile(filepath=ANIM_BLEND)
    else:
        bpy.ops.wm.open_mainfile(filepath=ANIM_BLEND)
    arm = bpy.data.objects[ARM_NAME]
    return arm, mesh_objects()


def save_project():
    bpy.ops.wm.save_as_mainfile(filepath=ANIM_BLEND)
    return ANIM_BLEND


def export_glb(arm, path=None):
    path = path or ANIM_GLB
    bpy.ops.object.select_all(action="DESELECT")
    count = 0
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
            count += 1
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        # 必须为 True：T-pose 定稿的 GLB 是应用 subsurf 后导出的，
        # 动画包若用 False 会导出未细分的控制网格 —— 两包网格密度不一致，
        # 引擎里替换时会跳形。
        export_apply=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_bake_animation=False,
        export_force_sampling=True,
        export_optimize_animation_size=False,
        export_cameras=False,
        export_lights=False,
    )
    return count


def report(name, payload):
    print("%s %s" % (name, json.dumps(payload, ensure_ascii=False,
                                      default=str)))
