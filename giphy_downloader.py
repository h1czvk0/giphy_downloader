import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
import os
import json
import threading
from urllib.parse import urlparse
import time
from PIL import Image, ImageTk
import sys
import platform

# 设置CustomTkinter外观模式和主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LargerFontGiphyDownloader:
    def __init__(self):
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("Giphy下载器")

        # 设置高DPI感知，提高字体清晰度
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # 设置DPI感知
        except:
            pass

        # 设置紧凑型窗口尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 根据屏幕分辨率调整字体和窗口大小 - 增大字体
        if screen_width >= 1920:
            window_width, window_height = 880, 620  # 稍微增大窗口
            self.font_size = 13  # 从11增大到13
        elif screen_width >= 1366:
            window_width, window_height = 800, 600  # 稍微增大窗口
            self.font_size = 12  # 从10增大到12
        else:
            window_width, window_height = 740, 570  # 稍微增大窗口
            self.font_size = 11  # 从9增大到11

        # 居中显示窗口
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(720, 520)  # 增大最小尺寸
        self.root.resizable(True, True)

        # 检测系统并选择最佳字体
        self.setup_fonts()

        # API保存文件路径
        self.config_file = os.path.join(os.path.expanduser("~"), ".giphy_downloader_config.json")

        # 初始化变量
        self.api_key = tk.StringVar()
        self.author_name = tk.StringVar()
        self.download_path = tk.StringVar(value=os.path.join(os.getcwd(), "downloads"))
        self.quality_option = tk.StringVar(value="Original")
        self.download_gifs = tk.BooleanVar(value=True)
        self.download_stickers = tk.BooleanVar(value=True)
        self.is_downloading = False

        # 画质选项映射
        self.quality_mapping = {
            "Original": "original",
            "High": "fixed_height", 
            "Medium": "downsized",
            "Small": "fixed_width_small"
        }

        # 加载保存的配置
        self.load_config()

        self.setup_larger_font_ui()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_fonts(self):
        """设置最适合的系统字体"""
        system = platform.system()

        if system == "Windows":
            # Windows系统推荐字体
            self.ui_font_family = "Microsoft YaHei UI"  # 微软雅黑UI，专为界面优化
            self.code_font_family = "Consolas"  # 等宽字体
            # 备用字体
            self.fallback_fonts = ["Segoe UI", "Arial", "SimHei"]
        else:
            # 其他系统备用字体
            self.ui_font_family = "Arial"
            self.code_font_family = "Courier New"
            self.fallback_fonts = ["Arial", "DejaVu Sans"]

        # 测试字体可用性
        try:
            test_font = ctk.CTkFont(family=self.ui_font_family, size=10)
            # 如果能创建则字体可用
        except:
            # 字体不可用，使用备用字体
            for fallback in self.fallback_fonts:
                try:
                    test_font = ctk.CTkFont(family=fallback, size=10)
                    self.ui_font_family = fallback
                    break
                except:
                    continue

    def create_font(self, size, family=None, weight="normal"):
        """创建优化的字体对象"""
        if family is None:
            family = self.ui_font_family

        return ctk.CTkFont(
            family=family,
            size=size,
            weight=weight,
            underline=False,
            overstrike=False
        )

    def load_config(self):
        """加载保存的配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
                    self.download_path.set(config.get('download_path', os.path.join(os.getcwd(), "downloads")))
                    # 兼容旧配置文件中的中文选项
                    old_quality = config.get('quality', 'Original')
                    if old_quality == '高清':
                        self.quality_option.set('Original')
                    elif old_quality == '标准':
                        self.quality_option.set('High')
                    elif old_quality == '压缩':
                        self.quality_option.set('Medium')
                    elif old_quality == '小图':
                        self.quality_option.set('Small')
                    else:
                        self.quality_option.set(old_quality)
        except Exception as e:
            print(f"配置文件加载失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'api_key': self.api_key.get(),
                'download_path': self.download_path.get(),
                'quality': self.quality_option.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"配置文件保存失败: {e}")

    def on_closing(self):
        """窗口关闭时保存配置"""
        self.save_config()
        self.root.destroy()

    def setup_larger_font_ui(self):
        """设置大字体UI界面"""
        # 主容器
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 标题区域
        self.create_larger_font_header(main_frame)

        # 主要内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(10, 0))

        # 左侧配置区域
        self.create_config_section(content_frame)

        # 右侧选项和控制区域
        self.create_options_control_section(content_frame)

        # 底部进度和结果区域
        self.create_bottom_section(main_frame)

    def create_larger_font_header(self, parent):
        """创建大字体标题区域"""
        header_frame = ctk.CTkFrame(parent, height=65, corner_radius=10)  # 增大高度
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Giphy下载器",
            font=self.create_font(self.font_size + 6)  # 从+5增大到+6
        )
        title_label.pack(expand=True)

    def create_config_section(self, parent):
        """创建左侧配置区域"""
        left_frame = ctk.CTkFrame(parent, corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # 配置标题 - 增大字体
        config_label = ctk.CTkLabel(
            left_frame,
            text="🔑 配置设置",
            font=self.create_font(self.font_size + 2)  # 从+1增大到+2
        )
        config_label.pack(pady=(15, 10))

        # API密钥
        api_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        api_frame.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            api_frame, 
            text="API密钥:",
            anchor="w", 
            font=self.create_font(self.font_size + 1)  # 从基础字体增大到+1
        ).pack(fill="x")

        api_input_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_input_frame.pack(fill="x", pady=(3, 0))

        self.api_entry = ctk.CTkEntry(
            api_input_frame,
            textvariable=self.api_key,
            placeholder_text="请输入GIPHY API密钥",
            height=34,  # 从30增大到34
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            show="*"
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # API保存状态指示
        self.api_status = ctk.CTkLabel(
            api_input_frame,
            text="💾" if self.api_key.get() else "❌",
            width=30,  # 从25增大到30
            font=self.create_font(self.font_size + 2)  # 从+1增大到+2
        )
        self.api_status.pack(side="right")

        # 绑定API输入变化事件
        self.api_key.trace_add("write", self.on_api_change)

        # 作者用户名
        author_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        author_frame.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            author_frame, 
            text="用户名:",
            anchor="w", 
            font=self.create_font(self.font_size + 1)  # 增大字体
        ).pack(fill="x")

        self.author_entry = ctk.CTkEntry(
            author_frame,
            textvariable=self.author_name,
            placeholder_text="输入作者用户名",
            height=34,  # 增大高度
            font=self.create_font(self.font_size)  # 增大字体
        )
        self.author_entry.pack(fill="x", pady=(3, 0))

        # 下载路径
        path_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            path_frame, 
            text="保存路径:",
            anchor="w", 
            font=self.create_font(self.font_size + 1)  # 增大字体
        ).pack(fill="x")

        path_input_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_input_frame.pack(fill="x", pady=(3, 0))

        self.path_entry = ctk.CTkEntry(
            path_input_frame,
            textvariable=self.download_path,
            height=34,  # 增大高度
            font=self.create_font(self.font_size - 1)  # 从-2增大到-1
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="📁",
            width=34,  # 从30增大到34
            height=34,
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            command=self.browse_folder
        )
        browse_btn.pack(side="right")

    def create_options_control_section(self, parent):
        """创建右侧选项和控制区域"""
        right_frame = ctk.CTkFrame(parent, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # 选项标题 - 增大字体
        options_label = ctk.CTkLabel(
            right_frame,
            text="⚙️ 下载选项",
            font=self.create_font(self.font_size + 2)  # 从+1增大到+2
        )
        options_label.pack(pady=(15, 10))

        # 内容类型选择
        type_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            type_frame, 
            text="内容类型:",
            anchor="w", 
            font=self.create_font(self.font_size + 1)  # 增大字体
        ).pack(fill="x")

        checkbox_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(3, 0))

        self.gif_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="GIF动图",
            variable=self.download_gifs,
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            width=85  # 稍微增大宽度
        )
        self.gif_checkbox.pack(side="left")

        self.sticker_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="贴纸",
            variable=self.download_stickers,
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            width=70  # 稍微增大宽度
        )
        self.sticker_checkbox.pack(side="left", padx=(10, 0))

        # 画质选择
        quality_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            quality_frame, 
            text="画质:",
            anchor="w", 
            font=self.create_font(self.font_size + 1)  # 增大字体
        ).pack(fill="x")

        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.quality_option,
            values=list(self.quality_mapping.keys()),
            height=34,  # 从30增大到34
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            command=self.on_quality_change
        )
        self.quality_menu.pack(fill="x", pady=(3, 0))

        # 控制按钮区域
        control_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        control_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.start_btn = ctk.CTkButton(
            control_frame,
            text="🚀 开始下载",
            height=42,  # 从38增大到42
            font=self.create_font(self.font_size + 1),  # 从基础字体增大到+1
            command=self.start_download
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ 停止",
            height=36,  # 从32增大到36
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            command=self.stop_download,
            state="disabled",
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_btn.pack(fill="x")

    def create_bottom_section(self, parent):
        """创建底部进度和结果区域"""
        bottom_frame = ctk.CTkFrame(parent, corner_radius=10)
        bottom_frame.pack(fill="both", expand=True, pady=(10, 0))

        # 进度区域
        progress_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(15, 10))

        # 状态和进度在同一行
        status_progress_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        status_progress_frame.pack(fill="x")

        self.progress_var = tk.StringVar(value="准备就绪")
        self.status_label = ctk.CTkLabel(
            status_progress_frame,
            textvariable=self.progress_var,
            font=self.create_font(self.font_size),  # 从-1增大到基础字体
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.progress_bar = ctk.CTkProgressBar(
            status_progress_frame,
            width=150,
            height=8  # 保持进度条高度
        )
        self.progress_bar.pack(side="right", padx=(10, 0))
        self.progress_bar.set(0)

        # 结果显示区域
        self.result_text = ctk.CTkTextbox(
            bottom_frame,
            height=120,  # 保持高度
            corner_radius=8,
            font=self.create_font(self.font_size - 1, self.code_font_family),  # 从-2增大到-1
            wrap="word"
        )
        self.result_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def on_api_change(self, *args):
        """API输入变化时更新状态指示器"""
        if self.api_key.get().strip():
            self.api_status.configure(text="💾")
            # 实时保存API密钥
            self.save_config()
        else:
            self.api_status.configure(text="❌")

    def on_quality_change(self, value):
        """画质选择变化时保存配置"""
        self.save_config()

    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            self.save_config()

    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime('%H:%M:%S')
        self.result_text.insert("end", f"[{timestamp}] {message}\n")
        self.result_text.see("end")
        self.root.update()

    def start_download(self):
        """开始下载"""
        if not self.api_key.get().strip():
            messagebox.showerror("错误", "请输入GIPHY API密钥")
            return

        if not self.author_name.get().strip():
            messagebox.showerror("错误", "请输入作者用户名")
            return

        if not (self.download_gifs.get() or self.download_stickers.get()):
            messagebox.showerror("错误", "请至少选择一种内容类型")
            return

        # 保存当前配置
        self.save_config()

        # 创建下载目录
        os.makedirs(self.download_path.get(), exist_ok=True)

        # 更新界面状态
        self.is_downloading = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.result_text.delete("1.0", "end")

        # 启动下载线程
        self.download_thread = threading.Thread(target=self.download_content)
        self.download_thread.daemon = True
        self.download_thread.start()

    def stop_download(self):
        """停止下载"""
        self.is_downloading = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set("已停止")
        self.log_message("❌ 下载已停止")

    def search_user_content(self, content_type, username):
        """搜索用户内容"""
        base_url = f"https://api.giphy.com/v1/{content_type}/search"
        all_content = []
        offset = 0
        limit = 50

        while self.is_downloading:
            params = {
                'api_key': self.api_key.get(),
                'q': f'@{username}',
                'limit': limit,
                'offset': offset,
                'rating': 'g'
            }

            try:
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'data' not in data or not data['data']:
                    break

                all_content.extend(data['data'])

                if len(data['data']) < limit:
                    break

                offset += limit
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                self.log_message(f"❌ API请求失败: {str(e)}")
                break

        return all_content

    def get_quality_url(self, item, quality_key):
        """根据画质选择获取对应的URL"""
        try:
            images = item.get('images', {})
            quality_data = images.get(quality_key, {})

            if 'url' in quality_data:
                return quality_data['url']
            elif 'mp4' in quality_data:
                return quality_data['mp4']
            elif 'webp' in quality_data:
                return quality_data['webp']
            else:
                return images.get('original', {}).get('url', '')
        except:
            return ''

    def download_file(self, url, filepath):
        """下载单个文件"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.is_downloading:
                        return False
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            self.log_message(f"❌ 下载失败 {os.path.basename(filepath)}: {str(e)}")
            return False

    def download_content(self):
        """主要下载逻辑"""
        username = self.author_name.get().strip()
        download_dir = self.download_path.get()
        quality_key = self.quality_mapping[self.quality_option.get()]

        self.log_message(f"🔍 开始搜索用户 '{username}' 的内容...")
        self.progress_var.set(f"搜索中...")

        total_downloaded = 0
        all_items = []

        # 搜索GIFs
        if self.download_gifs.get() and self.is_downloading:
            self.progress_var.set("搜索GIF中...")
            gifs = self.search_user_content('gifs', username)
            if gifs:
                all_items.extend([('gif', item) for item in gifs])
                self.log_message(f"📁 找到 {len(gifs)} 个GIF文件")

        # 搜索Stickers
        if self.download_stickers.get() and self.is_downloading:
            self.progress_var.set("搜索贴纸中...")
            stickers = self.search_user_content('stickers', username)
            if stickers:
                all_items.extend([('sticker', item) for item in stickers])
                self.log_message(f"📁 找到 {len(stickers)} 个贴纸文件")

        if not all_items:
            self.progress_var.set("未找到内容")
            self.log_message("❌ 未找到任何内容")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            return

        self.log_message(f"🎯 共找到 {len(all_items)} 个文件，开始下载...")

        # 下载所有内容
        for i, (content_type, item) in enumerate(all_items, 1):
            if not self.is_downloading:
                break

            progress = i / len(all_items)
            self.progress_bar.set(progress)

            title = item.get('title', 'Untitled')[:18]
            self.progress_var.set(f"下载中 ({i}/{len(all_items)}): {title}...")

            type_dir = os.path.join(download_dir, username, f"{content_type}s")
            os.makedirs(type_dir, exist_ok=True)

            file_url = self.get_quality_url(item, quality_key)
            if not file_url:
                continue

            extension = '.mp4' if file_url.endswith('.mp4') else '.webp' if file_url.endswith('.webp') else '.gif'
            filename = f"{item['id']}{extension}"
            filepath = os.path.join(type_dir, filename)

            if self.download_file(file_url, filepath):
                total_downloaded += 1
                self.log_message(f"✅ 已下载: {filename} ({self.quality_option.get()}画质)")

        # 完成下载
        if self.is_downloading:
            self.progress_bar.set(1.0)
            self.progress_var.set(f"✨ 下载完成! 共 {total_downloaded} 个文件")
            self.log_message(f"🎉 下载完成! 总共下载了 {total_downloaded} 个文件")
            self.log_message(f"📂 文件保存位置: {os.path.join(download_dir, username)}")

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.is_downloading = False

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

def main():
    try:
        app = LargerFontGiphyDownloader()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败: {str(e)}")

if __name__ == "__main__":
    main()
