# 🎬 Créateur Vidéo Multimodal IA (Veo 3.0 & Gemini)

## Introduction

Ce projet est une application de bureau interactive (GUI) développée avec **Tkinter** en Python, permettant aux utilisateurs d'exploiter la puissance des modèles multimodaux de Google, notamment **Gemini** pour l'analyse de contenu et **Veo 3.0** pour la génération de vidéos.

L'application facilite la création de clips vidéo personnalisés en combinant divers médias d'entrée (images, audio, vidéos) avec un prompt textuel enrichi par l'IA, le tout dans un style visuel et une durée définis.

## 🌟 Fonctionnalités Principales

* **Chargement Multimodal :** Supporte l'importation de fichiers **Image**, **Audio** et **Vidéo**.
* **Analyse IA Intelligente :** Utilise un agent **Gemini (gemini-2.0-flash-exp)** pour analyser les médias chargés et générer un script/prompt détaillé basé sur le contenu.
* **Génération de Prompt :** Outil pour pré-générer un prompt initial incluant le style et la durée souhaités.
* **Paramètres Vidéo :** Contrôle de la **durée** (4-8 secondes) et sélection du **style visuel** (ex. *Années 1980*, *Anime*, *Ciné Réaliste*).
* **Génération Veo 3.0 :** Utilise le modèle `veo-3.0-generate-001` pour créer la vidéo à partir du prompt final, gérant le polling asynchrone et le téléchargement du fichier MP4 généré.
* **Interface Utilisateur (GUI) :** Interface claire et conviviale construite avec `tkinter` et `ttk`.

## ⚙️ Prérequis

Pour exécuter ce projet, vous devez disposer des éléments suivants :

1.  **Python 3.8+**
2.  **Une Clé API Google/Gemini** (Nécessaire pour accéder à Gemini et aux services Veo 3.0).

### Configuration de la Clé API

La clé doit être définie comme une variable d'environnement nommée `GOOGLE_API_KEY` ou `GEMINI_API_KEY`.

**Exemple (Linux/macOS) :**

```bash
export GEMINI_API_KEY="VOTRE_CLÉ_API_ICI"
```

**Exemple (Windows - Command Prompt) :**

```bash
set GEMINI_API_KEY="VOTRE_CLÉ_API_ICI"
```

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
Note : La dépendance agno utilisée dans le script est supposée être une librairie interne ou un wrapper pour les appels google-genai. Si vous rencontrez des problèmes, assurez-vous que google-genai et requests sont correctement installés.

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

- Ajustez la **durée** (entre *4 et 8 secondes*).  
- Sélectionnez le **Style Visuel** souhaité.

---

### 3. Générer le Prompt *(optionnel)*

Cliquez sur 🧩 **Générer le Prompt** pour obtenir une base textuelle incluant vos paramètres choisis.

---

### 4. Analyser *(Étape Cruciale)*

1. Entrez le **prompt** décrivant ce que l’IA doit faire  
   > Exemple : « Décrivez le contenu de l’image et créez un scénario de 5 secondes avec cet audio. »

2. Cliquez sur 🚀 **Analyser**.  
   L’agent **Gemini** analysera les médias et le prompt.

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
