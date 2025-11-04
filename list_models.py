import google.genai as genai

# Initialise le client avec ta clé API (si elle n’est pas déjà dans tes variables d’environnement)
client = genai.Client()

print("\n--- Liste des modèles accessibles ---")

try:
    # Liste tous les modèles disponibles pour ton compte
    models = client.models.list()

    for model in models:
        print(f"- {model.name}")

    print("\n--- Vérification de modèles spécifiques ---")

    # Exemple : vérifier l'accès à Veo
    try:
        veo_model = client.models.get("veo-3.1-generate-preview")
        print(f"✅ Accès à {veo_model.name}")
    except Exception as e:
        print(f"❌ Veo inaccessible : {e}")

except Exception as e:
    print(f"Erreur lors de la récupération de la liste des modèles : {e}")
