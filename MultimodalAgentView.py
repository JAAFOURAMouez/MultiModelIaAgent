import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from PIL import Image as PILImage, ImageTk
import cv2
from typing import Optional
import time

class MultimodalAgentView:
    """Vue - Gère l'interface utilisateur"""
    
    STYLES = ["Années 1920", "Années 1980", "Cartoon", "Anime", "Ciné Réaliste", "Minimaliste"]
    
    def __init__(self, root):
        self.root = root
        self.root.title("Agent Multimodal IA - Création Vidéo")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Variables Tkinter
        self.image_label_var = tk.StringVar(value="Aucun fichier")
        self.audio_label_var = tk.StringVar(value="Aucun fichier")
        self.video_label_var = tk.StringVar(value="Aucun fichier")
        self.duration_var = tk.IntVar(value=5)
        self.style_var = tk.StringVar(value=self.STYLES[0])
        
        self.analysis_vars = {
            "Image": tk.BooleanVar(value=True),
            "Audio": tk.BooleanVar(),
            "Vidéo": tk.BooleanVar(),
            "Web Search": tk.BooleanVar(),
        }
        
        self.video_cap = None
        self.is_playing = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        self._setup_styles()
        self._create_header()
        self._create_main_container()
    
    def _setup_styles(self):
        """Configure les styles ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', background='#1e1e1e', foreground='#00d4ff', 
                       font=('Segoe UI', 20, 'bold'))
        style.configure('Subtitle.TLabel', background='#1e1e1e', foreground='#ffffff', 
                       font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=10)
    
    def _create_header(self):
        """Crée l'en-tête"""
        header_frame = tk.Frame(self.root, bg='#1e1e1e', pady=20)
        header_frame.pack(fill='x')
        
        ttk.Label(header_frame, text="🎬 Créateur Vidéo Multimodal IA", 
                 style='Title.TLabel').pack()
        ttk.Label(header_frame, 
                 text="Créez des vidéos à partir de vos médias et visualisez-les directement",
                 style='Subtitle.TLabel').pack()
    
    def _create_main_container(self):
        """Crée le conteneur principal"""
        main_container = tk.Frame(self.root, bg='#1e1e1e', padx=20)
        main_container.pack(fill='both', expand=True)
        
        # Panel gauche
        left_panel = tk.Frame(main_container, bg='#2d2d2d', relief='raised', bd=2)
        left_panel.pack(side='left', fill='both', expand=False, padx=(0, 10), ipadx=10)
        self._create_left_panel(left_panel)
        
        # Panel droit
        right_panel = tk.Frame(main_container, bg='#2d2d2d', relief='raised', bd=2)
        right_panel.pack(side='right', fill='both', expand=True)
        self._create_right_panel(right_panel)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Prêt", bg='#0d0d0d', fg='#00d4ff',
                                     font=('Segoe UI', 9), anchor='w', padx=10)
        self.status_label.pack(side='bottom', fill='x')
    
    def _create_left_panel(self, parent):
        """Crée le panel gauche (contrôles)"""
        # Titre
        tk.Label(parent, text="📁 Fichiers Média", 
                bg='#2d2d2d', fg='#00d4ff', 
                font=('Segoe UI', 14, 'bold'), pady=10).pack()
        
        # Upload des fichiers
        upload_container = tk.Frame(parent, bg='#2d2d2d', padx=10, pady=5)
        upload_container.pack(fill='x')
        
        self._create_file_upload_button(upload_container, "🖼️ Image", "image", 
                                       self.image_label_var)
        self._create_file_upload_button(upload_container, "🎵 Audio", "audio", 
                                       self.audio_label_var)
        self._create_file_upload_button(upload_container, "🎬 Vidéo", "video", 
                                       self.video_label_var)
        
        # Options d'analyse
        self._create_analysis_options(parent)
        
        # Durée
        self._create_duration_control(parent)
        
        # Style
        self._create_style_selector(parent)
        
        # Prompt
        self._create_prompt_editor(parent)
        
        # Boutons d'action
        self._create_action_buttons(parent)
    
    def _create_file_upload_button(self, parent, label, file_type, label_var):
        """Crée un bouton d'upload de fichier"""
        frame = tk.Frame(parent, bg='#2d2d2d', pady=5, padx=5)
        frame.pack(side='left', fill='y')
        
        btn = tk.Button(frame, text=label, bg='#3d3d3d', fg='#ffffff', 
                        font=('Segoe UI', 10), cursor='hand2', 
                        width=12, relief='flat')
        btn.pack(pady=(0, 2))
        
        file_label = tk.Label(frame, textvariable=label_var, bg='#2d2d2d', 
                            fg='#888888', font=('Segoe UI', 7, 'italic'), 
                            anchor='center', wraplength=80, cursor='hand2')
        file_label.pack(fill='x')
        
        # Stocker les références selon le type
        if file_type == "image":
            self.image_upload_btn = btn
            self.image_file_label = file_label
        elif file_type == "audio":
            self.audio_upload_btn = btn
            self.audio_file_label = file_label
        elif file_type == "video":
            self.video_upload_btn = btn
            self.video_file_label = file_label
        
        return btn, file_label
    
    def _create_analysis_options(self, parent):
        """Crée les options d'analyse"""
        option_frame = tk.LabelFrame(parent, text="🧠 Type d'analyse", 
                                     bg='#2d2d2d', fg='#ffffff', 
                                     font=('Segoe UI', 10, 'bold'))
        option_frame.pack(fill='x', padx=10, pady=10)
        
        cb_frame = tk.Frame(option_frame, bg='#2d2d2d')
        cb_frame.pack(fill='x', padx=5, pady=5)
        
        for name, var in self.analysis_vars.items():
            tk.Checkbutton(cb_frame, text=name, variable=var, 
                          bg='#2d2d2d', fg='white', 
                          selectcolor='#1e1e1e').pack(side='left', padx=10)
    
    def _create_duration_control(self, parent):
        """Crée le contrôle de durée"""
        duration_frame = tk.LabelFrame(parent, text="⏱️ Durée de la vidéo (4-8 secondes)", 
                                       bg='#2d2d2d', fg='#ffffff', 
                                       font=('Segoe UI', 10, 'bold'))
        duration_frame.pack(fill='x', padx=10, pady=10)
        
        self.duration_minus_btn = tk.Button(duration_frame, text="-", 
                                           bg='#3d3d3d', fg='white', width=4)
        self.duration_minus_btn.pack(side='left', padx=5)
        
        tk.Label(duration_frame, textvariable=self.duration_var, 
                bg='#2d2d2d', fg='#00d4ff',
                font=('Segoe UI', 12, 'bold')).pack(side='left', padx=5)
        
        self.duration_plus_btn = tk.Button(duration_frame, text="+", 
                                          bg='#3d3d3d', fg='white', width=4)
        self.duration_plus_btn.pack(side='left', padx=5)
    
    def _create_style_selector(self, parent):
        """Crée le sélecteur de style"""
        style_frame = tk.LabelFrame(parent, text="🎨 Style Visuel", 
                                   bg='#2d2d2d', fg='#ffffff', 
                                   font=('Segoe UI', 10, 'bold'))
        style_frame.pack(fill='x', padx=10, pady=10)
        
        style_menu = ttk.Combobox(style_frame, textvariable=self.style_var, 
                                 values=self.STYLES, state='readonly')
        style_menu.pack(fill='x', padx=10, pady=5)
    
    def _create_prompt_editor(self, parent):
        """Crée l'éditeur de prompt"""
        query_frame = tk.Frame(parent, bg='#2d2d2d', pady=10)
        query_frame.pack(fill='both', expand=True, padx=10)
        
        tk.Label(query_frame, text="💬 Prompt à générer ou modifier", 
                bg='#2d2d2d', fg='white', 
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0,5))
        
        self.query_text = scrolledtext.ScrolledText(query_frame, wrap=tk.WORD, 
                                                    height=4, font=('Segoe UI', 10),
                                                    bg='#3d3d3d', fg='white', 
                                                    insertbackground='white')
        self.query_text.pack(fill='both', expand=True)
        self.query_text.insert('1.0', "Décrivez en détail le contenu des fichiers média fournis.")
        
        self.generate_prompt_btn = tk.Button(query_frame, text="🧩 Générer le Prompt",
                                            bg='#00b8e6', fg='black', 
                                            font=('Segoe UI', 10, 'bold'))
        self.generate_prompt_btn.pack(fill='x', pady=5)
    
    def _create_action_buttons(self, parent):
        """Crée les boutons d'action"""
        btn_frame = tk.Frame(parent, bg='#2d2d2d', pady=10)
        btn_frame.pack(fill='x', padx=10)
        
        self.analyze_btn = tk.Button(btn_frame, text="🚀 Analyser",
                                     bg='#00d4ff', fg='black', 
                                     font=('Segoe UI', 12, 'bold'), relief='flat')
        self.analyze_btn.pack(fill='x', ipady=10)
        
        self.generate_video_btn = tk.Button(btn_frame, text="🎥 Générer la vidéo",
                                           bg='#ffaa00', fg='black', 
                                           font=('Segoe UI', 12, 'bold'), relief='flat')
        self.generate_video_btn.pack(fill='x', pady=(5, 0), ipady=10)
        
        self.clear_btn = tk.Button(btn_frame, text="🗑️ Effacer",
                                   bg='#ff4444', fg='white', 
                                   font=('Segoe UI', 10))
        self.clear_btn.pack(fill='x', pady=(5, 0), ipady=5)
    
    def _create_right_panel(self, parent):
        """Crée le panel droit (résultats + vidéo)"""
        # Lecteur vidéo
        video_frame = tk.LabelFrame(parent, text="🎬 Lecteur Vidéo", 
                                   bg='#2d2d2d', fg='#00d4ff', 
                                   font=('Segoe UI', 12, 'bold'), 
                                   padx=10, pady=10)
        video_frame.pack(fill='both', expand=True, padx=10, pady=(10, 5))
        
        self.video_canvas = tk.Canvas(video_frame, bg='#000000', highlightthickness=0)
        self.video_canvas.pack(fill='both', expand=True, pady=(0, 10))
        
        self.video_canvas.create_text(200, 150,
                                      text="La vidéo générée s'affichera ici",
                                      fill='#666666', font=('Segoe UI', 14),
                                      tags='placeholder')
        
        # Contrôles vidéo
        self._create_video_controls(video_frame)
        
        # Résultats de l'analyse
        self._create_results_panel(parent)
    
    def _create_video_controls(self, parent):
        """Crée les contrôles vidéo"""
        controls_frame = tk.Frame(parent, bg='#2d2d2d')
        controls_frame.pack(fill='x')
        
        self.play_btn = tk.Button(controls_frame, text="▶️ Lecture",
                                  bg='#00d4ff', fg='black', 
                                  font=('Segoe UI', 10, 'bold'), state='disabled')
        self.play_btn.pack(side='left', padx=5)
        
        self.pause_btn = tk.Button(controls_frame, text="⏸️ Pause",
                                   bg='#3d3d3d', fg='white', 
                                   font=('Segoe UI', 10), state='disabled')
        self.pause_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(controls_frame, text="⏹️ Stop",
                                  bg='#3d3d3d', fg='white', 
                                  font=('Segoe UI', 10), state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        self.save_btn = tk.Button(controls_frame, text="💾 Sauvegarder",
                                  bg='#00cc88', fg='black', 
                                  font=('Segoe UI', 10, 'bold'), state='disabled')
        self.save_btn.pack(side='right', padx=5)
    
    def _create_results_panel(self, parent):
        """Crée le panel de résultats"""
        tk.Label(parent, text="📊 Résultats de l'Analyse", 
                bg='#2d2d2d', fg='#00d4ff', 
                font=('Segoe UI', 12, 'bold'), pady=5).pack()
        
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD,
                                                     font=('Segoe UI', 9),
                                                     bg='#3d3d3d', fg='white',
                                                     insertbackground='white',
                                                     state='normal', height=8)
        self.result_text.pack(fill='both', expand=False, padx=10, pady=(5, 10))
    
    # Méthodes d'accès aux données de la vue
    
    def get_prompt(self) -> str:
        return self.query_text.get('1.0', tk.END).strip()
    
    def set_prompt(self, text: str):
        self.query_text.delete('1.0', tk.END)
        self.query_text.insert('1.0', text)
    
    def get_analysis_result(self) -> str:
        return self.result_text.get('1.0', tk.END).strip()
    
    def update_result(self, text: str, append=True):
        self.result_text.config(state='normal')
        if not append:
            self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, message: str):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def start_progress(self):
        self.progress.start(10)
    
    def stop_progress(self):
        self.progress.stop()
    
    def enable_analyze_button(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        text = "🚀 Analyser" if enabled else "⏳ Analyse en cours..."
        self.analyze_btn.config(state=state, text=text)
    
    def enable_video_controls(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        self.play_btn.config(state=state)
        self.pause_btn.config(state=state)
        self.stop_btn.config(state=state)
        self.save_btn.config(state=state)
    
    def ask_file_path(self, file_type: str) -> Optional[str]:
        """Ouvre une boîte de dialogue pour sélectionner un fichier"""
        filetypes_map = {
            "image": [("Images", "*.jpg *.jpeg *.png *.gif *.bmp")],
            "audio": [("Audio", "*.mp3 *.wav *.ogg *.m4a")],
            "video": [("Vidéo", "*.mp4 *.avi *.mov *.mkv")]
        }
        
        filetypes = filetypes_map.get(file_type, []) + [("Tous les fichiers", "*.*")]
        return filedialog.askopenfilename(filetypes=filetypes)
    
    def ask_save_path(self) -> Optional[str]:
        """Ouvre une boîte de dialogue pour sauvegarder"""
        return filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("Vidéo MP4", "*.mp4"), ("Tous les fichiers", "*.*")],
            initialfile=f"video_veo_{int(time.time())}.mp4"
        )
    
    def show_error(self, title: str, message: str):
        messagebox.showerror(title, message)
    
    def show_warning(self, title: str, message: str):
        messagebox.showwarning(title, message)
    
    def show_info(self, title: str, message: str):
        messagebox.showinfo(title, message)
    
    # Méthodes pour le lecteur vidéo
    
    def load_video(self, video_path: str):
        """Charge une vidéo dans le lecteur"""
        if self.video_cap is not None:
            self.video_cap.release()
        
        self.video_cap = cv2.VideoCapture(video_path)
        if self.video_cap.isOpened():
            self.show_first_frame()
            self.enable_video_controls(True)
            return True
        return False
    
    def show_first_frame(self):
        """Affiche la première frame de la vidéo"""
        if self.video_cap is None:
            return
        
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.video_cap.read()
        
        if ret:
            self.display_frame(frame)
    
    def display_frame(self, frame):
        """Affiche une frame sur le canvas"""
        self.video_canvas.delete('placeholder')
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 640
            canvas_height = 360
        
        frame_height, frame_width = frame.shape[:2]
        ratio = min(canvas_width / frame_width, canvas_height / frame_height)
        
        new_width = int(frame_width * ratio)
        new_height = int(frame_height * ratio)
        
        frame = cv2.resize(frame, (new_width, new_height))
        
        img = PILImage.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        self.video_canvas.delete('video')
        self.video_canvas.create_image(x, y, anchor='nw', image=imgtk, tags='video')
        self.video_canvas.image = imgtk
    
    def get_video_frame(self):
        """Récupère la frame suivante de la vidéo"""
        if self.video_cap is None or not self.video_cap.isOpened():
            return None
        
        ret, frame = self.video_cap.read()
        if not ret:
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_cap.read()
        
        return frame if ret else None
    
    def get_video_fps(self):
        """Récupère les FPS de la vidéo"""
        if self.video_cap is None:
            return 30
        return self.video_cap.get(cv2.CAP_PROP_FPS) or 30
    
    def reset_video_canvas(self):
        """Réinitialise le canvas vidéo"""
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
        
        self.video_canvas.delete('video')
        canvas_width = self.video_canvas.winfo_width() if self.video_canvas.winfo_width() > 1 else 200
        canvas_height = self.video_canvas.winfo_height() if self.video_canvas.winfo_height() > 1 else 150
        
        self.video_canvas.create_text(
            canvas_width // 2, canvas_height // 2,
            text="La vidéo générée s'affichera ici",
            fill='#666666', font=('Segoe UI', 14),
            tags='placeholder'
        )