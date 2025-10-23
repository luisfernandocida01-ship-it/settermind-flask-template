import os
from apify_client import ApifyClient

APIFY_TOKEN = os.environ.get('APIFY_TOKEN')
client = ApifyClient(APIFY_TOKEN)

print("--- INICIANDO PRUEBA DIRECTA DE APIFY ---")

try:
    post_scraper = client.actor("apify/instagram-post-scraper")
    print("Actor 'post-scraper' encontrado. Ejecutando...")
    
    run_input = {
        "directUrls": ["https://www.instagram.com/p/C6_s-jZPY-C/"], # Una URL pública y reciente
        "resultsLimit": 1,
    }
    
    run = post_scraper.call(run_input=run_input)
    
    print("\n--- RESULTADOS DEL DATASET ---")
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        print(item)

    print("\n--- PRUEBA COMPLETADA ---")

except Exception as e:
    print(f"\n--- ERROR EN LA PRUEBA DIRECTA: {e} ---")