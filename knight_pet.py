# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import ctypes

# ==========================================
# ▼▼▼ 游戏配置 ▼▼▼
RAPID_FIRE_DELAY = 0.08      
AFK_TIMEOUT = 10.0           
ATTACK_FRAME_SPEED = 30      
IDLE_FRAME_SPEED = 200       
BONFIRE_FRAME_SPEED = 120    
SOULS_PER_LEVEL_BASE = 20

# 掉落率 (1%)
LOOT_DROP_RATE = 0.01 

# 💰 回收价格表
SELL_PRICES = {
    "white": 10, "green": 50, "blue": 200, "purple": 1000, "gold": 5000,
    "chest": 0 
}

# 宝箱消耗
CHEST_COSTS = {
    "white": 100, "green": 500, "blue": 2000, "purple": 5000, "gold": 20000
}

VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_Q = 0x51
VK_W = 0x57

SOUL_QUOTES = [
    "火已渐熄...", "到处都是活尸...", "赞美太阳！", "寻找灵魂...",
    "余火尚存...", "喵... (严肃地)", "菜就多练 (Git gud)", "篝火已点燃。"
]

# ==========================================
# ▼▼▼ 📦 物品数据库 (注意信件命名格式) ▼▼▼
# ==========================================
# 格式：系列名: 章节名
ITEMS_DB = [
    # --- 宝箱 ---
    ("破旧的木箱", "📦", "布满灰尘的箱子，不知道里面有什么。", "white", "chest", None),
    ("铁皮补给箱", "🧰", "骑士团的制式补给箱，锁扣很结实。", "green", "chest", None),
    ("贵族珍藏箱", "💎", "装饰华丽的箱子，通常装有不错的宝物。", "blue", "chest", None),
    ("深渊沉淀箱", "⬛", "从深渊打捞上来的箱子，散发着不祥的气息。", "purple", "chest", None),
    ("葛温的宝藏", "🌞", "闪耀着太阳光辉的宝箱，传说中的神物。", "gold", "chest", None),

    # --- 🤍 白色 ---
    ("破旧的猫薄荷", "🌿", "虽然干枯了，但依然能让猫咪兴奋一小会儿。", "white", "toy", None),
    ("打结的毛线球", "🧶", "一个被抓得乱七八糟的毛线球，经典的玩具。", "white", "toy", None),
    # 家书系列
    ("家书: 第一章", "📜", "【致我最爱的孩子】\n\n当你看到这封信时，我已经踏上了寻找初火的旅途。\n村里的长者说，只有点燃初火，才能驱散这漫长的黑夜。\n我把家里的钥匙埋在了那棵老橡树下，如果我不回来，房子就归你了。\n\n—— 爱你的父亲", "white", "letter", None),
    
    # --- 💚 绿色 ---
    ("发条老鼠", "🐁", "上紧发条就会满地乱跑的机械玩具。", "green", "toy", None),
    # 家书系列
    ("家书: 第二章", "📜", "【致我最爱的孩子】\n\n路途比我想象的艰难。\n洛斯里克的城墙上到处都是活尸，它们穿着破烂的盔甲，漫无目的地游荡。\n我必须小心翼翼地穿过这里。\n我有些后悔出来了，但我必须前进。\n\n如果我回不来，请把我的剑交给铁匠安德烈，他知道该怎么做。", "green", "letter", None),
    ("太阳徽章盾", "🛡️", "【太阳套装】画着滑稽太阳的盾牌，看起来充满希望。", "green", "equip", "solar"),
    
    # --- 💙 蓝色 ---
    ("骑士的日记", "📘", "【洋葱骑士的观察日记】\n\n那个自称洋葱骑士的家伙在井里睡着了，真拿他没办法。\n他说他的盔甲被偷了，没办法出来。\n我把备用的盔甲丢下去了，希望能帮到他。\n\n这个世界虽然残酷，但还是有好人的，对吧？", "blue", "letter", None),
    ("水晶球", "🔮", "摇晃它，里面会飘起金色的雪花。", "blue", "toy", None),
    ("太阳直剑", "⚔️", "【太阳套装】被阳光祝福过的直剑，挥舞时有暖意。", "blue", "equip", "solar"),
    
    # --- 💜 紫色 ---
    ("深渊臂甲", "🦾", "【深渊套装】仿佛有生命的黑色铠甲，会不自觉地颤抖。", "purple", "equip", "abyss"),
    ("深渊大剑", "🗡️", "【深渊套装】沉重无比的巨剑，曾属于一位漫步深渊的英雄。", "purple", "equip", "abyss"),
    ("无名王者的信", "💌", "【致老友】\n\n风暴已至，我的老友。\n若你还能以此身侍奉古龙，若你还记得我们在云端并肩作战的日子...\n\n那就来古龙顶端找我吧，钟声为证。\n我们要最后一次，挑战诸神。", "purple", "letter", None),
    ("被污染的玩偶", "🧸", "一个破旧的玩偶，散发着令人不安的寒气。", "purple", "toy", None),
    
    # --- 💛 金色 ---
    ("太阳长子头冠", "👑", "【太阳套装】传说中被放逐的战神的头冠，拥有雷电的力量。", "gold", "equip", "solar"),
    ("深渊凝视之眼", "👁️", "【深渊套装】当你凝视它时，它也在凝视你。", "gold", "equip", "abyss"),
    ("防火女的遗书", "🔥", "【给灰烬大人】\n\n灰烬大人，请您夺火吧...这个世界已经太冷了。\n即使是微弱的火苗，也能照亮下一个时代。\n\n哪怕那是...黑暗的时代。\n我会一直在祭祀场等您，直到世界的尽头。", "gold", "letter", None),
    ("初始之火的余烬", "🔥", "仅存的一朵初火，温暖得让人想哭。", "gold", "toy", None),
]

