from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import time

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
        
        # Initialisation de l'agent
        from agno.agent import Agent
        from agno.models.google import Gemini
        from agno.tools.duckduckgo import DuckDuckGoTools
        import google.genai as genai
        
        self.agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp"),
            tools=[DuckDuckGoTools()],
            markdown=True
        )
        self.client = genai.Client()
    
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
        """Génère un prompt basé sur la configuration"""
        selected = self.config.selected_analyses
        style = self.config.style
        duration = self.config.duration
        
        return f"""Crée une vidéo de {duration} seconde(s) avec le style visuel "{style}". 
Analyse les éléments suivants : {', '.join(selected)}.
Assure-toi que le modèle a bien compris les données d'entrée et crée un script narratif cohérent entre les médias.
"""
    
    def prepare_media_for_analysis(self) -> Dict[str, List]:
        """Prépare les fichiers média pour l'analyse"""
        from agno.media import Image, Audio, Video
        
        images, audios, videos = [], [], []
        
        if self.image.exists:
            with open(self.image.path, 'rb') as f:
                img_format = Path(self.image.path).suffix[1:]
                images.append(Image(content=f.read(), format=img_format))
        
        if self.audio.exists:
            with open(self.audio.path, 'rb') as f:
                audio_format = Path(self.audio.path).suffix[1:]
                audios.append(Audio(content=f.read(), format=audio_format))
        
        if self.video.exists:
            with open(self.video.path, 'rb') as f:
                video_format = Path(self.video.path).suffix[1:]
                videos.append(Video(content=f.read(), format=video_format))
        
        params = {}
        if images: params['images'] = images
        if audios: params['audio'] = audios
        if videos: params['videos'] = videos
        
        return params
    
    def run_analysis(self, query: str, callback=None):
        """Exécute l'analyse avec l'agent"""
        params = self.prepare_media_for_analysis()
        params['stream'] = True
        
        response_generator = self.agent.run(query, **params)
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
    
    def generate_video(self, prompt: str, progress_callback=None):
        """Génère une vidéo avec Veo"""
        import os
        import requests
        
        duration_sec = self.config.duration
        style = self.config.style
        
        final_veo_prompt = f"Créer une vidéo de {duration_sec} secondes au style {style}, basée sur: {prompt}"
        
        # Récupérer la clé API
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Clé API (GOOGLE_API_KEY ou GEMINI_API_KEY) non trouvée")
        
        if progress_callback:
            progress_callback("Envoi de la requête à Veo 3.0...")
        
        # Générer la vidéo
        response = self.client.models.generate_videos(
            model="veo-3.0-generate-001",
            prompt=final_veo_prompt
        )
        
        operation_name = getattr(response, 'name', None) or (
            response.get('name') if isinstance(response, dict) else None
        )
        
        if not operation_name:
            raise ValueError("Impossible de récupérer l'ID de l'opération")
        
        if progress_callback:
            progress_callback(f"Opération démarrée: {operation_name}")
        
        # Attendre la fin de la génération
        max_attempts = 60
        attempt = 0
        operation_result = None
        
        while attempt < max_attempts:
            time.sleep(10)
            attempt += 1
            
            op_url = f"https://generativelanguage.googleapis.com/v1alpha/{operation_name}"
            op_response = requests.get(op_url, params={'key': api_key}, timeout=10)
            
            if op_response.status_code == 403:
                raise PermissionError("Erreur 403: API Generative Language non activée")
            
            if op_response.status_code != 200:
                continue
            
            operation_result = op_response.json()
            
            is_done = operation_result.get('done', False)
            if not is_done and 'metadata' in operation_result:
                state = operation_result['metadata'].get('state', '')
                is_done = state in ['SUCCEEDED', 'FAILED', 'COMPLETED']
            
            if is_done:
                break
            
            if attempt % 3 == 0 and progress_callback:
                progress_callback(".")
        
        if attempt >= max_attempts:
            raise TimeoutError(f"Timeout atteint. ID: {operation_name}")
        
        # Vérifier les erreurs
        if isinstance(operation_result, dict) and 'error' in operation_result:
            error_msg = operation_result['error'].get('message', str(operation_result['error']))
            raise Exception(error_msg)
        
        # Extraire l'URI de la vidéo
        video_uri = None
        if isinstance(operation_result, dict) and 'response' in operation_result:
            response_data = operation_result['response']
            if 'generateVideoResponse' in response_data:
                video_response = response_data['generateVideoResponse']
                if 'generatedSamples' in video_response and video_response['generatedSamples']:
                    video_data = video_response['generatedSamples'][0]
                    if 'video' in video_data and 'uri' in video_data['video']:
                        video_uri = video_data['video']['uri']
        
        if not video_uri:
            raise ValueError("Impossible de trouver l'URI de la vidéo")
        
        # Télécharger la vidéo
        if progress_callback:
            progress_callback(f"Téléchargement depuis: {video_uri}")
        
        temp_path = f"temp_video_{int(time.time())}.mp4"
        download_url = f"{video_uri}&key={api_key}"
        video_response = requests.get(download_url, timeout=60)
        video_response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            f.write(video_response.content)
        
        self.generated_video_path = temp_path
        return temp_path
    
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