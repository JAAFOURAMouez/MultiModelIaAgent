# 🎬 Créateur Vidéo Multimodal IA (Hugging Face LTX-Video & Groq gpt-oss)

## Introduction

Ce projet est une application de bureau interactive (GUI) développée avec **Tkinter** en Python, permettant aux utilisateurs d'exploiter l'IA générative : **gpt-oss d'OpenAI via Groq** pour écrire le script/prompt et **LTX-Video (via un Space Hugging Face)** pour la génération de vidéos.

L'application facilite la création de clips vidéo personnalisés en combinant divers médias d'entrée (images, audio, vidéos) avec un prompt textuel enrichi par l'IA, le tout dans un style visuel et une durée définis.

## 🌟 Fonctionnalités Principales

* **Chargement Multimodal :** Supporte l'importation de fichiers **Image**, **Audio** et **Vidéo**.
* **Analyse IA Intelligente :** Utilise un agent **Groq (`openai/gpt-oss-120b`, repli sur `gpt-oss-20b`)** pour générer un script/prompt détaillé. Ces modèles sont texte uniquement : l'agent reçoit les métadonnées des médias (nom, taille, résolution, durée), pas leur contenu visuel ou sonore. Décrivez le contenu dans votre prompt.
* **Génération de Prompt :** Outil pour pré-générer un prompt initial incluant le style et la durée souhaités.
* **Paramètres Vidéo :** Contrôle de la **durée** (4-24 secondes) et sélection du **style visuel** (ex. *Années 1980*, *Anime*, *Ciné Réaliste*).
* **Génération LTX-Video :** Appelle le Space gratuit `Lightricks/ltx-video-distilled` avec `gradio_client` (texte→vidéo, ou image→vidéo si une image est chargée), jusqu'à 8 s, puis enregistre le MP4. Le quota ZeroGPU d'un compte gratuit est de 5 min de GPU par jour.
* **Vidéos longues (> 8 s) :** la vidéo est générée en segments de 8 s maximum, chaque segment repartant de la dernière image du précédent (image→vidéo), puis assemblés avec ffmpeg. Chaque segment consomme ≈ 1 min de quota GPU ZeroGPU. Limite réglable avec `HF_MAX_TOTAL` (24 s par défaut).
* **Remplissage automatique du prompt :** le bouton « Générer le Prompt » analyse l'image et/ou la vidéo chargées (modèle de vision `qwen/qwen3.8-27b` sur Groq, 3 images max) et transcrit l'audio (Whisper sur Groq, y compris la piste audio d'une vidéo), puis `gpt-oss` rédige *Idée de la scène / Caméra / Sons*. Sans média, un gabarit à compléter est inséré.
* **Son dans la vidéo finale :** si un fichier audio est chargé, il est ajouté à la vidéo (ffmpeg, coupé ou complété à la durée de la vidéo). Sinon le son est généré par IA avec le Space `hkchengrex/MMAudio` à partir de la ligne `AUDIO:` du prompt. `HF_AUDIO=0` désactive le son.
* **Prompts optimisés :** l'agent écrit en anglais un prompt structuré `VIDEO:` (sujet, action, décor, caméra, lumière, style) et `AUDIO:` (bruitages et ambiance). Vous pouvez les modifier avant de générer.
* **Interface Utilisateur (GUI) :** Interface claire et conviviale construite avec `tkinter` et `ttk`.

## ⚙️ Prérequis

Pour exécuter ce projet, vous devez disposer des éléments suivants :

1.  **Python 3.8+**
2.  **Une clé API Groq** (gratuite, script/prompt) : https://console.groq.com/keys
3.  **Un token Hugging Face** (gratuit, génération vidéo) : https://huggingface.co/settings/tokens

### Configuration des clés API

Copiez `.env.example` en `.env` puis renseignez vos clés :

```env
GROQ_API_KEY=votre_cle_groq
HF_TOKEN=votre_token_huggingface
```

Le fichier `.env` est chargé automatiquement au démarrage et ignoré par Git.

## 🛠️ Installation

Suivez ces étapes pour configurer et lancer l'application :

1. **Cloner le Dépôt**

```bash
git clone https://github.com/JAAFOURAMouez/MultiModelIaAgent.git
cd votre_repo
```
2. **Créer et Activer l'Environnement Virtuel**

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows (Command Prompt)
venv\Scripts\activate.bat
```
3. **Installer les Dépendances**

```bash
pip install -r requirements.txt
```

## 🚀 Utilisation de l'Application

Une fois les prérequis satisfaits et les dépendances installées, lancez l'application :

```bash
python main.py
```

## 🧭 Workflow

### 1. Charger les Médias

Utilisez les boutons :

- 🖼️ **Image**  
- 🎵 **Audio**  
- 🎬 **Vidéo**

pour importer vos fichiers.  
Les chemins des fichiers sélectionnés sont affichés sous chaque bouton.

---

### 2. Configurer la Vidéo

- Ajustez la **durée** (entre *4 et 24 secondes*).  
- Sélectionnez le **Style Visuel** souhaité.

---

### 3. Générer le Prompt *(optionnel)*

Cliquez sur 🧩 **Générer le Prompt** pour obtenir une base textuelle incluant vos paramètres choisis.

---

### 4. Analyser *(Étape Cruciale)*

1. Entrez le **prompt** décrivant ce que l’IA doit faire  
   > Exemple : « Décrivez le contenu de l’image et créez un scénario de 5 secondes avec cet audio. »

2. Cliquez sur 🚀 **Analyser**.  
   L’agent **Groq (gpt-oss)** rédigera le script à partir de votre prompt.

3. Le **résultat de l’analyse** s’affichera dans le panneau de droite.  
   Vous pouvez modifier ce texte pour finaliser votre script de génération vidéo.

---

### 5. Générer la Vidéo

- Assurez-vous que le texte dans le panneau de résultats est le **prompt final** que vous souhaitez voir dans la vidéo.  
- Cliquez sur 🎥 **Générer la vidéo**.  
  L’application enverra le prompt final à **Veo 3.0**.  
- Le **statut de l’opération** s’affichera dans le panneau de droite.  

⏳ *Soyez patient : cela peut prendre plusieurs minutes.*

---

### 6. Sauvegarder

Une fois la génération terminée, une boîte de dialogue s’ouvrira pour **enregistrer le fichier `.mp4`**.


---

### 🔊 Remarque sur le son

Le lecteur intégré affiche l'image sans le son : ouvrez le MP4 enregistré (bouton Sauvegarder) dans un lecteur classique pour entendre l'audio. La génération du son consomme aussi du quota GPU Hugging Face (ZeroGPU).
