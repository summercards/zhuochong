# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import json
import tkinter as tk
from PIL import Image, ImageTk
import ctypes

# ==========================================
# ▼▼▼ 速度配置 ▼▼▼
RAPID_FIRE_DELAY = 0.08      
AFK_TIMEOUT = 10.0           
ATTACK_FRAME_SPEED = 30      
IDLE_FRAME_SPEED = 200       
BONFIRE_FRAME_SPEED = 120    
# ==========================================

SOULS_PER_LEVEL_BASE = 20

# 常用键位 (Polling用)
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_Q = 0x51
VK_W = 0x57

SOUL_QUOTES = [
    "火已渐熄...",
    "到处都是活尸...",
    "赞美太阳！",
    "寻找灵魂...",
    "余火尚存...",
    "喵... (严肃地)",
    "菜就多练 (Git gud)",
    "篝火已点燃。"
]

DATA_FILE = "save_data.json"

class KnightPet(tk.Tk):
    def __init__(self, base_dir):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.wm_attributes("-transparentcolor", "white")
        except tk.TclError:
            pass

        self.data_file_path = os.path.join(base_dir, DATA_FILE)
        self.data = self._load_data()
        self.last_interaction_time = time.time()
        self.state = "IDLE" 
        self.is_resting = False
        self.last_fire_time = 0 
        self.attack_frame_index = 0
        self.bonfire_frame_index = 0
        self.idle_frame_index = 0
        self.monster_ids = [] 

        self.base_width = 200
        
        # 路径加载
        idle_dir = os.path.join(base_dir, "images", "idle")
        self.idle_frames = self._load_frames(idle_dir)
        if not self.idle_frames:
            img_path_fallback = os.path.join(base_dir, "images", "knight.png")
            if os.path.exists(img_path_fallback):
                self._load_fallback_idle(img_path_fallback)

        attack_dir = os.path.join(base_dir, "images", "attack")
        self.attack_frames = self._load_frames(attack_dir)

        bonfire_dir = os.path.join(base_dir, "images", "bonfire")
        self.bonfire_frames = self._load_frames(bonfire_dir)

        self.canvas_width = self.base_width + 250 
        self.canvas_height = self.h_size + 150 
        
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height,
                                highlightthickness=0, bg="white")
        self.canvas.pack()

        self.center_x = self.base_width // 2 + 50
        self.base_y = self.h_size // 2 + 80 
        self.sun_aura_id = self.canvas.create_oval(0,0,0,0, fill="", outline="", state='hidden')
        
        first_img = self.idle_frames[0] if self.idle_frames else self.knight_photo_idle_fallback
        self.knight_id = self.canvas.create_image(self.center_x, self.base_y, image=first_img)
        
        self.bubble_rect = self.canvas.create_rectangle(0,0,0,0, fill="#222", outline="#555", width=2, state='hidden')
        self.bubble_text = self.canvas.create_text(0,0, text="", fill="#ddd", font=("Microsoft YaHei", 9), state='hidden')
        self.hud_text = self.canvas.create_text(0,0, text="", fill="#ffd700", font=("Microsoft YaHei", 10, "bold"))
        self.xp_bar_bg = self.canvas.create_rectangle(0,0,0,0, fill="#333", outline="#555")
        self.xp_bar_fill = self.canvas.create_rectangle(0,0,0,0, fill="#ffd700", outline="")
        self._update_hud()

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - self.canvas_width - 20
        y = sh - self.canvas_height - 50
        self.geometry(f"{self.canvas_width}x{self.canvas_height}+{x}+{y}")

        self.after(100, self._animate_idle_loop) 
        self.after(1000, self._check_afk)
        self.after(5000, self._random_talk_loop)
        self._setup_inputs_and_drag()

    # --- Windows API Polling ---
    def _is_key_down(self, key_code):
        return ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000 != 0

    def _check_any_key(self):
        for k in range(0x30, 0x5A + 1): 
            if self._is_key_down(k): return True
        for k in [0x0D, 0x10, 0x11, 0x12, 0x20]:
            if self._is_key_down(k): return True
        return False

    def _input_loop(self):
        try:
            now = time.time()
            if now - self.last_fire_time >= RAPID_FIRE_DELAY:
                if self._is_key_down(VK_SPACE):
                    self._trigger_action("PRAISE")
                elif self._is_key_down(VK_Q) or self._is_key_down(VK_W) or self._is_key_down(VK_SHIFT):
                    self._trigger_action("BLOCK")
                elif self._check_any_key():
                    self._trigger_action("ATTACK")
        except Exception:
            pass
        self.after(20, self._input_loop)

    # --------------------------------------------------------

    def _load_fallback_idle(self, path):
        pil_image = Image.open(path)
        w_percent = (self.base_width / float(pil_image.size[0]))
        self.h_size = int((float(pil_image.size[1]) * float(w_percent)))
        pil_resized = pil_image.resize((self.base_width, self.h_size), Image.LANCZOS)
        self.knight_photo_idle_fallback = ImageTk.PhotoImage(pil_resized)

    def _load_frames(self, folder_path):
        frames = []
        if not os.path.exists(folder_path): return frames
        h_target = 0
        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        for i, file in enumerate(files):
            path = os.path.join(folder_path, file)
            try:
                pil_img = Image.open(path)
                w_percent = (self.base_width / float(pil_img.size[0]))
                if h_target == 0:
                    h_target = int((float(pil_img.size[1]) * float(w_percent)))
                    self.h_size = h_target 
                pil_resized = pil_img.resize((self.base_width, h_target), Image.LANCZOS)
                frames.append(ImageTk.PhotoImage(pil_resized))
            except: pass
        return frames

    def _load_data(self):
        default = {"level": 1, "current_xp": 0, "total_souls": 0}
        if os.path.exists(self.data_file_path):
            try:
                with open(self.data_file_path, "r") as f: return json.load(f)
            except: return default
        return default

    def _save_data(self):
        try:
            with open(self.data_file_path, "w") as f: json.dump(self.data, f)
        except: pass

    def _get_xp_needed(self):
        return self.data["level"] * 10 + SOULS_PER_LEVEL_BASE

    def _update_hud(self):
        txt = f"等级 {self.data['level']} | 灵魂 {self.data['total_souls']}"
        text_y = self.base_y + self.h_size//2 + 15
        self.canvas.coords(self.hud_text, self.center_x, text_y)
        self.canvas.itemconfigure(self.hud_text, text=txt)
        bw, bh = 120, 6
        bx = self.center_x - bw // 2
        by = text_y + 10
        self.canvas.coords(self.xp_bar_bg, bx, by, bx + bw, by + bh)
        need = self._get_xp_needed()
        curr = self.data["current_xp"]
        pct = min(1.0, curr / need) if need > 0 else 0
        fill_w = int(bw * pct)
        if fill_w > 0:
            self.canvas.coords(self.xp_bar_fill, bx, by, bx + fill_w, by + bh)
            self.canvas.itemconfigure(self.xp_bar_fill, state='normal')
        else:
            self.canvas.itemconfigure(self.xp_bar_fill, state='hidden')

    def _setup_inputs_and_drag(self):
        # 拖拽数据初始化
        self._drag_data = {
            "offset_x": 0, "offset_y": 0, 
            "is_moving": False
        }
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.bind("<B1-Motion>", self._on_drag_motion)
        
        self.after(20, self._input_loop)
        # 注意：这里移除了 bind <Button-1>，统一在 _on_drag_stop 里处理点击

    # =======================================================
    # ▼▼▼ 修复：使用偏移量计算法 (Offset Method) ▼▼▼
    # 这能保证你点哪拖哪，绝不乱跳
    # =======================================================
    def _on_drag_start(self, event):
        # 记录你点击的位置 相对于 窗口左上角的距离
        # event.x / event.y 本身就是相对于窗口的坐标
        self._drag_data["offset_x"] = event.x
        self._drag_data["offset_y"] = event.y
        self._drag_data["is_moving"] = False 

    def _on_drag_motion(self, event):
        # 计算新位置 = 当前屏幕鼠标位置 - 刚才记录的偏移量
        # 这样窗口左上角就会始终保持和鼠标的相对距离不变
        new_x = event.x_root - self._drag_data["offset_x"]
        new_y = event.y_root - self._drag_data["offset_y"]
        
        # 简单的防抖动，防止轻微手抖导致无法点击
        # 只有移动超过一点点才算拖拽
        self._drag_data["is_moving"] = True
        self.geometry(f"+{new_x}+{new_y}")

    def _on_drag_stop(self, event):
        # 只有当【没有发生移动】时，才判定为“点击攻击”
        # 如果刚才移动了，松开鼠标时什么都不做（只是放下）
        if not self._drag_data["is_moving"]:
            self._trigger_action("ATTACK")
        
        self._drag_data["is_moving"] = False
    # =======================================================

    def _trigger_action(self, action_type):
        self.last_fire_time = time.time()
        self.last_interaction_time = self.last_fire_time
        if self.is_resting:
            self._wake_up()
            return
        if self.state != action_type:
            self._reset_pose()
        self.state = action_type
        self._gain_xp()
        if action_type == "ATTACK": 
            self._animate_attack_sequence()

    def _reset_pose(self):
        if self.idle_frames:
            self.canvas.itemconfig(self.knight_id, image=self.idle_frames[0])
        elif hasattr(self, 'knight_photo_idle_fallback'):
            self.canvas.itemconfig(self.knight_id, image=self.knight_photo_idle_fallback)
        self.canvas.coords(self.knight_id, self.center_x, self.base_y)
        self.canvas.itemconfigure(self.sun_aura_id, state='hidden')
        self.canvas.delete("temp_effect")
        self._clear_monster() 

    def _gain_xp(self):
        self.data["total_souls"] += 1
        self.data["current_xp"] += 1
        need = self._get_xp_needed()
        if self.data["current_xp"] >= need:
            self.data["level"] += 1
            self.data["current_xp"] = 0 
            self._show_bubble("灵魂等级提升！", 2000, "#ffd700")
            self.canvas.config(bg="yellow")
            self.after(50, lambda: self.canvas.config(bg="white"))
        self._update_hud()
        self._save_data()

    def _spawn_monster(self):
        mx = self.center_x - 80
        my = self.base_y + 40
        body = self.canvas.create_oval(mx-20, my-20, mx+20, my+10, fill="#222", outline="black", tags="monster")
        eye1 = self.canvas.create_oval(mx-10, my-10, mx-4, my-4, fill="red", tags="monster")
        eye2 = self.canvas.create_oval(mx+4, my-10, mx+10, my-4, fill="red", tags="monster")
        self.monster_ids = [body, eye1, eye2]

    def _move_monster(self):
        if self.monster_ids:
            self.canvas.move("monster", -15, -8)

    def _clear_monster(self):
        self.canvas.delete("monster")
        self.monster_ids = []

    def _animate_attack_sequence(self):
        if not self.attack_frames:
            self.canvas.scale(self.knight_id, self.center_x, self.base_y, 1.2, 1.2)
            self.after(80, lambda: self._reset_pose())
            return
        self._spawn_monster()
        self.attack_frame_index = 0
        self._play_next_frame()

    def _play_next_frame(self):
        if self.state != "ATTACK": return
        if self.attack_frame_index < len(self.attack_frames):
            frame = self.attack_frames[self.attack_frame_index]
            self.canvas.itemconfig(self.knight_id, image=frame)
            self._move_monster()
            self.attack_frame_index += 1
            self.after(ATTACK_FRAME_SPEED, self._play_next_frame)
        else:
            self._reset_pose()
            self.state = "IDLE"

    def _animate_idle_loop(self):
        if self.is_resting:
            if self.bonfire_frames:
                frame = self.bonfire_frames[self.bonfire_frame_index]
                self.canvas.itemconfig(self.knight_id, image=frame)
                self.bonfire_frame_index = (self.bonfire_frame_index + 1) % len(self.bonfire_frames)
            self.after(BONFIRE_FRAME_SPEED, self._animate_idle_loop)
            return

        if self.state == "IDLE":
            if self.idle_frames:
                frame = self.idle_frames[self.idle_frame_index]
                self.canvas.itemconfig(self.knight_id, image=frame)
                self.idle_frame_index = (self.idle_frame_index + 1) % len(self.idle_frames)
            self.after(IDLE_FRAME_SPEED, self._animate_idle_loop)
            return
        self.after(100, self._animate_idle_loop)

    def _check_afk(self):
        if not self.is_resting and time.time() - self.last_interaction_time > AFK_TIMEOUT:
            self._go_to_rest()
        self.after(2000, self._check_afk)

    def _go_to_rest(self):
        self.is_resting = True
        self.state = "REST"
        self._show_bubble("篝火已点燃...", 2000)
        self.bonfire_frame_index = 0

    def _wake_up(self):
        self.is_resting = False
        self.state = "IDLE"
        self._show_bubble("使命在召唤。", 1000)
        self._reset_pose()

    def _random_talk_loop(self):
        if not self.is_resting and random.random() < 0.2:
            self._show_bubble(random.choice(SOUL_QUOTES))
        self.after(random.randint(10000, 20000), self._random_talk_loop)

    def _show_bubble(self, text, duration=3000, color="#ddd"):
        self.canvas.itemconfigure(self.bubble_text, text=text, fill=color, state='normal')
        bbox = self.canvas.bbox(self.bubble_text)
        if bbox:
            pad = 5
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            nx = self.center_x
            ny = self.base_y - self.h_size//2 - 30
            self.canvas.coords(self.bubble_text, nx, ny)
            self.canvas.coords(self.bubble_rect, nx - w//2 - pad, ny - h//2 - pad, nx + w//2 + pad, ny + h//2 + pad)
            self.canvas.itemconfigure(self.bubble_rect, state='normal')
            self.canvas.tag_raise(self.bubble_rect)
            self.canvas.tag_raise(self.bubble_text)
        self.after(duration, self._hide_bubble)

    def _hide_bubble(self):
        self.canvas.itemconfigure(self.bubble_text, state='hidden')
        self.canvas.itemconfigure(self.bubble_rect, state='hidden')

    def destroy(self):
        self._save_data()
        super().destroy()

def main():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        app = KnightPet(base_dir)
        app.mainloop()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("错误", f"发生错误:\n{e}")

if __name__ == "__main__":
    main()