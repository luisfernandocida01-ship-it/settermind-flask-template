import os
from apify_client import ApifyClient

APIFY_TOKEN = os.environ.get('APIFY_TOKEN_PLANTILLA') or os.environ.get('APIFY_TOKEN')
client = ApifyClient(APIFY_TOKEN)

print("--- INICIANDO PRUEBA DIRECTA DE APIFY ---")

try:
    actor = client.actor("apify/instagram-scraper")
    print("Actor 'instagram-scraper' encontrado. Ejecutando...")

    run_input = {
        "directUrls": ["https://www.instagram.com/p/DcjRQUKxLPV/"],
        "resultsType": "posts",
        "resultsLimit": 1,
    }

    run = actor.call(run_input=run_input)

    print("\n--- RESULTADOS DEL DATASET ---")
    dataset_id = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId") or run.get("default_dataset_id")
    dataset_items = list(client.dataset(dataset_id).iterate_items())
    print(f"Total de registros obtenidos: {len(dataset_items)}")

    for item in dataset_items:
        print("Owner:", item.get("ownerUsername"))
        print("Likes:", item.get("likesCount"))
        print("Comments Count:", item.get("commentsCount"))
        caption = item.get("caption") or ""
        print("Caption:", caption[:120], "...")

    print("\n--- PRUEBA COMPLETADA CON ÉXITO ---")

except Exception as e:
    print(f"\n--- ERROR EN LA PRUEBA DIRECTA: {e} ---")