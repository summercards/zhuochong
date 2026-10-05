# -*- coding: utf-8 -*-
"""从 bigman_tpose_v001.blend 导出**纯几何** GLB（无骨架、无蒙皮、无动画）。

用途：游戏资产规范里的「模型」桶 —— 供碰撞体生成、剪影对照、LOD 基准使用。
绝不改动/另存源 .blend。

用法:
    blender --background --factory-startup <tpose.blend> --python export_mesh_only.py -- <out.glb>
"""
import bpy
import os
import sys


def main():
    argv = sys.argv
    out = argv[argv.index("--") + 1]
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # 1) 复制全部网格对象（保留原对象供后续删除）
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.duplicate()
    dups = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    print("DUP %d meshes" % len(dups))

    # 2) 副本：去掉骨架修改器 + 断开父子（保持世界变换）
    for o in dups:
        for m in list(o.modifiers):
            if m.type == "ARMATURE":
                o.modifiers.remove(m)
        if o.parent is not None:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
        # 清掉仅副本残留的动画数据
        o.animation_data_clear()

    # 3) 删除所有原始对象（含骨架）
    for o in list(bpy.data.objects):
        if o in dups:
            continue
        bpy.data.objects.remove(o, do_unlink=True)

    # 4) 清掉全部 Action，确保导出零动画
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)

    # 5) 导出
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_skins=False,
        export_animations=False,
        export_yup=True,
        export_materials="EXPORT",
        export_normals=True,
        export_tangents=False,
        export_texcoords=True,
    )
    print("EXPORTED %s" % out)
    print("SIZE %d bytes" % os.path.getsize(out))
    print("OBJECTS_LEFT %d" % len([o for o in bpy.data.objects if o.type == "MESH"]))


main()
