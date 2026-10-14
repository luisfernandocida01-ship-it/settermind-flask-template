# logic.py
import os
import json
from apify_client import ApifyClient
from openai import OpenAI

APIFY_TOKEN = os.environ.get('APIFY_TOKEN_PLANTILLA') or os.environ.get('APIFY_TOKEN')
apify_client = ApifyClient(APIFY_TOKEN)
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
_openai_client = None

def generate_ai_json(prompt: str) -> str:
    global _openai_client
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('Falta configurar OPENAI_API_KEY.')
    if _openai_client is None:
        _openai_client = OpenAI(api_key=api_key)

    response = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError('OpenAI devolvió una respuesta vacía.')
    return content

def generate_ai_text(prompt: str) -> str:
    global _openai_client
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('Falta configurar OPENAI_API_KEY.')
    if _openai_client is None:
        _openai_client = OpenAI(api_key=api_key)

    response = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError('OpenAI devolvió una respuesta vacía.')
    return content

def scrape_instagram_comments(url: str):
    print("Iniciando scraping de comentarios con Apify...")
    try:
        dataset_id = None
        actor = apify_client.actor("apify/instagram-comment-scraper")
        actor_run = actor.call(run_input={"directUrls": [url], "resultsLimit": 100})
        
        dataset_id = getattr(actor_run, "default_dataset_id", None) or actor_run.get("defaultDatasetId") or actor_run.get("default_dataset_id")
        
        comments = []
        for item in apify_client.dataset(dataset_id).iterate_items():
            text = item.get("text") or item.get("comment")
            # Apify suele devolver el autor en 'ownerUsername' o en 'user.username'
            # Búsqueda en cascada en todas las variantes de Apify
            owner_obj = item.get("owner") if isinstance(item.get("owner"), dict) else {}
            user_obj = item.get("user") if isinstance(item.get("user"), dict) else {}
            author_obj = item.get("author") if isinstance(item.get("author"), dict) else {}
            
            raw_owner = (
                item.get("ownerUsername")
                or owner_obj.get("username")
                or user_obj.get("username")
                or author_obj.get("username")
                or item.get("username")
                or item.get("authorUsername")
                or item.get("ownerFullName")
                or "prospecto_ig"
            )
            clean_username = str(raw_owner).replace("@", "").strip()
            
            if isinstance(text, str) and text.strip():
                comments.append({
                    "username": clean_username,
                    "text": text.strip()
                })
        
               
        print(f"Scraping finalizado: {len(comments)} comentarios procesados con autor.")
        return comments
    except Exception as e:
        print(f"Error al extraer comentarios con Apify: {e}")
        return []

def analyze_profile_with_ai(biography: str):
    """
    Usa OpenAI para analizar la biografía de un perfil de Instagram y deducir su nicho y avatar.
    """
    if not biography or not biography.strip():
        print("Biografía vacía, saltando análisis de perfil.")
        return {"niche": "No se pudo determinar (sin biografía).", "avatar": "No se pudo determinar (sin biografía)."}

    print("Iniciando análisis de perfil con OpenAI...")
    
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
        cleaned_response = generate_ai_json(prompt)
        print("Análisis de perfil completado.")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error con API de OpenAI al analizar perfil: {e}")
        return {"niche": "Error en el análisis.", "avatar": "Error en el análisis."}

