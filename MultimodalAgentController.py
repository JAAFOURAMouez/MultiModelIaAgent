import threading
import shutil
import tkinter as tk
from PIL import Image as PILImage, ImageTk
import cv2
from pathlib import Path
import time

class MultimodalAgentController:
    """Contrôleur - Gère la logique de contrôle et les interactions"""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.video_playing_thread = None
        
        self._bind_events()
    
    def _bind_events(self):
        """Lie les événements de la vue aux méthodes du contrôleur"""
        # Boutons d'upload - Correction de la liaison
        self.view.image_upload_btn.config(command=lambda: self.upload_file("image"))
        self.view.image_file_label.bind('<Button-1>', lambda e: self.preview_media("image"))
        
        self.view.audio_upload_btn.config(command=lambda: self.upload_file("audio"))
        self.view.audio_file_label.bind('<Button-1>', lambda e: self.preview_media("audio"))
        
        self.view.video_upload_btn.config(command=lambda: self.upload_file("video"))
        self.view.video_file_label.bind('<Button-1>', lambda e: self.preview_media("video"))
        
        # Contrôles de durée
        self.view.duration_minus_btn.config(command=lambda: self.change_duration(-1))
        self.view.duration_plus_btn.config(command=lambda: self.change_duration(1))
        
        # Boutons d'action
        self.view.generate_prompt_btn.config(command=self.generate_prompt)
        self.view.analyze_btn.config(command=self.analyze)
        self.view.generate_video_btn.config(command=self.generate_video)
        self.view.clear_btn.config(command=self.clear_all)
        
        # Contrôles vidéo
        self.view.play_btn.config(command=self.play_video)
        self.view.pause_btn.config(command=self.pause_video)
        self.view.stop_btn.config(command=self.stop_video)
        self.view.save_btn.config(command=self.save_video)
    
    # Supprimer la méthode _get_upload_button car elle n'est plus nécessaire
    
    def upload_file(self, file_type: str):
        """Gère l'upload d'un fichier"""
        filename = self.view.ask_file_path(file_type)
        
        if filename:
            self.model.set_media_file(file_type, filename)
            media_file = self.model.get_media_file(file_type)
            
            # Mettre à jour la vue
            label_var = getattr(self.view, f'{file_type}_label_var')
            label_var.set(media_file.display_name)
            
            self.view.update_status(
                f"✓ {file_type.capitalize()} chargé: {media_file.name} "
                f"(Cliquez sur le nom pour prévisualiser)"
            )
        else:
            self.model.set_media_file(file_type, None)
            label_var = getattr(self.view, f'{file_type}_label_var')
            label_var.set("Aucun fichier")
            self.view.update_status(f"Chargement de {file_type.capitalize()} annulé.")
    
    def preview_media(self, file_type: str):
        """Prévisualise un média"""
        media_file = self.model.get_media_file(file_type)
        
        if not media_file.exists:
            self.view.show_info("Information", f"Aucun fichier {file_type} chargé")
            return
        
        # Créer une fenêtre de prévisualisation
        preview_window = tk.Toplevel(self.view.root)
        preview_window.title(f"Prévisualisation - {media_file.name}")
        preview_window.configure(bg='#1e1e1e')
        preview_window.geometry("800x600")
        
        main_frame = tk.Frame(preview_window, bg='#1e1e1e', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        tk.Label(main_frame, text=f"📁 {media_file.name}", 
                bg='#1e1e1e', fg='#00d4ff', 
                font=('Segoe UI', 14, 'bold')).pack(pady=(0, 10))
        
        if file_type == 'image':
            self._preview_image(main_frame, media_file.path)
        elif file_type == 'video':
            self._preview_video(main_frame, media_file.path, preview_window)
        elif file_type == 'audio':
            self._preview_audio(main_frame, media_file.path)
        
        tk.Button(main_frame, text="✖️ Fermer", 
                 command=preview_window.destroy,
                 bg='#ff4444', fg='white', 
                 font=('Segoe UI', 10, 'bold')).pack(pady=(10, 0))
    
    def _preview_image(self, parent, image_path):
        """Prévisualise une image"""
        try:
            img = PILImage.open(image_path)
            max_size = (700, 500)
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            img_frame = tk.Frame(parent, bg='#000000', relief='sunken', bd=2)
            img_frame.pack(fill='both', expand=True)
            
            img_label = tk.Label(img_frame, image=photo, bg='#000000')
            img_label.image = photo
            img_label.pack(padx=10, pady=10)
            
            original_img = PILImage.open(image_path)
            info_text = f"Dimensions: {original_img.size[0]}x{original_img.size[1]}"
            tk.Label(parent, text=info_text, bg='#1e1e1e', fg='#888888', 
                    font=('Segoe UI', 9)).pack(pady=(5, 0))
            
        except Exception as e:
            tk.Label(parent, text=f"❌ Erreur: {str(e)}", 
                    bg='#1e1e1e', fg='#ff4444', 
                    font=('Segoe UI', 10)).pack()
    
    def _preview_video(self, parent, video_path, window):
        """Prévisualise une vidéo"""
        try:
            canvas = tk.Canvas(parent, bg='#000000', highlightthickness=0, height=400)
            canvas.pack(fill='both', expand=True)
            
            controls_frame = tk.Frame(parent, bg='#1e1e1e')
            controls_frame.pack(fill='x', pady=(10, 0))
            
            video_state = {'cap': cv2.VideoCapture(video_path), 'playing': False}
            
            def update_frame():
                if video_state['playing'] and video_state['cap'].isOpened():
                    ret, frame = video_state['cap'].read()
                    
                    if not ret:
                        video_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = video_state['cap'].read()
                    
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        canvas_width = canvas.winfo_width()
                        canvas_height = canvas.winfo_height()
                        
                        if canvas_width > 1 and canvas_height > 1:
                            h, w = frame.shape[:2]
                            ratio = min(canvas_width / w, canvas_height / h)
                            new_w = int(w * ratio)
                            new_h = int(h * ratio)
                            
                            frame = cv2.resize(frame, (new_w, new_h))
                            
                            img = PILImage.fromarray(frame)
                            photo = ImageTk.PhotoImage(image=img)
                            
                            canvas.delete('all')
                            canvas.create_image(canvas_width//2, canvas_height//2, 
                                              image=photo, anchor='center')
                            canvas.image = photo
                        
                        fps = video_state['cap'].get(cv2.CAP_PROP_FPS)
                        delay = int(1000 / fps) if fps > 0 else 30
                        canvas.after(delay, update_frame)
            
            def play_video():
                video_state['playing'] = True
                play_btn.config(state='disabled')
                pause_btn.config(state='normal')
                update_frame()
            
            def pause_video():
                video_state['playing'] = False
                play_btn.config(state='normal')
                pause_btn.config(state='disabled')
            
            def stop_video():
                video_state['playing'] = False
                video_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                play_btn.config(state='normal')
                pause_btn.config(state='disabled')
            
            play_btn = tk.Button(controls_frame, text="▶️ Lecture", command=play_video,
                               bg='#00d4ff', fg='black', font=('Segoe UI', 9, 'bold'))
            play_btn.pack(side='left', padx=5)
            
            pause_btn = tk.Button(controls_frame, text="⏸️ Pause", command=pause_video,
                                bg='#3d3d3d', fg='white', font=('Segoe UI', 9), 
                                state='disabled')
            pause_btn.pack(side='left', padx=5)
            
            stop_btn = tk.Button(controls_frame, text="⏹️ Stop", command=stop_video,
                               bg='#3d3d3d', fg='white', font=('Segoe UI', 9))
            stop_btn.pack(side='left', padx=5)
            
            cap_temp = cv2.VideoCapture(video_path)
            fps = cap_temp.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap_temp.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap_temp.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap_temp.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap_temp.release()
            
            info_text = f"Résolution: {width}x{height} | Durée: {duration:.1f}s | FPS: {fps:.1f}"
            tk.Label(controls_frame, text=info_text, bg='#1e1e1e', fg='#888888', 
                    font=('Segoe UI', 8)).pack(side='right', padx=10)
            
            ret, frame = video_state['cap'].read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = frame.shape[:2]
                ratio = min(700 / w, 400 / h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                frame = cv2.resize(frame, (new_w, new_h))
                
                img = PILImage.fromarray(frame)
                photo = ImageTk.PhotoImage(image=img)
                canvas.create_image(400, 200, image=photo, anchor='center')
                canvas.image = photo
            
            video_state['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            def on_close():
                video_state['playing'] = False
                if video_state['cap']:
                    video_state['cap'].release()
                window.destroy()
            
            window.protocol("WM_DELETE_WINDOW", on_close)
            
        except Exception as e:
            tk.Label(parent, text=f"❌ Erreur: {str(e)}", 
                    bg='#1e1e1e', fg='#ff4444', 
                    font=('Segoe UI', 10)).pack()
    
    def _preview_audio(self, parent, audio_path):
        """Prévisualise un fichier audio"""
        try:
            import pygame
            
            audio_frame = tk.Frame(parent, bg='#2d2d2d', relief='raised', bd=2)
            audio_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            tk.Label(audio_frame, text="🎵", bg='#2d2d2d', fg='#00d4ff', 
                    font=('Segoe UI', 48)).pack(pady=30)
            
            file_size = Path(audio_path).stat().st_size / (1024 * 1024)
            info_text = f"Taille: {file_size:.2f} MB\nFormat: {Path(audio_path).suffix}"
            tk.Label(audio_frame, text=info_text, bg='#2d2d2d', fg='#ffffff', 
                    font=('Segoe UI', 10), justify='center').pack(pady=10)
            
            pygame.mixer.init()
            audio_state = {'playing': False}
            
            def play_audio():
                try:
                    if not audio_state['playing']:
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play()
                        audio_state['playing'] = True
                        play_btn.config(text="⏸️ Pause")
                        status_label.config(text="▶️ Lecture en cours...", fg='#00ff00')
                    else:
                        pygame.mixer.music.pause()
                        audio_state['playing'] = False
                        play_btn.config(text="▶️ Lecture")
                        status_label.config(text="⏸️ Pause", fg='#ffaa00')
                except Exception as e:
                    status_label.config(text=f"❌ Erreur: {str(e)}", fg='#ff4444')
            
            def stop_audio():
                pygame.mixer.music.stop()
                audio_state['playing'] = False
                play_btn.config(text="▶️ Lecture")
                status_label.config(text="⏹️ Arrêté", fg='#888888')
            
            controls_frame = tk.Frame(audio_frame, bg='#2d2d2d')
            controls_frame.pack(pady=20)
            
            play_btn = tk.Button(controls_frame, text="▶️ Lecture", command=play_audio,
                               bg='#00d4ff', fg='black', font=('Segoe UI', 10, 'bold'),
                               width=12)
            play_btn.pack(side='left', padx=5)
            
            stop_btn = tk.Button(controls_frame, text="⏹️ Stop", command=stop_audio,
                               bg='#ff4444', fg='white', font=('Segoe UI', 10, 'bold'),
                               width=12)
            stop_btn.pack(side='left', padx=5)
            
            status_label = tk.Label(audio_frame, text="Prêt à jouer", 
                                  bg='#2d2d2d', fg='#888888', 
                                  font=('Segoe UI', 9, 'italic'))
            status_label.pack(pady=10)
            
        except ImportError:
            tk.Label(parent, 
                    text="❌ Module pygame non installé\nInstallez avec: pip install pygame", 
                    bg='#1e1e1e', fg='#ff4444', 
                    font=('Segoe UI', 10), justify='center').pack(pady=50)
        except Exception as e:
            tk.Label(parent, text=f"❌ Erreur: {str(e)}", 
                    bg='#1e1e1e', fg='#ff4444', 
                    font=('Segoe UI', 10)).pack()
    
    def change_duration(self, delta: int):
        """Change la durée de la vidéo"""
        new_value = self.view.duration_var.get() + delta
        if 4 <= new_value <= self.model.MAX_TOTAL_DURATION:
            self.view.duration_var.set(new_value)
            self.model.config.duration = new_value
    
    def generate_prompt(self):
        """Génère le prompt : rempli automatiquement par l'IA si des médias sont chargés, sinon gabarit à compléter"""
        # Synchroniser la config avec la vue
        self.model.config.duration = self.view.duration_var.get()
        self.model.config.style = self.view.style_var.get()
        self.model.config.analysis_options = {
            name: var.get() for name, var in self.view.analysis_vars.items()
        }

        if not self.model.has_media_files():
            self.view.set_prompt(self.model.generate_prompt())
            self.view.update_status("✅ Gabarit généré : complétez-le (ou chargez un média pour le remplissage automatique).")
            return

        self.view.generate_prompt_btn.config(state='disabled')
        self.view.start_progress()
        thread = threading.Thread(target=self._run_prompt_from_media)
        thread.daemon = True
        thread.start()

    def _run_prompt_from_media(self):
        """Analyse les médias (vision + audio) dans un thread et remplit le prompt"""
        try:
            prompt = self.model.generate_prompt_from_media(callback=self.view.update_status)
            self.view.set_prompt(prompt)
            self.view.update_status("✅ Champs remplis à partir de vos médias : relisez et ajustez avant d'analyser.")
        except Exception as e:
            self.view.set_prompt(self.model.generate_prompt())
            self.view.update_status(f"⚠️ Remplissage automatique impossible : {str(e)[:150]}")
            self.view.show_warning("Remplissage automatique", f"Impossible d'analyser les médias :\n{e}\n\nUn gabarit a été inséré à la place.")
        finally:
            self.view.stop_progress()
            self.view.generate_prompt_btn.config(state='normal')

    def analyze(self):
        """Lance l'analyse des médias"""
        query = self.view.get_prompt()
        
        if not query:
            self.view.show_warning("Attention", "Veuillez entrer une question!")
            return
        
        if not self.model.has_media_files():
            self.view.show_warning("Attention", 
                                  "Veuillez charger au moins un fichier média!")
            return
        
        self.view.enable_analyze_button(False)
        self.view.start_progress()
        self.view.result_text.config(state='disabled')
        self.view.update_result("", append=False)
        
        thread = threading.Thread(target=self._run_analysis, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self, query: str):
        """Exécute l'analyse dans un thread séparé"""
        try:
            self.view.update_status("📤 Préparation des fichiers...")
            
            def update_callback(text):
                self.view.update_result(text, append=True)
            
            self.view.update_status("🤖 Analyse en cours...")
            result = self.model.run_analysis(query, callback=update_callback)
            
            if not result.strip():
                self.view.update_result("\n❌ Aucune réponse reçue de l'agent.", append=True)
            
            self.view.update_status("✅ Analyse terminée! Modifiez le résultat si nécessaire.")
            
        except Exception as e:
            error_msg = f"❌ Erreur: {str(e)}"
            self.view.update_result(error_msg, append=False)
            self.view.update_status(error_msg)
            self.view.show_error("Erreur", str(e))
        
        finally:
            self.view.stop_progress()
            self.view.enable_analyze_button(True)
            self.view.result_text.config(state='normal')
    
    def generate_video(self):
        """Lance la génération de vidéo"""
        self.view.result_text.config(state='normal')
        final_prompt = self.view.get_analysis_result()
        
        if not final_prompt:
            self.view.show_warning("Attention", 
                "Le panneau de résultats est vide. Veuillez effectuer une analyse "
                "ou taper une prompt de génération vidéo.")
            return
        
        self.view.enable_analyze_button(False)
        self.view.start_progress()
        self.view.update_result(f"\n🎥 Lancement de la génération Hugging Face (LTX-Video)...\n", append=True)
        self.view.result_text.config(state='disabled')
        
        thread = threading.Thread(target=self._run_video_generation, args=(final_prompt,))
        thread.daemon = True
        thread.start()
    
    def _run_video_generation(self, prompt: str):
        """Exécute la génération vidéo dans un thread séparé"""
        try:
            # Synchroniser la config
            self.model.config.duration = self.view.duration_var.get()
            self.model.config.style = self.view.style_var.get()
            
            def progress_callback(message):
                self.view.update_result(f"{message}\n", append=True)
            
            video_path = self.model.generate_video(prompt, progress_callback)
            
            self.view.update_result(f"✅ Vidéo générée: {video_path}\n", append=True)
            self.view.update_status("✅ Vidéo générée et chargée dans le lecteur!")
            
            # Charger la vidéo dans le lecteur
            if self.view.load_video(video_path):
                self.view.update_status("✅ Vidéo prête à être visualisée!")
            
        except Exception as e:
            error_msg = f"\n❌ Erreur: {str(e)}\n"
            self.view.update_result(error_msg, append=True)
            self.view.update_status("❌ Erreur de génération")
            self.view.show_error("Erreur", f"Impossible de générer la vidéo:\n{str(e)}")
        
        finally:
            self.view.stop_progress()
            self.view.enable_analyze_button(True)
            self.view.result_text.config(state='normal')
    
    def play_video(self):
        """Démarre la lecture de la vidéo"""
        self.view.is_playing = True
        self.view.play_btn.config(state='disabled')
        self.view.pause_btn.config(state='normal')
        self.view.update_status("▶️ Lecture en cours...")
        
        self.video_playing_thread = threading.Thread(target=self._play_video_loop, daemon=True)
        self.video_playing_thread.start()
    
    def _play_video_loop(self):
        """Boucle de lecture vidéo"""
        fps = self.view.get_video_fps()
        delay = 1.0 / fps
        
        while self.view.is_playing:
            frame = self.view.get_video_frame()
            if frame is not None:
                self.view.display_frame(frame)
            time.sleep(delay)
    
    def pause_video(self):
        """Met en pause la vidéo"""
        self.view.is_playing = False
        self.view.play_btn.config(state='normal')
        self.view.pause_btn.config(state='disabled')
        self.view.update_status("⏸️ Vidéo en pause")
    
    def stop_video(self):
        """Arrête la vidéo"""
        self.view.is_playing = False
        self.view.play_btn.config(state='normal')
        self.view.pause_btn.config(state='disabled')
        self.view.show_first_frame()
        self.view.update_status("⏹️ Vidéo arrêtée")
    
    def save_video(self):
        """Sauvegarde la vidéo générée"""
        if not self.model.generated_video_path or \
           not Path(self.model.generated_video_path).exists():
            self.view.show_warning("Attention", "Aucune vidéo à sauvegarder")
            return
        
        save_path = self.view.ask_save_path()
        
        if save_path:
            try:
                shutil.copy(self.model.generated_video_path, save_path)
                self.view.update_status(f"✅ Vidéo sauvegardée: {Path(save_path).name}")
                self.view.show_info("Succès", f"Vidéo sauvegardée:\n{save_path}")
            except Exception as e:
                self.view.show_error("Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
    
    def clear_all(self):
        """Efface tout et réinitialise"""
        self.view.is_playing = False
        
        self.model.clear_all()
        
        self.view.image_label_var.set("Aucun fichier")
        self.view.audio_label_var.set("Aucun fichier")
        self.view.video_label_var.set("Aucun fichier")
        
        self.view.result_text.config(state='normal')
        self.view.result_text.delete('1.0', tk.END)
        
        self.view.enable_video_controls(False)
        self.view.reset_video_canvas()
        
        self.view.update_status("🗑️ Tout effacé")