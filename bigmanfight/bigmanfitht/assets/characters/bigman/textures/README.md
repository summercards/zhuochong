# textures/ —— 本角色**没有贴图**

## 结论

`bigman` v001 的 17 个材质**全部是纯色/参数材质**，零张贴图（`images = 0`，`textures = 0`，
三种 GLB —— model / skin / anim —— 都是 0）。

## 这不是漏导出

上游 Blender 工程的材质就是直接给 Base Color / Roughness / Metallic 数值，
没有接任何 Image Texture 节点。所以导出零贴图是**预期结果**，不是打包失误。

## 后果

- 角色是**扁平色块风**（cartoon flat）。想要细节（布料纹理、皮肤毛孔、金属划痕）就得补贴图。
- 优势：包体小、加载快、不会出现贴图丢失导致的粉红/白模、跨平台无压缩格式差异。

## 万一以后要加贴图

放这里，命名 `<char_id>_<part>_<channel>_v<NNN>.png`，例如
`bigman_jacket_basecolor_v001.png`、`bigman_jacket_normal_v001.png`。
贴图进本目录后，需回 Blender 源工程接节点、重新导出三桶 GLB，并更新本文件。