def analyze_comments_with_ai(comments: list, context: dict):
    print("Iniciando análisis de CONGRUENCIA con OpenAI...")
    
    # Formatear el bloque preservando el autor del comentario
    comments_lines = []
    for c in comments:
        if isinstance(c, dict):
            comments_lines.append(f"[@{c.get('username', 'usuario')}]: {c.get('text', '')}")
        else:
            comments_lines.append(f"- {c}")
    comments_text_block = "\n".join(comments_lines)
    
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
            *   **username:** El usuario exacto de Instagram que hizo el comentario (sin el @).
            *   **comment_text:** El texto original del comentario.
            *   **pain_point_identified:** Describe el dolor o necesidad del prospecto. Considera si su dolor es congruente con la solución que ofrece MI PRODUCTO.
            *   **potential_score:** Una puntuación de 1 a 10, donde 10 es un prospecto perfecto y altamente congruente.
            *   **suggested_openers:** Genera 3 openers que conecten su dolor con la solución de MI PRODUCTO.

        **FORMATO DE SALIDA (JSON Obligatorio):**
        {{
          "leads": [
            {{
              "username": "usuario_real",
              "comment_text": "texto del comentario",
              "pain_point_identified": "explicación del dolor",
              "potential_score": 8,
              "suggested_openers": ["opener 1", "opener 2", "opener 3"]
            }}
          ]
        }}
    """
    try:
        response_content = generate_ai_json(prompt)
        print("Análisis de congruencia completado.")
        return response_content
    except Exception as e:
        print(f"Error en analyze_comments_with_ai: {e}")
        return None

import unicodedata

def clean_tag(text: str) -> str:
    """Elimina acentos, tildes y símbolos para maximizar compatibilidad con Instagram/Apify"""
    nfkd = unicodedata.normalize('NFKD', text)
    cleaned = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return cleaned.replace("#", "").strip().lower()

def find_instagram_posts_by_hashtag(hashtag: str):
    cleaned_hashtag = clean_tag(hashtag)
    print(f"Iniciando BÚSQUEDA de #{cleaned_hashtag} con Apify...")
    try:
        run_input = {
            "hashtags": [cleaned_hashtag],
            "resultsType": "posts",       # <-- Cambiar "top" por "posts"
            "resultsLimit": 70
        }
        actor_run = apify_client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        
        all_posts = []
        dataset_id = getattr(actor_run, "default_dataset_id", None) or actor_run.get("defaultDatasetId") or actor_run.get("default_dataset_id")
        
        spanish_markers = {" el ", " la ", " de ", " en ", " y ", " que ", " para ", " con ", " por ", " tu ", " tus ", " los ", " las "}
        
        for item in apify_client.dataset(dataset_id).iterate_items():
            url = item.get('url') or item.get('postUrl')
            if not url:
                continue
                
            owner = item.get('owner') if isinstance(item.get('owner'), dict) else {}
            owner_user = (
                item.get('ownerUsername')
                or owner.get('username')
                or item.get('username')
                or ''
            )
            
            comments_cnt = (
                item.get('commentsCount')
                or item.get('comments_count')
                or (item.get('edge_media_to_comment') or {}).get('count')
                or 0
            )
            
            likes_cnt = (
                item.get('likesCount')
                or item.get('likes_count')
                or (item.get('edge_liked_by') or {}).get('count')
                or 0
            )
            
            caption_text = item.get('caption') or item.get('text') or ''
            cap_lower = f" {caption_text.lower()} "
            is_spanish = 1 if any(m in cap_lower for m in spanish_markers) else 0
            
            all_posts.append({
                "url": url,
                "caption": caption_text or 'Sin descripción.',
                "likesCount": max(likes_cnt, 0),
                "commentsCount": max(comments_cnt, 0),
                "ownerUsername": str(owner_user).replace("@", "").strip(),
                "ownerFullName": item.get('ownerFullName') or owner.get('fullName') or '',
                "ownerProfilePicUrl": item.get('ownerProfilePicUrl') or owner.get('profilePicUrl') or '',
                "_is_spanish": is_spanish
            })
            
        # Filtro prioritario: publicaciones con comentarios reales
        with_comments = [p for p in all_posts if p["commentsCount"] >= 1]
        
        # Si hay suficientes con comentarios, usamos esas; si son pocas, completamos con las de mayor interacción
        if len(with_comments) >= 4:
            selected_posts = with_comments
        else:
            # Fallback: incluir las publicaciones con más likes del término
            selected_posts = sorted(all_posts, key=lambda p: (p["commentsCount"], p["likesCount"]), reverse=True)[:10]

        # Ordenar: primero español, luego volumen de comentarios y likes
        selected_posts.sort(key=lambda p: (p["_is_spanish"], p["commentsCount"], p["likesCount"]), reverse=True)
        
        for p in selected_posts:
            p.pop("_is_spanish", None)
            
        print(f"Total posts entregados al Radar: {len(selected_posts)}")
        return selected_posts
    except Exception as e:
        print(f"Error en find_instagram_posts_by_hashtag: {e}")
        return [] 
    
# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

# logic.py - Añadiendo el Generador de Estrategias

# ... (tus otras funciones de logic.py van aquí arriba) ...

def generate_prospecting_strategy(context: dict):
    """
    Usa OpenAI para generar palabras clave y hashtags a partir de un contexto de negocio.
    """
    print("Iniciando generación de estrategia de prospección con OpenAI...")
    
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
        cleaned_response = generate_ai_json(prompt)
        print("Generación de estrategia completada.")
        return cleaned_response
    except Exception as e:
        print(f"Error con API de OpenAI al generar estrategia: {e}")
        return None

def generate_highlights_logic(name: str, mission: str, method_name: str, result_example: str):
    prompt = f"""
    Eres un estratega experto en Instagram Branding y High-Ticket Setting.
    Diseña una estructura de Historias Destacadas (Highlights) persuasiva y profesional.
    
    DATOS DEL CLIENTE:
    - Nombre o Marca: {name}
    - Misión / Por qué: {mission}
    - Nombre del Método: {method_name}
    - Caso de éxito: {result_example}
    
    Genera un texto bien formateado con 4 Highlights indispensables:
    1. HISTORIA / ORIGEN (Quién eres y tu propósito)
    2. MÉTODO (Cómo funciona {method_name})
    3. CASOS DE ÉXITO (Prueba social con {result_example})
    4. CÓMO EMPEZAR (Llamado a la acción directo al DM)
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando highlights: {e}")
        return None


