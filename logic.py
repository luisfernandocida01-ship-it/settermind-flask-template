# logic.py
import os
import time
from apify_client import ApifyClient
from selenium import webdriver
from selenium.webdriver.common.by import By
import google.generativeai as genai

APIFY_TOKEN = os.environ.get('APIFY_TOKEN_PLANTILLA')
apify_client = ApifyClient(APIFY_TOKEN)

def scrape_instagram_comments(url: str):
    print("Iniciando scraping de comentarios...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage")
    comments = []
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url); time.sleep(8)
        elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'x78zum5')]//div[contains(@class, 'x1cy8zhl')]//span")
        comments = [el.text for el in elements if el.text]
    except Exception as e: print(f"Error en scraping: {e}")
    finally:
        if driver: driver.quit()
    print("Scraping finalizado.")
    return comments

def analyze_profile_with_ai(biography: str, model):
    """
    Usa Gemini para analizar la biografía de un perfil de Instagram y deducir su nicho y avatar.
    """
    if not biography or not biography.strip():
        print("Biografía vacía, saltando análisis de perfil.")
        return {"niche": "No se pudo determinar (sin biografía).", "avatar": "No se pudo determinar (sin biografía)."}

    print("Iniciando análisis de perfil con Gemini...")
    
    prompt = f"""
        **IDENTIDAD:** Eres 'BrandStrategist AI', un experto en branding y marketing digital. Tu especialidad es analizar perfiles de redes sociales para entender su posicionamiento de mercado.

        **TAREA:** Analiza la siguiente BIOGRAFÍA de un perfil de Instagram. Basándote en el texto, deduce el nicho principal del perfil y describe a su cliente ideal (avatar).

        **BIOGRAFÍA PARA ANALIZAR:**
        "{biography}"

        **FORMATO DE SALIDA (Obligatorio - JSON):**
        Devuelve un objeto JSON con dos claves: "niche" y "avatar".
        - "niche": Una frase corta que resuma el nicho del perfil.
        - "avatar": Una descripción breve del tipo de persona a la que este perfil le está hablando.
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        print("Análisis de perfil completado.")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error con API de Gemini al analizar perfil: {e}")
        return {"niche": "Error en el análisis.", "avatar": "Error en el análisis."}

def analyze_comments_with_ai(comments: list, context: dict, model):
    print("Iniciando análisis de CONGRUENCIA con Gemini...")
    comments_text_block = "\n".join(f"- {c}" for c in comments)
    
    # --- ¡PROMPT MEJORADO CON CONGRUENCIA! ---
    prompt = f"""
        **IDENTIDAD:** Eres 'SetterMind AI', un experto en análisis de prospectos y congruencia de mercado.

        **TAREA PRINCIPAL:**
        Te proporcionaré el CONTEXTO DE UN PRODUCTO (lo que quiero vender) y el CONTEXTO DE UN POST (donde encontré a los prospectos). Tu misión es analizar una lista de COMENTARIOS de ese post y, para cada uno, determinar si es un buen prospecto para el producto.

        **CONTEXTO DEL PRODUCTO (Lo que yo vendo):**
        *   **Nicho/Producto:** {context.get('niche', 'No especificado')}
        *   **Cliente Ideal (Avatar):** {context.get('avatar', 'No especificado')}

        **CONTEXTO DEL POST (Donde están los comentarios):**
        *   **Descripción del Post (Caption):** {context.get('caption', 'No especificada')}

        **COMENTARIOS PARA ANALIZAR:**
        {comments_text_block}
        
        **INSTRUCCIONES DE ANÁLISIS:**
        1.  **FILTRA:** Ignora comentarios inútiles (spam, emojis solos, texto de la interfaz).
        2.  **IDENTIFICA:** Selecciona un máximo de 5-7 comentarios que sean prospectos REALES.
        3.  **ANALIZA CADA PROSPECTO:** Para cada uno, proporciona la siguiente información:
            *   **comment_text:** El texto original.
            *   **pain_point_identified:** Describe el dolor o necesidad del prospecto. **Considera si su dolor es congruente con la solución que ofrece MI PRODUCTO.**
            *   **potential_score:** Una puntuación de 1 a 10, donde 10 es un prospecto perfecto y altamente congruente.
            *   **suggested_openers:** Genera 3 openers que conecten su dolor con la solución de MI PRODUCTO.

        **FORMATO DE SALIDA (JSON Obligatorio):**
        {{ "leads": [ ... ] }}
    """
    try:
        response = model.generate_content(prompt)
        print("Análisis de congruencia completado.")
        return response.text.strip().replace('```json', '').replace('```', '')
    except Exception as e:
        print(f"Error con API de Gemini: {e}"); return None

def find_instagram_posts_by_hashtag(hashtag: str):
    cleaned_hashtag = hashtag.strip().replace("#", "")
    print(f"Iniciando BÚSQUEDA SIMPLE para #{cleaned_hashtag} con Apify...")
    try:
        run_input = { "hashtags": [cleaned_hashtag], "resultsLimit": 3 } 
        actor_run = apify_client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        posts_data = []
        for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items():
            if item.get('url'):
                posts_data.append({
                    "url": item.get('url'), "caption": item.get('caption', 'Sin descripción.'),
                    "likesCount": 0, "commentsCount": 0, "ownerUsername": "N/A", "ownerProfilePicUrl": None
                })
        return posts_data
    except Exception as e:
        print(f"Error en prospección simple: {e}"); return None
    
# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

def generate_prospecting_strategy(context: dict, model):
    """
    Usa la IA de Gemini para generar palabras clave y hashtags a partir de un contexto de negocio.
    """
    print("Iniciando generación de estrategia de prospección con Gemini...")
    
    # Usamos el Meta-Prompt que diseñamos para esta tarea específica.
    prompt = f"""
        **IDENTIDAD:** Eres 'StrategyMind AI', un estratega de marketing de contenidos experto en encontrar comunidades online. Tu especialidad es traducir un concepto de negocio en términos de búsqueda accionables para redes sociales.

        **CONTEXTO DEL NEGOCIO:**
        *   **Producto/Solución:** {context.get('niche', 'N/A')}
        *   **Cliente Ideal (Avatar):** {context.get('avatar', 'N/A')}

        **TAREA PRINCIPAL:**
        Basado en el contexto del negocio, genera una estrategia de prospección para encontrar publicaciones relevantes. La salida debe ser un objeto JSON con dos claves: "keywords" y "hashtags".

        1.  **Genera 8 Palabras Clave de Búsqueda:** Deben ser frases que el avatar buscaría o que describirían las conversaciones donde se encuentra.
        2.  **Genera 8 Hashtags Relevantes:** Deben ser una mezcla de hashtags de nicho amplio y de subnicho específico.

        **FORMATO DE SALIDA (Obligatorio - JSON):**
        {{
          "keywords": ["frase clave 1", "frase clave 2", ...],
          "hashtags": ["hashtag1", "hashtag2", ...]
        }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiamos la respuesta para asegurarnos de que es un JSON válido
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        print("Generación de estrategia completada.")
        return cleaned_response
    except Exception as e:
        print(f"Error con API de Gemini al generar estrategia: {e}")
        return None
    
def get_post_details(url: str, gemini_model): # Ahora le pasamos el modelo de Gemini
    """
    Usa Apify para obtener detalles del post Y LUEGO usa Gemini para analizar el perfil del autor.
    """
    print(f"Obteniendo detalles enriquecidos para la URL: {url}...")
    try:
        actor = apify_client.actor("apify/instagram-scraper")
        run_input = {"urls": [url], "resultsType": "posts", "resultsLimit": 1}
        actor_run = actor.call(run_input=run_input)
        
        for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items():
            # Primero, recolectamos los datos del post
            post_details = {
                "caption": item.get('caption', 'Sin descripción.'),
                "ownerUsername": item.get('ownerUsername', 'N/A'),
                "likesCount": item.get('likesCount', 0),
                "commentsCount": item.get('commentsCount', 0)
            }
            
            # Ahora, obtenemos la biografía del autor
            author_bio = item.get('ownerBiography', '')
            
            # ¡LA NUEVA MAGIA! Llamamos a nuestra nueva función de análisis de perfil
            profile_analysis = analyze_profile_with_ai(author_bio, gemini_model)
            
            print("Detalles y análisis de perfil obtenidos con éxito.")
            # Devolvemos un objeto que contiene AMBAS piezas de información
            return {
                "post": post_details,
                "profile": profile_analysis
            }
        
        print("No se encontraron items en el dataset de Apify.")
        return None

    except Exception as e:
        print(f"Error al obtener detalles enriquecidos: {e}")
        return None