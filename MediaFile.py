from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import time
import re

# --- Prompts ---------------------------------------------------------------
# Description anglaise de chaque style (LTX-Video et MMAudio répondent mieux à l'anglais)
STYLE_DESCRIPTIONS = {
    "Années 1920": "1920s silent-film era look, black and white, film grain, flickering light, vintage lenses",
    "Années 1980": "1980s retro aesthetic, VHS texture, neon colors, synthwave mood, soft glow",
    "Cartoon": "vibrant 3D cartoon animation, expressive characters, bold saturated colors, smooth motion",
    "Anime": "Japanese anime style, hand-drawn look, dynamic framing, vivid colors, cel shading",
    "Ciné Réaliste": "photorealistic cinematic look, shallow depth of field, natural lighting, 35mm film, high detail",
    "Minimaliste": "minimalist composition, clean background, limited color palette, calm and elegant motion",
}

PROMPT_ENGINEER_INSTRUCTIONS = [
    "You are an expert prompt engineer for text-to-video (LTX-Video) and video-to-audio (MMAudio) models.",
    "Turn the user's request (usually in French) into an optimized prompt. Always answer in ENGLISH, with EXACTLY this format and nothing else:",
    "VIDEO: <one single paragraph of 4 to 6 flowing sentences in the present tense>",
    "AUDIO: <one or two sentences describing the sounds>",
    "VIDEO rules: start with the main subject and its action, then describe the setting, the camera movement (e.g. slow dolly-in, handheld, tracking shot), the lighting and colors, the mood and the requested visual style. "
    "Describe only what can be SEEN and one coherent continuous shot that fits the requested duration. "
    "Be concrete and visual (textures, materials, motion). No scene cuts, no on-screen text or subtitles, no lists, no brand names.",
    "AUDIO rules: describe realistic diegetic sound effects and ambience matching the scene (footsteps, wind, rain, crowd murmur, engine, water...), "
    "with their intensity. Mention background music only if the user asks for it. No dialogue or lyrics.",
    "Never invent the content of media files you cannot see: rely on the user's description. Do not add explanations, titles or markdown.",
]


@dataclass
class MediaFile:
    """Représente un fichier média"""
    path: Optional[str] = None
    file_type: str = ""
    
    @property
    def exists(self) -> bool:
        return self.path is not None and Path(self.path).exists()
    
    @property
    def name(self) -> str:
        if self.path:
            return Path(self.path).name
        return "Aucun fichier"
    
    @property
    def display_name(self) -> str:
        name = self.name
        if len(name) > 12 and name != "Aucun fichier":
            return "..." + name[-9:]
        return name


@dataclass
class VideoGenerationConfig:
    """Configuration pour la génération vidéo"""
    duration: int = 5
    style: str = "Années 1920"
    analysis_options: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.analysis_options is None:
            self.analysis_options = {
                "Image": True,
                "Audio": False,
                "Vidéo": False,
                "Web Search": False,
            }
    
    @property
    def selected_analyses(self) -> List[str]:
        return [name for name, enabled in self.analysis_options.items() if enabled]


