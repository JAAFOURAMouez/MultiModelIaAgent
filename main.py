import tkinter as tk
from pathlib import Path
import sys

# Imports des modules de l'application
from MediaFile import MultimodalAgentModel
from MultimodalAgentView import MultimodalAgentView
from MultimodalAgentController import MultimodalAgentController


def main():
    """Point d'entrée principal de l'application"""
    try:
        # Créer la fenêtre principale Tkinter
        root = tk.Tk()
        
        # Initialiser le modèle (logique métier et données)
        model = MultimodalAgentModel()
        
        # Initialiser la vue (interface utilisateur)
        view = MultimodalAgentView(root)
        
        # Initialiser le contrôleur (gestion des événements)
        controller = MultimodalAgentController(model, view)
        
        # Centrer la fenêtre sur l'écran
        center_window(root)
        
        # Message de bienvenue dans le status bar
        view.update_status("🎬 Prêt à créer des vidéos multimodales avec IA!")
        
        # Démarrer la boucle d'événements Tkinter
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur fatale au démarrage: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def center_window(window):
    """Centre la fenêtre sur l'écran"""
    window.update_idletasks()
    
    # Dimensions de la fenêtre
    width = window.winfo_width()
    height = window.winfo_height()
    
    # Dimensions de l'écran
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculer la position pour centrer
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    # Appliquer la géométrie
    window.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == "__main__":
    # Vérifier les dépendances critiques
    try:
        import tkinter
        import PIL
        import cv2
        import agno
        import google.genai
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("\n📦 Installez les dépendances requises:")
        print("pip install pillow opencv-python agno google-genai")
        sys.exit(1)
    
    # Vérifier la variable d'environnement pour l'API
    import os
    if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
        print("⚠️  AVERTISSEMENT: Aucune clé API trouvée!")
        print("Définissez GOOGLE_API_KEY ou GEMINI_API_KEY dans vos variables d'environnement")
        print("Exemple: export GOOGLE_API_KEY='votre_cle_ici'")
        print("\nL'application va démarrer mais la génération vidéo échouera sans clé API.\n")
    
    # Lancer l'application
    main()