# --- 👔 套装定义 ---
EQUIPMENT_SETS = {
    "solar": {
        "name": "太阳战士",
        "items": ["太阳徽章盾", "太阳直剑", "太阳长子头冠"], 
        "skin_folder": "images/skins/solar" 
    },
    "abyss": {
        "name": "深渊行者",
        "items": ["深渊臂甲", "深渊大剑", "深渊凝视之眼"],
        "skin_folder": "images/skins/abyss" 
    }
}

RARITY_COLORS = {
    "white": "#cccccc", "green": "#1eff00", "blue": "#0070dd", 
    "purple": "#a335ee", "gold": "#ff8000"
}
RARITY_WEIGHTS = {"gold": 5, "purple": 4, "blue": 3, "green": 2, "white": 1}

DATA_FILE = "save_data.json"

class KnightPet(tk.Tk):
    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
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
        self.chest_ids = [] 
        self.is_menu_open = False 
        self.selected_slot_index = -1
        self.current_skin = self.data.get("current_skin", "default")
        self.prev_keys_state = set()
        
        # 挂机计时器
        self.last_drop_time = time.time()

        self.base_width = 200
        
        # --- 加载资源 ---
        self._reload_skin_resources()

        # --- 画布 ---
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
        
        # UI & HUD
        self.bubble_rect = self.canvas.create_rectangle(0,0,0,0, fill="#222", outline="#555", width=2, state='hidden')
        self.bubble_text = self.canvas.create_text(0,0, text="", fill="#ddd", font=("Microsoft YaHei", 9), state='hidden')
        self.hud_text = self.canvas.create_text(0,0, text="", fill="#ffd700", font=("Microsoft YaHei", 10, "bold"))
        self.xp_bar_bg = self.canvas.create_rectangle(0,0,0,0, fill="#333", outline="#555")
        self.xp_bar_fill = self.canvas.create_rectangle(0,0,0,0, fill="#ffd700", outline="")
        self._update_hud()

        # 悬浮菜单
        btn_x = self.center_x + 80 
        btn_y = self.base_y + self.h_size//2 + 20
        self.btn_menu_bg = self.canvas.create_oval(btn_x, btn_y, btn_x+24, btn_y+24, fill="#333", outline="white", state='hidden', tags="ui_btn")
        self.btn_menu_icon = self.canvas.create_text(btn_x+12, btn_y+12, text="⚙️", fill="white", font=("Segoe UI", 10), state='hidden', tags="ui_btn")
        
        self.sub_btns = []
        
        # 档案馆
        arc_x = btn_x + 35
        self.btn_arc_bg = self.canvas.create_oval(arc_x, btn_y, arc_x+24, btn_y+24, fill="#444", outline="#cd853f", state='hidden', tags="sub_btn")
        self.btn_arc_icon = self.canvas.create_text(arc_x+12, btn_y+12, text="📖", fill="white", state='hidden', tags="sub_btn")
        self.sub_btns.extend([self.btn_arc_bg, self.btn_arc_icon])

        # 背包
        bp_x = arc_x + 35
        self.btn_bp_bg = self.canvas.create_oval(bp_x, btn_y, bp_x+24, btn_y+24, fill="#444", outline="#ffd700", state='hidden', tags="sub_btn")
        self.btn_bp_icon = self.canvas.create_text(bp_x+12, btn_y+12, text="🎒", fill="white", state='hidden', tags="sub_btn")
        self.sub_btns.extend([self.btn_bp_bg, self.btn_bp_icon])

        # 退出
        quit_x = bp_x + 35
        self.btn_quit_bg = self.canvas.create_oval(quit_x, btn_y, quit_x+24, btn_y+24, fill="#500", outline="red", state='hidden', tags="sub_btn")
        self.btn_quit_icon = self.canvas.create_text(quit_x+12, btn_y+12, text="❌", fill="white", state='hidden', tags="sub_btn")
        self.sub_btns.extend([self.btn_quit_bg, self.btn_quit_icon])

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - self.canvas_width - 20
        y = sh - self.canvas_height - 50
        self.geometry(f"{self.canvas_width}x{self.canvas_height}+{x}+{y}")

        self.after(100, self._animate_idle_loop) 
        self.after(1000, self._check_afk)
        self.after(5000, self._random_talk_loop)
        
        self.after(1000, self._time_drop_loop)

        self._setup_inputs_and_drag()

    # --- 皮肤资源加载 ---
    def _reload_skin_resources(self):
        skin_rel_path = ""
        if self.current_skin != "default":
            for sid, data in EQUIPMENT_SETS.items():
                if sid == self.current_skin:
                    skin_rel_path = data["skin_folder"]
                    break
        
        if skin_rel_path:
            skin_root = os.path.join(self.base_dir, skin_rel_path)
        else:
            skin_root = self.base_dir
            
        idle_dir = os.path.join(skin_root, "idle")
        if not os.path.exists(idle_dir):
            idle_dir = os.path.join(self.base_dir, "images", "idle")
            
        self.idle_frames = self._load_frames(idle_dir)
        if not self.idle_frames:
            img = os.path.join(self.base_dir, "images", "knight.png")
            self._load_fallback_idle(img)

        att_dir = os.path.join(skin_root, "attack")
        if not os.path.exists(att_dir):
            att_dir = os.path.join(self.base_dir, "images", "attack")
        self.attack_frames = self._load_frames(att_dir)

        bf_dir = os.path.join(self.base_dir, "images", "bonfire")
        self.bonfire_frames = self._load_frames(bf_dir)

    def _load_fallback_idle(self, path):
        try:
            pil_image = Image.open(path)
            w_percent = (self.base_width / float(pil_image.size[0]))
            self.h_size = int((float(pil_image.size[1]) * float(w_percent)))
            pil_resized = pil_image.resize((self.base_width, self.h_size), Image.LANCZOS)
            self.knight_photo_idle_fallback = ImageTk.PhotoImage(pil_resized)
        except: pass

    def _load_frames(self, folder_path):
        frames = []
        if not os.path.exists(folder_path): return frames
        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        for i, file in enumerate(files):
            path = os.path.join(folder_path, file)
            try:
                pil_img = Image.open(path)
                w_percent = (self.base_width / float(pil_img.size[0]))
                if i==0 and not hasattr(self, 'h_size'):
                    self.h_size = int((float(pil_img.size[1]) * float(w_percent)))
                h_target = int((float(pil_img.size[1]) * float(w_percent)))
                pil_resized = pil_img.resize((self.base_width, h_target), Image.LANCZOS)
                frames.append(ImageTk.PhotoImage(pil_resized))
            except: pass
        return frames

    # --- API Polling ---
    def _get_current_pressed_keys(self):
        pressed = set()
        for k in range(0x30, 0x5A + 1):
            if ctypes.windll.user32.GetAsyncKeyState(k) & 0x8000:
                pressed.add(k)
        special_keys = [0x08, 0x09, 0x0D, 0x10, 0x11, 0x12, 0x1B, 0x20, 0x25, 0x26, 0x27, 0x28]
        for k in special_keys:
            if ctypes.windll.user32.GetAsyncKeyState(k) & 0x8000:
                pressed.add(k)
        return pressed

    def _input_loop(self):
        try:
            current_keys = self._get_current_pressed_keys()
            new_keys = current_keys - self.prev_keys_state
            
            if new_keys:
                if VK_SPACE in new_keys:
                    self._trigger_action("PRAISE")
                elif (VK_Q in new_keys) or (VK_W in new_keys) or (VK_SHIFT in new_keys):
                    self._trigger_action("BLOCK")
                else:
                    self._trigger_action("ATTACK")
            
            self.prev_keys_state = current_keys
        except Exception:
            pass
        self.after(20, self._input_loop)

    # --- Data ---
    def _load_data(self):
        default = {
            "level": 1, "current_xp": 0, "total_souls": 0, 
            "inventory": [], 
            "archive": [], 
            "unlocked_skins": ["default"], 
            "current_skin": "default",
            "gift_received_5": False,
            "gift_received_10": False
        }
        if os.path.exists(self.data_file_path):
            try:
                with open(self.data_file_path, "r") as f: 
                    d = json.load(f)
                    for k, v in default.items():
                        if k not in d: d[k] = v
                    return d
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
        self._drag_data = {"offset_x": 0, "offset_y": 0, "is_moving": False}
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<Motion>", self._on_mouse_hover)
        
        self.canvas.tag_bind(self.btn_menu_bg, "<Button-1>", self._toggle_menu)
        self.canvas.tag_bind(self.btn_menu_icon, "<Button-1>", self._toggle_menu)
        self.canvas.tag_bind(self.btn_bp_bg, "<Button-1>", self._open_backpack)
        self.canvas.tag_bind(self.btn_bp_icon, "<Button-1>", self._open_backpack)
        self.canvas.tag_bind(self.btn_arc_bg, "<Button-1>", self._open_archive_ui)
        self.canvas.tag_bind(self.btn_arc_icon, "<Button-1>", self._open_archive_ui)
        self.canvas.tag_bind(self.btn_quit_bg, "<Button-1>", self.exit_game)
        self.canvas.tag_bind(self.btn_quit_icon, "<Button-1>", self.exit_game)

        self.after(20, self._input_loop)

    def _on_mouse_hover(self, event):
        xp_bbox = self.canvas.bbox(self.xp_bar_bg) 
        if not xp_bbox: return
        x1, y1, x2, y2 = xp_bbox
        pad = 20
        is_hover = (x1 - pad <= event.x <= x2 + 80) and (y1 - pad <= event.y <= y2 + 40)
        
        if is_hover:
            self.canvas.itemconfigure(self.btn_menu_bg, state='normal')
            self.canvas.itemconfigure(self.btn_menu_icon, state='normal')
        else:
            if not self.is_menu_open:
                self.canvas.itemconfigure(self.btn_menu_bg, state='hidden')
                self.canvas.itemconfigure(self.btn_menu_icon, state='hidden')

    def _toggle_menu(self, event):
        self._drag_data["is_moving"] = True 
        self.is_menu_open = not self.is_menu_open
        state = 'normal' if self.is_menu_open else 'hidden'
        for item in self.sub_btns:
            self.canvas.itemconfigure(item, state=state)

    def _time_drop_loop(self):
        if time.time() - self.last_drop_time > 1800: # 30分钟
            self._spawn_afk_chest()
            self.last_drop_time = time.time()
        self.after(1000, self._time_drop_loop)

    def _spawn_afk_chest(self):
        level = self.data["level"]
        rarity = "white"
        roll = random.random()
        if level >= 50 and roll < 0.2: rarity = "gold"
        elif level >= 30 and roll < 0.3: rarity = "purple"
        elif level >= 10 and roll < 0.4: rarity = "blue"
        elif roll < 0.5: rarity = "green"
        
        chest_candidates = [i for i in ITEMS_DB if i[4] == "chest" and i[3] == rarity]
        if not chest_candidates: 
            chest_candidates = [i for i in ITEMS_DB if i[4] == "chest" and i[3] == "white"]
            
        chest_item = random.choice(chest_candidates)
        
        if self._add_item_to_inventory(chest_item, bypass_limit=False):
            self._show_bubble("挂机收获!", 3000, "#ffd700")
        else:
            self._show_bubble("背包满了!", 3000, "red")

    def _add_item_to_inventory(self, item_data, bypass_limit=False):
        name, icon, desc, r, i_type, set_id = item_data
        
        if "inventory" not in self.data: self.data["inventory"] = []
        
        if len(self.data["inventory"]) < 20 or bypass_limit:
            new_item = {
                "name": name, "icon": icon, "desc": desc, 
                "rarity": r, "type": i_type, "set_id": set_id
            }
            self.data["inventory"].append(new_item)
            self._save_data()
            
            if hasattr(self, 'backpack_window') and self.backpack_window.winfo_exists():
                self._refresh_backpack_ui()
                
            return True
        else:
            return False

    def _give_level_gifts(self):
        if self.data["level"] >= 5 and not self.data.get("gift_received_5", False):
            self.data["gift_received_5"] = True
            items = [("绿花草", "green"), ("修理光粉", "green")]
            for target_name, _ in items:
                for item in ITEMS_DB:
                    if item[0] == target_name:
                        self._add_item_to_inventory(item, bypass_limit=True)
            self._show_bubble("🎉 5级礼包!", 3000, "#ffd700")
            messagebox.showinfo("5级奖励", "恭喜达到5级！获得了一些补给品。")

        if self.data["level"] >= 10 and not self.data.get("gift_received_10", False):
            self.data["gift_received_10"] = True
            solar_items = ["太阳徽章盾", "太阳直剑", "太阳长子头冠"]
            for target_name in solar_items:
                for item in ITEMS_DB:
                    if item[0] == target_name:
                        self._add_item_to_inventory(item, bypass_limit=True)
                        break
            self._show_bubble("🎉 10级大礼包!", 3000, "#ffd700")
            messagebox.showinfo("10级奖励", "恭喜达到10级！\n获得【太阳战士套装】！\n请在背包中查看并去【更换皮肤】处合成。")

    # ==========================================
    # ▼▼▼ 档案馆 UI (核心更新) ▼▼▼
    # ==========================================
    def _open_archive_ui(self, event=None):
        self._drag_data["is_moving"] = True
        self.is_menu_open = False
        for item in self.sub_btns: self.canvas.itemconfigure(item, state='hidden')

        if hasattr(self, 'archive_window') and self.archive_window.winfo_exists():
            self.archive_window.lift()
            return

        aw = tk.Toplevel(self)
        aw.title("Archive")
        aw.geometry("450x550") 
        aw.resizable(False, False)
        aw.configure(bg="#2c2520") # 书架色
        aw.attributes("-topmost", True)
        self.archive_window = aw

        main_x = self.winfo_x()
        main_y = self.winfo_y()
        aw.geometry(f"+{main_x + 250}+{main_y}")

        # Title
        tk.Label(aw, text="档案馆", font=("Times New Roman", 16, "bold"), fg="#deb887", bg="#2c2520").pack(pady=10)
        
        paned = tk.PanedWindow(aw, orient="horizontal", bg="#2c2520", sashwidth=4, sashrelief="ridge")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left List
        left_frame = tk.Frame(paned, bg="#3e3630")
        self.arc_list = tk.Listbox(left_frame, bg="#3e3630", fg="#dcdcdc", font=("Microsoft YaHei", 10), 
                                   selectbackground="#8b4513", selectforeground="white", borderwidth=0, highlightthickness=0)
        self.arc_list.pack(side="left", fill="both", expand=True)
        paned.add(left_frame, width=150)

        # Right Text (羊皮纸风格)
        right_frame = tk.Frame(paned, bg="#f5deb3")
        self.arc_text = tk.Text(right_frame, bg="#f5deb3", fg="#3e2723", font=("KaiTi", 12), 
                                wrap="word", padx=15, pady=15, borderwidth=0, highlightthickness=0)
        self.arc_text.pack(fill="both", expand=True)
        self.arc_text.insert("1.0", "请选择要阅读的文献...")
        self.arc_text.config(state="disabled")
        paned.add(right_frame)

        self._refresh_archive_list()
        self.arc_list.bind("<<ListboxSelect>>", self._on_archive_select)

    def _refresh_archive_list(self):
        self.arc_list.delete(0, "end")
        archive_data = self.data.get("archive", [])
        if not archive_data:
            self.arc_list.insert("end", "(暂无记录)")
            self.arc_list.config(state="disabled")
            return
        
        self.arc_list.config(state="normal")
        
        # 1. 归类逻辑：提取冒号前的名称
        self.grouped_archive = {} # {"家书": [item1, item2], ...}
        
        for item in archive_data:
            name = item["name"]
            if ":" in name:
                series_name = name.split(":")[0]
                if series_name not in self.grouped_archive:
                    self.grouped_archive[series_name] = []
                self.grouped_archive[series_name].append(item)
            else:
                # 没冒号的单独放
                self.grouped_archive[name] = [item]
        
        # 2. 显示列表
        for title in self.grouped_archive.keys():
            self.arc_list.insert("end", f"📜 {title}")

    def _on_archive_select(self, event):
        selection = self.arc_list.curselection()
        if not selection: return
        
        # 获取选中的标题 (去掉前面的emoji)
        display_text = self.arc_list.get(selection[0])
        title = display_text.replace("📜 ", "")
        
        items = self.grouped_archive.get(title, [])
        if not items: return
        
        # 按名称排序 (保证章节顺序)
        items.sort(key=lambda x: x["name"])
        
        # 拼合内容
        full_content = ""
        for item in items:
            full_content += f"【{item['name']}】\n\n{item['desc']}\n\n"
            full_content += "- " * 15 + "\n\n"
            
        self.arc_text.config(state="normal")
        self.arc_text.delete("1.0", "end")
        self.arc_text.insert("1.0", full_content)
        self.arc_text.config(state="disabled")

    # ==========================================
    # ▼▼▼ 美化版信件阅读弹窗 ▼▼▼
    # ==========================================
    def _show_letter_ui(self, title, content):
        win = tk.Toplevel(self)
        win.title("阅读")
        win.geometry("350x450")
        win.configure(bg="#f5deb3") # 羊皮纸色
        win.attributes("-topmost", True)
        
        # 居中
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        win.geometry(f"+{main_x+50}+{main_y+50}")
        
        # 标题
        tk.Label(win, text=title, font=("KaiTi", 16, "bold"), bg="#f5deb3", fg="#5c4033", pady=15).pack()
        
        # 内容
        text_box = tk.Text(win, font=("KaiTi", 12), bg="#f5deb3", fg="#3e2723", wrap="word", 
                           borderwidth=0, highlightthickness=0, padx=20, pady=10)
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", content)
        text_box.config(state="disabled")
        
        # 底部提示
        tk.Label(win, text="(已收入档案馆)", font=("Microsoft YaHei", 8), bg="#f5deb3", fg="#8b4513").pack(pady=10)
        
        tk.Button(win, text="关闭", bg="#8b4513", fg="white", command=win.destroy, relief="flat", padx=10).pack(pady=(0, 15))

    # --- 核心修改：阅读并归档 ---
    def _read_and_archive_letter(self):
        if self.selected_slot_index == -1: return
        inventory = self.data.get("inventory", [])
        if self.selected_slot_index >= len(inventory): return
        
        item = inventory[self.selected_slot_index]
        
        # 1. 存入档案馆 (去重)
        if "archive" not in self.data: self.data["archive"] = []
        
        exists = False
        for arc_item in self.data["archive"]:
            if arc_item["name"] == item["name"]:
                exists = True
                break
        
        if not exists:
            self.data["archive"].append({
                "name": item["name"],
                "desc": item["desc"]
            })
        
        # 2. 弹窗显示 (美化版)
        self._show_letter_ui(item['name'], item['desc'])
        
        # 3. 从背包移除
        del inventory[self.selected_slot_index]
        self._save_data()
        
        # 4. 刷新UI
        self.selected_slot_index = -1
        self._refresh_backpack_ui()
        self.lbl_desc_name.config(text="已归档", fg="#cd853f")
        self.lbl_desc_text.config(text="")
        self.btn_action.pack_forget()

    # ==========================================
    # ▼▼▼ 原有背包与系统逻辑 ▼▼▼
    # ==========================================
    def _open_backpack(self, event=None):
        self._drag_data["is_moving"] = True
        self.is_menu_open = False
        for item in self.sub_btns: self.canvas.itemconfigure(item, state='hidden')

        if hasattr(self, 'backpack_window') and self.backpack_window.winfo_exists():
            self.backpack_window.lift()
            self._refresh_backpack_ui()
            return

        bp = tk.Toplevel(self)
        bp.title("Inventory")
        bp.geometry("260x380") 
        bp.resizable(False, False)
        bp.configure(bg="#1c1c1c")
        bp.attributes("-topmost", True)
        self.backpack_window = bp

        main_x = self.winfo_x()
        main_y = self.winfo_y()
        bp_x = main_x + self.center_x + 80
        bp_y = main_y + 80
        bp.geometry(f"+{bp_x}+{bp_y}")

        self._init_backpack_ui(bp)
        self._refresh_backpack_ui()

    def _init_backpack_ui(self, win):
        header_frame = tk.Frame(win, bg="#1c1c1c")
        header_frame.pack(fill="x", pady=(10, 5), padx=10)
        tk.Label(header_frame, text="INVENTORY", font=("Times New Roman", 12, "bold"), fg="#c0a062", bg="#1c1c1c").pack(side="left")
        
        sort_btn = tk.Label(header_frame, text="🔃", font=("Segoe UI Emoji", 12), fg="white", bg="#333", cursor="hand2")
        sort_btn.pack(side="right", padx=5)
        sort_btn.bind("<Button-1>", lambda e: self._sort_inventory())
        
        skin_btn = tk.Label(header_frame, text="👕", font=("Segoe UI Emoji", 12), fg="white", bg="#333", cursor="hand2")
        skin_btn.pack(side="right", padx=5)
        skin_btn.bind("<Button-1>", lambda e: self._open_skin_menu())

        self.bp_grid_frame = tk.Frame(win, bg="#1c1c1c")
        self.bp_grid_frame.pack(padx=10, pady=5)

        self.bp_desc_frame = tk.Frame(win, bg="#252525", height=100, borderwidth=1, relief="sunken")
        self.bp_desc_frame.pack(fill="x", padx=15, pady=10)
        self.bp_desc_frame.pack_propagate(False)

        self.lbl_desc_name = tk.Label(self.bp_desc_frame, text="请选择物品", font=("Microsoft YaHei", 10, "bold"), fg="gray", bg="#252525", anchor="w")
        self.lbl_desc_name.pack(fill="x", padx=5, pady=(5,0))
        
        self.lbl_desc_text = tk.Label(self.bp_desc_frame, text="", font=("Microsoft YaHei", 8), fg="#aaa", bg="#252525", anchor="nw", justify="left", wraplength=220)
        self.lbl_desc_text.pack(fill="both", expand=True, padx=5, pady=2)
        
        # 按钮容器
        btn_frame = tk.Frame(self.bp_desc_frame, bg="#252525")
        btn_frame.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor="se")

        # 动态按钮
        self.btn_action = tk.Button(btn_frame, text="操作", bg="#444", fg="white", font=("Microsoft YaHei", 8))
        self.btn_action.pack(side="right", padx=2)
        self.btn_action.pack_forget()

        self.lbl_soul_count = tk.Label(win, text="", font=("Consolas", 10), fg="#888", bg="#1c1c1c")
        self.lbl_soul_count.pack(side="bottom", pady=5)

    def _refresh_backpack_ui(self):
        if not hasattr(self, 'backpack_window') or not self.backpack_window.winfo_exists(): return
        for widget in self.bp_grid_frame.winfo_children(): widget.destroy()

        my_inventory = self.data.get("inventory", [])
        for i in range(20):
            row = i // 5
            col = i % 5
            slot_bg = "#2d2d2d"
            item_text = ""
            rarity_color = "white"
            item_data = None
            bd_col = "#555"
            bd_w = 1

            if i < len(my_inventory):
                item_data = my_inventory[i]
                item_text = item_data["icon"]
                slot_bg = "#3d3d3d"
                rarity_color = RARITY_COLORS.get(item_data["rarity"], "white")
                if i == self.selected_slot_index:
                    bd_col = "#ffd700"
                    bd_w = 2

            slot = tk.Frame(self.bp_grid_frame, width=40, height=40, bg=slot_bg, 
                            highlightbackground=bd_col, highlightthickness=bd_w)
            slot.pack_propagate(False) 
            slot.grid(row=row, column=col, padx=2, pady=2)
            slot.bind("<Button-1>", lambda e, idx=i, it=item_data: self._on_slot_click(idx, it))

            if item_text:
                lbl = tk.Label(slot, text=item_text, font=("Segoe UI Emoji", 16), bg=slot_bg, fg=rarity_color)
                lbl.pack(expand=True)
                lbl.bind("<Button-1>", lambda e, idx=i, it=item_data: self._on_slot_click(idx, it))

        self.lbl_soul_count.config(text=f"SOULS: {self.data['total_souls']}")

    def _on_slot_click(self, index, item_data):
        self.selected_slot_index = index
        self._refresh_backpack_ui()
        self.btn_action.pack_forget() 
        
        if item_data:
            desc = item_data.get("desc", "")
            if not desc:
                for item_def in ITEMS_DB:
                    if item_def[0] == item_data["name"]:
                        desc = item_def[2]
                        item_data["desc"] = desc
                        item_data["type"] = item_def[4]
                        item_data["set_id"] = item_def[5]
                        break
            
            rarity = item_data.get("rarity", "white")
            i_type = item_data.get("type", "toy")
            color = RARITY_COLORS.get(rarity, "white")
            
            self.lbl_desc_name.config(text=f"{item_data['icon']} {item_data['name']}", fg=color)
            self.lbl_desc_text.config(text=desc)
            
            # 按钮逻辑
            if i_type == "chest":
                cost = CHEST_COSTS.get(rarity, 100)
                self.btn_action.config(text=f"开启 (-{cost})", bg="#228b22", fg="white", 
                                       command=self._open_selected_chest)
                self.btn_action.pack(side="right", padx=2)
            elif i_type == "letter":
                # 阅读归档
                self.btn_action.config(text="阅读 (归档)", bg="#cd853f", fg="white", 
                                       command=self._read_and_archive_letter)
                self.btn_action.pack(side="right", padx=2)
            else:
                price = SELL_PRICES.get(rarity, 10)
                self.btn_action.config(text=f"出售 (+{price})", bg="#600", fg="#ffd700", 
                                       command=self._sell_selected_item)
                self.btn_action.pack(side="right", padx=2)
        else:
            self.lbl_desc_name.config(text="空", fg="gray")
            self.lbl_desc_text.config(text="")

    def _sell_selected_item(self):
        if self.selected_slot_index == -1: return
        inventory = self.data.get("inventory", [])
        if self.selected_slot_index >= len(inventory): return
        
        item = inventory[self.selected_slot_index]
        rarity = item.get("rarity", "white")
        price = SELL_PRICES.get(rarity, 10)
        
        self.data["total_souls"] += price
        del inventory[self.selected_slot_index]
        self._save_data()
        
        self.selected_slot_index = -1
        self._show_bubble(f"获得灵魂 +{price}", 1000, "#ffd700")
        self._refresh_backpack_ui()
        self.lbl_desc_name.config(text="已出售", fg="#c0a062")
        self.lbl_desc_text.config(text="")
        self.btn_action.pack_forget()

    def _open_selected_chest(self):
        if self.selected_slot_index == -1: return
        inventory = self.data.get("inventory", [])
        item = inventory[self.selected_slot_index]
        rarity = item.get("rarity", "white")
        cost = CHEST_COSTS.get(rarity, 100)
        
        if self.data["total_souls"] < cost:
            messagebox.showwarning("灵魂不足", f"开启这个宝箱需要 {cost} 灵魂！\n快去挂机打怪赚取灵魂吧。")
            return
            
        self.data["total_souls"] -= cost
        del inventory[self.selected_slot_index]
        self._save_data()
        self.selected_slot_index = -1
        self.btn_action.pack_forget()
        self.lbl_desc_name.config(text="开启中...", fg="#c0a062")
        self.lbl_desc_text.config(text="")
        self._refresh_backpack_ui()
        
        count = random.randint(2, 3)
        rewards = []
        pool_rarity = [rarity] 
        if rarity == 'white': pool_rarity.append('green')
        elif rarity == 'green': pool_rarity.extend(['white', 'blue'])
        elif rarity == 'blue': pool_rarity.extend(['green', 'purple'])
        elif rarity == 'purple': pool_rarity.extend(['blue', 'gold'])
        elif rarity == 'gold': pool_rarity.extend(['purple'])
        
        for _ in range(count):
            r_target = random.choice(pool_rarity)
            candidates = [i for i in ITEMS_DB if i[4] != 'chest' and i[3] == r_target]
            if not candidates: candidates = [i for i in ITEMS_DB if i[4] != 'chest' and i[3] == 'white']
            item_data = random.choice(candidates)
            self._add_item_to_inventory(item_data, bypass_limit=True) 
            rewards.append(item_data[0])
            
        msg = "你获得了：\n" + "\n".join([f"- {n}" for n in rewards])
        messagebox.showinfo("宝箱开启", msg)
        self._refresh_backpack_ui()

    def _sort_inventory(self):
        if "inventory" in self.data:
            self.data["inventory"].sort(key=lambda x: (RARITY_WEIGHTS.get(x["rarity"], 0), x["name"]), reverse=True)
            self._save_data()
            self.selected_slot_index = -1
            self._refresh_backpack_ui()
            self.lbl_desc_name.config(text="整理完毕", fg="#c0a062")
            self.lbl_desc_text.config(text="")

    def _open_skin_menu(self):
        skin_win = tk.Toplevel(self.backpack_window)
        skin_win.title("更换皮肤")
        skin_win.geometry("260x350")
        skin_win.configure(bg="#1c1c1c")
        skin_win.attributes("-topmost", True)
        
        tk.Label(skin_win, text="WARDROBE", font=("Times New Roman", 12, "bold"), fg="#c0a062", bg="#1c1c1c").pack(pady=10)
        
        unlocked = self.data.get("unlocked_skins", ["default"])
        
        self._create_skin_btn(skin_win, "default", "默认骑士", True, False)

        for set_id, set_data in EQUIPMENT_SETS.items():
            is_unlocked = set_id in unlocked
            self._create_skin_btn(skin_win, set_id, set_data["name"], is_unlocked, True)

    def _create_skin_btn(self, win, skin_id, name, is_unlocked, is_craftable):
        frame = tk.Frame(win, bg="#1c1c1c")
        frame.pack(pady=3, fill="x", padx=20)
        
        if skin_id == self.current_skin:
            lbl_color = "#ffd700"
            state = "disabled"
        elif is_unlocked:
            lbl_color = "white"
            state = "normal"
        else:
            lbl_color = "gray"
            state = "normal"

        tk.Label(frame, text=name, fg=lbl_color, bg="#1c1c1c", width=12, anchor="w").pack(side="left")
        
        if skin_id == self.current_skin:
            tk.Label(frame, text="●", fg="#ffd700", bg="#1c1c1c").pack(side="right")
        elif is_unlocked:
            tk.Button(frame, text="装备", bg="#333", fg="white", width=6, font=("Microsoft YaHei", 8),
                      command=lambda: self._change_skin(skin_id, win)).pack(side="right")
        elif is_craftable:
            can_craft = self._check_can_craft(skin_id)
            btn_bg = "#006400" if can_craft else "#333"
            btn_fg = "white" if can_craft else "gray"
            btn_txt = "合成" if can_craft else "未集齐"
            
            tk.Button(frame, text=btn_txt, bg=btn_bg, fg=btn_fg, width=6, font=("Microsoft YaHei", 8),
                      state="normal" if can_craft else "disabled",
                      command=lambda: self._craft_skin(skin_id, win)).pack(side="right")

    def _check_can_craft(self, set_id):
        if set_id not in EQUIPMENT_SETS: return False
        needed = set(EQUIPMENT_SETS[set_id]["items"])
        owned = set(i["name"] for i in self.data["inventory"])
        return needed.issubset(owned)

    def _craft_skin(self, set_id, win):
        if not self._check_can_craft(set_id): return
        
        needed = EQUIPMENT_SETS[set_id]["items"]
        for need_name in needed:
            for i, item in enumerate(self.data["inventory"]):
                if item["name"] == need_name:
                    del self.data["inventory"][i]
                    break
        
        self.data["unlocked_skins"].append(set_id)
        self._save_data()
        
        win.destroy()
        self._open_skin_menu()
        self._refresh_backpack_ui()
        messagebox.showinfo("合成成功", f"【{EQUIPMENT_SETS[set_id]['name']}】制作完成！\n装备已消耗，新外观已解锁。")

    def _change_skin(self, skin_id, win):
        self.current_skin = skin_id
        self.data["current_skin"] = skin_id
        self._save_data()
        self._reload_skin_resources()
        self._reset_pose()
        win.destroy()
        self._show_bubble("换装成功！", 1500)

    # ==========================================

    def _on_drag_start(self, event):
        self._drag_data["offset_x"] = event.x
        self._drag_data["offset_y"] = event.y
        self._drag_data["is_moving"] = False 

    def _on_drag_motion(self, event):
        new_x = event.x_root - self._drag_data["offset_x"]
        new_y = event.y_root - self._drag_data["offset_y"]
        if abs(event.x - self._drag_data["offset_x"]) > 2 or abs(event.y - self._drag_data["offset_y"]) > 2:
            self._drag_data["is_moving"] = True
            self.geometry(f"+{new_x}+{new_y}")

    def _on_drag_stop(self, event):
        if not self._drag_data["is_moving"]:
            if event.num == 1: 
                self._trigger_action("ATTACK")
        self._drag_data["is_moving"] = False

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
            
            if self.data["level"] == 5:
                self._give_level_gifts()
            elif self.data["level"] == 10:
                self._give_level_gifts()

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

    def exit_game(self, event=None):
        self._save_data()
        self.destroy()
        sys.exit()

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