class MultimodalAgentModel:
    """Modèle principal - Gère les données et la logique métier"""
    
    def __init__(self):
        self.image = MediaFile(file_type="image")
        self.audio = MediaFile(file_type="audio")
        self.video = MediaFile(file_type="video")
        self.generated_video_path: Optional[str] = None
        self.config = VideoGenerationConfig()
        self.analysis_result: str = ""
        
        # Initialisation de l'agent (Groq + modèles OpenAI open-weight)
        from agno.agent import Agent
        from agno.models.groq import Groq
        from agno.tools.duckduckgo import DuckDuckGoTools
        import os

        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("Clé API Groq (GROQ_API_KEY) non trouvée. Ajoutez-la dans le fichier .env")

        # Modèles essayés dans l'ordre en cas de surcharge / limite de débit ; modifiable via GROQ_MODELS dans .env
        self.llm_models = [
            m.strip() for m in os.getenv(
                "GROQ_MODELS", "openai/gpt-oss-120b,openai/gpt-oss-20b"
            ).split(",") if m.strip()
        ]

        self.agent = Agent(
            model=Groq(id=self.llm_models[0]),
            instructions=PROMPT_ENGINEER_INSTRUCTIONS,
            tools=[DuckDuckGoTools()],
            markdown=True
        )

    def set_media_file(self, file_type: str, path: Optional[str]):
        """Définit le chemin d'un fichier média"""
        if file_type == "image":
            self.image.path = path
        elif file_type == "audio":
            self.audio.path = path
        elif file_type == "video":
            self.video.path = path
    
    def get_media_file(self, file_type: str) -> MediaFile:
        """Récupère un fichier média"""
        if file_type == "image":
            return self.image
        elif file_type == "audio":
            return self.audio
        elif file_type == "video":
            return self.video
        return MediaFile()
    
    def has_media_files(self) -> bool:
        """Vérifie si au moins un fichier média est chargé"""
        return any([self.image.exists, self.audio.exists, self.video.exists])
    
    def generate_prompt(self) -> str:
        """Génère un prompt de départ (à compléter avec votre idée) pour l'agent"""
        style = self.config.style
        duration = self.config.duration
        sound = "avec une ambiance sonore réaliste générée automatiquement" if not self.audio.exists \
            else "avec la piste audio fournie"
        return (
            f"Crée une vidéo de {duration} secondes, style \"{style}\", {sound}.\n"
            "Idée de la scène : [décrivez ici le sujet, l'action, le lieu et l'ambiance]\n"
            "Caméra souhaitée : [ex. travelling avant lent, plan fixe, caméra à l'épaule]\n"
            "Sons souhaités : [ex. vent, pas sur le gravier, ville au loin]"
        )

    @staticmethod
    def parse_prompt(text: str):
        """Sépare le texte final en (prompt vidéo, prompt audio) grâce aux marqueurs VIDEO: / AUDIO:"""
        m_audio = re.search(r"(?im)^\s*\**AUDIO\**\s*:\**\s*(.+?)\s*\Z", text, re.S)
        video = text
        audio = ""
        if m_audio:
            audio = m_audio.group(1).strip()
            video = text[:m_audio.start()]
        video = re.sub(r"(?im)^\s*\**VIDEO\**\s*:\**\s*", "", video).strip()
        return video, audio

    # --- Compréhension des médias fournis (vision + transcription) -------------
    VISION_MODEL = "qwen/qwen3.8-27b"           # modèle Groq avec vision (max 3 images/requête)
    STT_MODEL = "whisper-large-v3-turbo"        # transcription Groq

    @staticmethod
    def _b64_jpeg(pil_image, max_side: int = 1024) -> str:
        import base64, io
        img = pil_image.convert("RGB")
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _visual_inputs(self, max_images: int = 3):
        """Images (base64) à décrire : l'image chargée et/ou des images clés de la vidéo"""
        from PIL import Image as PILImage
        images = []
        if self.image.exists:
            with PILImage.open(self.image.path) as im:
                images.append(self._b64_jpeg(im))
        if self.video.exists and len(images) < max_images:
            import cv2
            cap = cv2.VideoCapture(self.video.path)
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            wanted = max_images - len(images)
            wanted = min(wanted, 3 if not images else 2)
            for k in range(wanted):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frames * (k + 0.5) / wanted) if frames else 0)
                ok, frame = cap.read()
                if ok:
                    images.append(self._b64_jpeg(PILImage.fromarray(frame[:, :, ::-1])))
            cap.release()
        return images

    def _transcribe_audio(self, client):
        """Transcrit l'audio fourni (ou la piste audio de la vidéo). Renvoie (texte, parole_détectée) ou None"""
        import subprocess
        import tempfile
        source, cleanup = None, None
        if self.audio.exists:
            source = self.audio.path
        elif self.video.exists:
            cleanup = tempfile.NamedTemporaryFile(suffix=".flac", delete=False).name
            res = subprocess.run(
                [self._ffmpeg(), "-y", "-i", self.video.path, "-vn", "-ac", "1", "-ar", "16000", cleanup],
                capture_output=True, timeout=120)
            if res.returncode == 0 and Path(cleanup).exists() and Path(cleanup).stat().st_size > 1000:
                source = cleanup
        if not source:
            return None
        try:
            if Path(source).stat().st_size > 24 * 1024 * 1024:
                return ("(fichier audio trop volumineux pour la transcription)", False)
            with open(source, "rb") as f:
                tr = client.audio.transcriptions.create(
                    file=(Path(source).name, f.read()), model=self.STT_MODEL, response_format="verbose_json")
            text = (getattr(tr, "text", "") or "").strip()
            segs = getattr(tr, "segments", None) or []
            probs = [s.get("no_speech_prob", 0) if isinstance(s, dict) else getattr(s, "no_speech_prob", 0) for s in segs]
            speech = bool(text) and (not probs or sum(probs) / len(probs) < 0.6)
            return (text, speech)
        finally:
            if cleanup:
                try:
                    Path(cleanup).unlink()
                except OSError:
                    pass

    def _chat(self, client, models, messages, max_tokens=700):
        """Appel Groq avec relances et modèles de secours"""
        last = None
        for model_id in models:
            for attempt in range(3):
                try:
                    r = client.chat.completions.create(model=model_id, messages=messages, max_tokens=max_tokens, temperature=0.4)
                    return (r.choices[0].message.content or "").strip()
                except Exception as e:
                    last = e
                    if not self._is_transient(e):
                        raise
                    time.sleep(2 ** attempt * 2)
        raise RuntimeError(f"Groq indisponible : {last}")

    def generate_prompt_from_media(self, callback=None) -> str:
        """Remplit automatiquement (scène / caméra / sons) à partir de l'image, l'audio ou la vidéo fournis"""
        import os
        from groq import Groq

        def say(msg):
            if callback:
                callback(msg)

        client = Groq()
        vision_model = os.getenv("GROQ_VISION_MODEL", self.VISION_MODEL)
        notes = []

        images = self._visual_inputs()
        if images:
            say("🖼️ Analyse visuelle des médias...")
            content = [{"type": "text", "text": (
                "Describe precisely what you see, in English: main subject(s), action or pose, setting/location, "
                "time of day, lighting and colors, mood, camera framing and angle (and apparent camera movement if "
                "these are consecutive frames of a video), and which sounds this scene would naturally have. "
                "Only describe what is visible. Max 150 words.")}]
            content += [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}"}} for b in images]
            notes.append("VISUAL DESCRIPTION: " + self._chat(
                client, [vision_model], [{"role": "user", "content": content}], max_tokens=500))

        if self.audio.exists or self.video.exists:
            say("🎧 Transcription de l'audio...")
            try:
                tr = self._transcribe_audio(client)
            except Exception as e:
                tr = None
                notes.append(f"AUDIO: transcription impossible ({str(e)[:120]}).")
            if tr:
                text, speech = tr
                if speech and text:
                    notes.append(f'AUDIO TRANSCRIPT (speech detected): "{text[:1500]}"')
                else:
                    notes.append("AUDIO: no clear speech detected (probably music, ambience or noise); "
                                 "its exact content is unknown, so do not invent it.")

        if not notes:
            return self.generate_prompt()

        say("✍️ Rédaction des champs...")
        sound_mode = "avec la piste audio fournie" if self.audio.exists else "avec une ambiance sonore réaliste générée automatiquement"
        system = (
            "Tu aides à préparer une vidéo courte à partir de médias fournis par l'utilisateur. "
            "À partir des notes d'analyse, remplis EXACTEMENT ces trois lignes, en français, concrètes et visuelles, "
            "sans rien inventer qui contredise les notes (tu peux proposer une suite logique de l'action) :\n"
            "SCENE: <sujet, action, lieu, ambiance, en 1 à 3 phrases>\n"
            "CAMERA: <mouvement et cadrage de caméra adaptés>\n"
            "SONS: <bruitages et ambiance sonore adaptés ; si une transcription existe, mentionne la voix/les paroles>\n"
            "Aucune autre ligne, aucun markdown."
        )
        user = (f"Durée : {self.config.duration} s. Style : {self.config.style}.\n\n" + "\n\n".join(notes))
        out = self._chat(client, self.llm_models, [{"role": "system", "content": system}, {"role": "user", "content": user}])

        def field(name, default):
            m = re.search(rf"(?im)^\s*\**{name}\**\s*:\**\s*(.+?)\s*(?=^\s*\**(?:SCENE|CAMERA|SONS)\**\s*:|\Z)", out, re.S)
            return m.group(1).strip() if m else default

        scene = field("SCENE", "[décrivez ici le sujet, l'action, le lieu et l'ambiance]")
        camera = field("CAMERA", "[ex. travelling avant lent, plan fixe, caméra à l'épaule]")
        sons = field("SONS", "[ex. vent, pas sur le gravier, ville au loin]")
        return (
            f"Crée une vidéo de {self.config.duration} secondes, style \"{self.config.style}\", {sound_mode}.\n"
            f"Idée de la scène : {scene}\n"
            f"Caméra souhaitée : {camera}\n"
            f"Sons souhaités : {sons}"
        )

    def describe_media(self) -> str:
        """Décrit en texte les médias chargés (les modèles gpt-oss de Groq sont texte uniquement)"""
        lines = []
        if self.image.exists:
            info = ""
            try:
                from PIL import Image as PILImage
                with PILImage.open(self.image.path) as im:
                    info = f", {im.width}x{im.height}px, mode {im.mode}"
            except Exception:
                pass
            lines.append(f"- Image : {self.image.name}{info}")
        if self.audio.exists:
            size_mb = Path(self.audio.path).stat().st_size / 1_048_576
            lines.append(f"- Audio : {self.audio.name} ({size_mb:.1f} Mo)")
        if self.video.exists:
            info = ""
            try:
                import cv2
                cap = cv2.VideoCapture(self.video.path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 0
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                info = f", {w}x{h}, {frames / fps:.1f}s" if fps else ""
            except Exception:
                pass
            lines.append(f"- Vidéo : {self.video.name}{info}")
        if not lines:
            return ""
        return ("Fichiers fournis par l'utilisateur (contenu non visible, seules ces métadonnées sont connues ; "
                "n'invente pas leur contenu, appuie-toi sur le prompt de l'utilisateur) :\n" + "\n".join(lines))

    @staticmethod
    def _is_transient(error: Exception) -> bool:
        msg = str(error).lower()
        return any(k in msg for k in ("503", "unavailable", "overloaded", "high demand", "429", "resource_exhausted", "rate limit", "rate_limit", "502"))

    def run_analysis(self, query: str, callback=None, retries_per_model: int = 3):
        """Analyse avec relances (backoff) et bascule sur un modèle de secours si Groq est surchargé"""
        from agno.models.groq import Groq

        last_error = None
        for model_id in self.llm_models:
            self.agent.model = Groq(id=model_id)
            for attempt in range(retries_per_model):
                try:
                    if callback and (attempt or model_id != self.llm_models[0]):
                        callback(f"\n[Modèle {model_id}, tentative {attempt + 1}]\n")
                    return self._run_analysis_once(query, callback)
                except Exception as e:
                    last_error = e
                    if not self._is_transient(e):
                        raise
                    time.sleep(2 ** attempt * 2)  # 2 s, 4 s, 8 s
        raise RuntimeError(
            f"Groq est indisponible ou limité sur tous les modèles essayés ({', '.join(self.llm_models)}). "
            f"Réessayez dans quelques minutes. Dernière erreur : {last_error}"
        )

    def _run_analysis_once(self, query: str, callback=None):
        """Exécute l'analyse avec l'agent"""
        media_info = self.describe_media()
        full_query = f"{query}\n\n{media_info}" if media_info else query

        response_generator = self.agent.run(full_query, stream=True)
        result_text = ""
        
        try:
            for chunk in response_generator:
                if hasattr(chunk, 'content'):
                    content = ""
                    if isinstance(chunk.content, str):
                        content = chunk.content
                    elif hasattr(chunk.content, 'text'):
                        content = chunk.content.text
                    
                    if content:
                        result_text += content
                        if callback:
                            callback(content)
        except TypeError:
            if hasattr(response_generator, 'content'):
                if isinstance(response_generator.content, str):
                    result_text = response_generator.content
                elif hasattr(response_generator.content, 'text'):
                    result_text = response_generator.content.text
                else:
                    result_text = str(response_generator.content)
            else:
                result_text = str(response_generator)
            
            if callback:
                callback(result_text)
        
        self.analysis_result = result_text
        return result_text
    
    # --- Génération vidéo via Hugging Face Spaces (gradio_client) ------------
    HF_DEFAULT_SPACE = "Lightricks/ltx-video-distilled"  # LTX-Video, ZeroGPU
    HF_MAX_DURATION = 8.0  # durée max d'un segment (le Space accepte 0.3 à 8.5 s)
    MAX_TOTAL_DURATION = int(__import__("os").getenv("HF_MAX_TOTAL", "24"))  # durée totale max (segments enchaînés)

    def _generate_silent_video(self, video_prompt: str, progress_callback=None, duration=None, image_path=None):
        """Génère une vidéo (sans son) en appelant un Space Hugging Face (texte→vidéo, ou image→vidéo si une image est chargée)"""
        import os
        import shutil
        from gradio_client import Client, handle_file

        token = os.getenv("HF_TOKEN") or None
        space = os.getenv("HF_SPACE", self.HF_DEFAULT_SPACE)
        if not token and progress_callback:
            progress_callback("⚠️ Pas de HF_TOKEN : quota GPU réduit (2 min/jour) et file d'attente lente.\n")

        duration = float(min(max(duration if duration is not None else self.config.duration, 1), self.HF_MAX_DURATION))
        width = int(os.getenv("HF_WIDTH", "704"))
        height = int(os.getenv("HF_HEIGHT", "512"))
        use_image = bool(image_path)

        style_desc = STYLE_DESCRIPTIONS.get(self.config.style, self.config.style)
        final_prompt = f"{video_prompt} Visual style: {style_desc}."
        params = {
            "prompt": final_prompt,
            "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, distorted",
            "height_ui": height,
            "width_ui": width,
            "mode": "image-to-video" if use_image else "text-to-video",
            "duration_ui": duration,
            "randomize_seed": True,
        }
        api_name = "/image_to_video" if use_image else "/text_to_video"
        if use_image:
            params["input_image_filepath"] = handle_file(image_path)

        if progress_callback:
            progress_callback(f"Connexion au Space {space}...\n")
        try:
            client = Client(space, token=token) if token else Client(space)
        except TypeError:  # anciennes versions de gradio_client : paramètre hf_token
            client = Client(space, hf_token=token)

        # On ne transmet que les paramètres réellement exposés par le Space (robuste aux mises à jour)
        try:
            info = client.view_api(return_format="dict", print_info=False)
            endpoint = info["named_endpoints"][api_name]
            accepted = {p.get("parameter_name") for p in endpoint["parameters"]}
            params = {k: v for k, v in params.items() if k in accepted}
        except Exception:
            pass  # on tente quand même avec tous les paramètres

        if progress_callback:
            mode_txt = "image→vidéo" if use_image else "texte→vidéo"
            progress_callback(f"Génération {mode_txt} ({duration:.1f}s, {width}x{height}), patientez (file d'attente GPU)...\n")

        try:
            job = client.submit(api_name=api_name, **params)
            result = job.result(timeout=900)
        except Exception as e:
            msg = str(e)
            if "quota" in msg.lower() or "gpu" in msg.lower():
                raise RuntimeError(
                    "Quota GPU ZeroGPU épuisé (il se réinitialise 24 h après la première utilisation). "
                    "Ajoutez HF_TOKEN dans .env pour avoir 5 min/jour au lieu de 2. Détail : " + msg[:200]
                )
            raise RuntimeError(f"Erreur du Space Hugging Face : {msg[:300]}")

        # Le résultat est (vidéo, seed) ; la vidéo peut être un chemin ou un dict {'video': chemin}
        video = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(video, dict):
            video = video.get("video") or video.get("path")
        if not video or not Path(video).exists():
            raise ValueError(f"Vidéo introuvable dans la réponse du Space : {result}")

        temp_path = f"temp_video_{int(time.time())}.mp4"
        shutil.copyfile(video, temp_path)
        self.generated_video_path = temp_path
        return temp_path

    # --- Son : audio fourni (ffmpeg) ou généré (Space MMAudio) -----------------
    HF_DEFAULT_AUDIO_SPACE = "hkchengrex/MMAudio"  # vidéo -> vidéo avec son

    @staticmethod
    def _video_duration(path: str, fallback: float) -> float:
        try:
            import cv2
            cap = cv2.VideoCapture(path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            cap.release()
            if fps and frames:
                return round(frames / fps, 2)
        except Exception:
            pass
        return fallback

    @staticmethod
    def _mux_audio(video_path: str, audio_path: str, out_path: str, duration: float):
        """Ajoute une piste audio à la vidéo avec ffmpeg (audio coupé/complété par du silence à la durée de la vidéo)"""
        import subprocess
        import imageio_ffmpeg
        cmd = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y",
            "-i", video_path, "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-af", f"apad=whole_dur={duration}", "-t", str(duration), out_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            raise RuntimeError(f"ffmpeg a échoué : {res.stderr[-300:]}")

    def _generate_audio_for_video(self, video_path: str, audio_prompt: str, progress_callback=None) -> str:
        """Génère le son avec le Space MMAudio (vidéo -> vidéo avec son) et renvoie le chemin du MP4 final"""
        import os
        import shutil
        from gradio_client import Client, handle_file

        token = os.getenv("HF_TOKEN") or None
        space = os.getenv("HF_AUDIO_SPACE", self.HF_DEFAULT_AUDIO_SPACE)
        duration = self._video_duration(video_path, float(self.config.duration))

        negative = os.getenv("HF_AUDIO_NEGATIVE")
        if negative is None:
            negative = "" if "music" in audio_prompt.lower() else "music"

        try:
            client = Client(space, token=token) if token else Client(space)
        except TypeError:
            client = Client(space, hf_token=token)

        values = {
            "video": handle_file(video_path),
            "prompt": audio_prompt,
            "negative_prompt": negative,
            "seed": -1,
            "num_steps": 25,
            "cfg_strength": 4.5,
            "duration": duration,
        }
        api_name, accepted = None, set()
        try:
            endpoints = client.view_api(return_format="dict", print_info=False)["named_endpoints"]
            api_name = next((n for n in endpoints if "video_to_audio" in n), None) or next(
                (n for n, e in endpoints.items()
                 if any(p.get("parameter_name") == "video" or "video" in str(p.get("type", "")).lower()
                        for p in e["parameters"])), None)
            if api_name:
                accepted = {p.get("parameter_name") for p in endpoints[api_name]["parameters"]}
        except Exception:
            pass

        if progress_callback:
            progress_callback(f"Génération du son avec {space} : « {audio_prompt[:80]} »...\n")

        if api_name and "video" in accepted:
            result = client.submit(api_name=api_name, **{k: v for k, v in values.items() if k in accepted}).result(timeout=900)
        else:  # noms de paramètres inconnus : appel positionnel dans l'ordre du Space
            result = client.submit(*values.values(), api_name=api_name or "/video_to_audio").result(timeout=900)

        out = result[0] if isinstance(result, (list, tuple)) else result
        if isinstance(out, dict):
            out = out.get("video") or out.get("path")
        if not out or not Path(out).exists():
            raise ValueError(f"Réponse audio inattendue : {result}")
        final_path = f"temp_video_audio_{int(time.time())}.mp4"
        shutil.copyfile(out, final_path)
        return final_path

    # --- Vidéos longues : plusieurs segments enchaînés (image→vidéo depuis la dernière image) ---
    @staticmethod
    def _ffmpeg():
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()

    def _extract_last_frame(self, video_path: str) -> str:
        """Extrait la dernière image d'une vidéo (PNG) pour lancer le segment suivant"""
        import subprocess
        out = f"{video_path}.last.png"
        res = subprocess.run(
            [self._ffmpeg(), "-y", "-sseof", "-0.2", "-i", video_path, "-frames:v", "1", "-update", "1", out],
            capture_output=True, text=True, timeout=60)
        if res.returncode != 0 or not Path(out).exists():
            raise RuntimeError(f"Extraction de la dernière image impossible : {res.stderr[-200:]}")
        return out

    def _concat_videos(self, paths, out_path: str):
        """Concatène des MP4 (avec ou sans son) en un seul fichier"""
        import subprocess
        list_file = f"{out_path}.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in paths:
                f.write(f"file '{Path(p).resolve().as_posix()}'\n")
        res = subprocess.run(
            [self._ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", list_file,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out_path],
            capture_output=True, text=True, timeout=300)
        try:
            Path(list_file).unlink()
        except OSError:
            pass
        if res.returncode != 0:
            raise RuntimeError(f"Concaténation ffmpeg échouée : {res.stderr[-300:]}")

    def generate_video(self, prompt: str, progress_callback=None):
        """Génère la vidéo (en plusieurs segments si > 8 s) puis lui ajoute du son. Renvoie le MP4 final."""
        import math
        import os

        def say(msg):
            if progress_callback:
                progress_callback(msg)

        video_prompt, audio_prompt = self.parse_prompt(prompt)
        if not audio_prompt:  # pas de ligne AUDIO: -> on déduit un prompt sonore de la scène
            audio_prompt = f"Realistic ambient sound and sound effects matching this scene: {video_prompt[:300]}"

        total = float(min(max(self.config.duration, 1), self.MAX_TOTAL_DURATION))
        n_seg = max(1, math.ceil(total / self.HF_MAX_DURATION))
        seg_len = round(total / n_seg, 2)
        if n_seg > 1:
            say(f"Vidéo de {total:.0f}s : {n_seg} segments de {seg_len}s enchaînés "
                f"(≈ {n_seg} × 1 min de quota GPU).\n")

        # 1) Segments vidéo (le 2e démarre sur la dernière image du 1er, etc.)
        segments, temp_files = [], []
        image = self.image.path if self.image.exists else None
        for i in range(n_seg):
            if n_seg > 1:
                say(f"--- Segment {i + 1}/{n_seg} ---\n")
            seg_prompt = video_prompt if i == 0 else f"{video_prompt} Continue the same shot seamlessly, same subject and setting."
            path = self._generate_silent_video(seg_prompt, progress_callback, duration=seg_len, image_path=image)
            segments.append(path)
            if i < n_seg - 1:
                image = self._extract_last_frame(path)
                temp_files.append(image)

        if n_seg > 1:
            silent_path = f"temp_video_{int(time.time())}_full.mp4"
            self._concat_videos(segments, silent_path)
            temp_files.append(silent_path)
        else:
            silent_path = segments[0]

        # 2) Son : audio fourni > audio généré par IA > aucun
        final_path = silent_path
        try:
            if self.audio.exists:
                say(f"Ajout de la piste audio fournie ({self.audio.name})...\n")
                final_path = f"temp_video_audio_{int(time.time())}.mp4"
                video_len = self._video_duration(silent_path, total)
                self._mux_audio(silent_path, self.audio.path, final_path, video_len)
            elif os.getenv("HF_AUDIO", "1") != "0":
                if n_seg == 1:
                    final_path = self._generate_audio_for_video(silent_path, audio_prompt, progress_callback)
                else:  # MMAudio est entraîné sur ~8 s : on génère le son segment par segment
                    with_audio = []
                    for i, seg in enumerate(segments):
                        say(f"Son du segment {i + 1}/{n_seg}...\n")
                        with_audio.append(self._generate_audio_for_video(seg, audio_prompt, progress_callback))
                    final_path = f"temp_video_audio_{int(time.time())}_full.mp4"
                    self._concat_videos(with_audio, final_path)
                    temp_files.extend(with_audio)
            else:
                say("Son désactivé (HF_AUDIO=0) : vidéo sans son.\n")
        except Exception as e:
            final_path = silent_path
            say(f"⚠️ Impossible d'ajouter le son ({str(e)[:200]}). La vidéo est conservée sans son.\n")

        # 3) Nettoyage des fichiers intermédiaires
        for f in segments + temp_files:
            if f != final_path:
                try:
                    Path(f).unlink()
                except OSError:
                    pass
        self.generated_video_path = final_path
        return final_path

    def clear_all(self):
        """Réinitialise toutes les données"""
        self.image = MediaFile(file_type="image")
        self.audio = MediaFile(file_type="audio")
        self.video = MediaFile(file_type="video")
        
        # Supprimer le fichier temporaire
        if self.generated_video_path and Path(self.generated_video_path).exists():
            try:
                Path(self.generated_video_path).unlink()
            except:
                pass
        
        self.generated_video_path = None
        self.analysis_result = ""