def generate_content_ideas_logic(topic: str):
    prompt = f"""
    Eres un creador de contenido viral y estratega de conversión para Setters.
    Genera 5 ideas de contenido accionables para el tema: '{topic}'.
    
    Para cada idea incluye:
    - Gancho (Hook) para los primeros 3 segundos.
    - Desarrollo del dolor o concepto central.
    - Llamado a la acción (CTA) para que comenten una palabra clave e iniciar DM.
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando ideas: {e}")
        return None


def generate_lead_magnet_logic(resource_type: str):
    prompt = f"""
    Eres un especialista en embudos orgánicos para Setters.
    Estructura un Lead Magnet irresistible del tipo: '{resource_type}'.
    
    Incluye:
    - Título gancho de alta conversión.
    - Promesa única de valor.
    - Esquema de 3 a 5 puntos clave que debe contener.
    - Mensaje sugerido para entregarlo por mensaje privado (DM).
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando lead magnet: {e}")
        return None


def generate_engagement_poll_logic(question: str):
    prompt = f"""
    Diseña una dinámica de historias de Instagram para abrir conversaciones de prospección a partir de esta pregunta/tema: '{question}'.
    
    Genera:
    - 3 Historias de contexto previo.
    - 1 Sticker de Encuesta / Pregunta con opciones estratégicas (una opción que revele dolor urgente).
    - Guion rompehielo para responder a quienes voten la opción de dolor.
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando engagement poll: {e}")
        return None


def generate_profile_magnet_logic(niche: str, transformation: str, lead_magnet: str):
    prompt = f"""
    Eres un consultor de optimización de biografías de Instagram de alta conversión.
    
    DATOS:
    - Nicho: {niche}
    - Transformación: {transformation}
    - Lead Magnet / Recurso: {lead_magnet or 'Guía Gratuita'}
    
    Genera un objeto en formato JSON con dos claves obligatorias: "bio" y "cta".
    "bio": Una biografía estructurada en 3 o 4 líneas con emojis.
    "cta": Un llamado a la acción persuasivo hacia el DM o enlace de la bio.
    
    FORMATO JSON OBLIGATORIO:
    {{
      "bio": "Texto de la biografía",
      "cta": "Texto del llamado a la acción"
    }}
    """
    try:
        return generate_ai_json(prompt)
    except Exception as e:
        print(f"Error generando perfil magnético: {e}")
        return None

def get_post_details(url: str):
    """
    Usa Apify para obtener detalles del post y OpenAI para analizar el perfil del autor.
    """
    print(f"Obteniendo detalles enriquecidos para la URL: {url}...")
    try:
        actor = apify_client.actor("apify/instagram-scraper")
        run_input = {"directUrls": [url], "resultsType": "posts", "resultsLimit": 1}
        actor_run = actor.call(run_input=run_input)
        
        dataset_id = getattr(actor_run, "default_dataset_id", None) or actor_run.get("defaultDatasetId") or actor_run.get("default_dataset_id")
        items = list(apify_client.dataset(dataset_id).iterate_items())
        
        if not items:
            print("No se encontraron items en el dataset de Apify.")
            return None

        item = items[0]
        post_details = {
            "caption": item.get('caption') or 'Sin descripción.',
            "ownerUsername": item.get('ownerUsername') or 'usuario_desconocido',
            "likesCount": item.get('likesCount', 0),
            "commentsCount": item.get('commentsCount', 0)
        }
        
        # Biografía del autor o fallback al caption para deducir el nicho
        author_bio = item.get('ownerBiography') or post_details["caption"]
        
        profile_analysis = None
        if author_bio:
            try:
                profile_analysis = analyze_profile_with_ai(author_bio)
            except Exception as err:
                print(f"Error analizando perfil con IA: {err}")
                profile_analysis = {"niche": "General", "avatar": "Audiencia interesada"}
        else:
            profile_analysis = {"niche": "General", "avatar": "Audiencia interesada"}
        
        print("Detalles y análisis de perfil obtenidos con éxito.")
        return {
            "post": post_details,
            "profile": profile_analysis,
            # Propiedades en la raíz para compatibilidad con el frontend
            "caption": post_details["caption"],
            "ownerUsername": post_details["ownerUsername"],
            "likesCount": post_details["likesCount"],
            "commentsCount": post_details["commentsCount"],
            "niche": profile_analysis.get("niche", "General") if isinstance(profile_analysis, dict) else "General",
            "avatar": profile_analysis.get("avatar", "Audiencia interesada") if isinstance(profile_analysis, dict) else "Audiencia interesada"
        }

    except Exception as e:
        print(f"Error en get_post_details: {e}")
        return None