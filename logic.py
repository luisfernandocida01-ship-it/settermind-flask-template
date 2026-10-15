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
    Usa OpenAI para analizar el perfil/caption y deducir nicho, avatar (profesion/objetivos) y puntos de dolor.
    """
    if not biography or not biography.strip():
        return {
            "niche": "No especificado",
            "avatar": "Audiencia general interesada",
            "profesion": "Emprendedor / Usuario interesado",
            "objetivos": ["Aprender nuevas habilidades", "Optimizar procesos actuales"],
            "puntos_de_dolor": ["Falta de tiempo y herramientas automáticas", "Dificultad para convertir prospectos"]
        }

    print("Iniciando análisis enriquecido de perfil con OpenAI...")
    prompt = f"""
        **IDENTIDAD:** Eres SetterMind AI, experto en análisis de audiencias, avatares y prospección estratégica.

        **TAREA:** Analiza la siguiente información de perfil o publicación de Instagram y extrae el perfil estratégico de la audiencia.

        **TEXTO A ANALIZAR:**
        "{biography}"

        **FORMATO DE SALIDA (JSON Únicamente):**
        {{
            "niche": "Resumen claro del nicho de mercado",
            "avatar": "Perfil del cliente ideal o seguidor objetivo",
            "profesion": "Profesión o rol principal del cliente ideal",
            "objetivos": [
                "Objetivo principal que busca alcanzar",
                "Objetivo de crecimiento o aprendizaje",
                "Objetivo de reconocimiento o facturación"
            ],
            "puntos_de_dolor": [
                "Punto de dolor o frustración frecuente",
                "Obstáculo recurrente en su proceso actual",
                "Dificultad en conversión o alcance comercial"
            ]
        }}
    """
    try:
        res = generate_ai_json(prompt)
        if isinstance(res, str):
            import json
            res = json.loads(res)
        print("Análisis de perfil completado con éxito.")
        return res
    except Exception as e:
        print(f"Error analizando perfil con IA: {e}")
        return {
            "niche": "Negocios y crecimiento digital",
            "avatar": "Profesionales y emprendedores",
            "profesion": "Profesional independiente",
            "objetivos": ["Aumentar clientes y ventas", "Incorporar nuevas habilidades prácticas"],
            "puntos_de_dolor": ["Procesos comerciales lentos", "Dificultad para cerrar prospectos"]
        }

def analyze_comments_with_ai(comments: list, context: dict):
    print("Iniciando análisis de CONGRUENCIA con OpenAI...")
    comments_lines = []
    for c in comments:
        if isinstance(c, dict):
            comments_lines.append(f"[@{c.get('username', 'usuario')}]: {c.get('text', '')}")
        else:
            comments_lines.append(f"- {c}")
    comments_text_block = "\n".join(comments_lines)

    prompt = f"""
        **IDENTIDAD:** Eres SetterMind AI, estratega de prospección y cualificación comercial de alto impacto.

        **TAREA PRINCIPAL:**
        Te proporciono el CONTEXTO DEL PRODUCTO que vendo y el CONTEXTO DEL POST donde encontré a los prospectos. Analiza la lista de COMENTARIOS para identificar prospectos de alta intención y generar para cada uno 3 Openers de conversación.

        **CONTEXTO DEL PRODUCTO (Lo que yo vendo):**
        * Nicho/Producto: {context.get('niche', 'No especificado')}
        * Cliente Ideal (Avatar): {context.get('avatar', 'No especificado')}

        **CONTEXTO DEL POST (Donde están los comentarios):**
        * Descripción del Post (Caption): {context.get('caption', 'No especificada')}

        **COMENTARIOS PARA ANALIZAR:**
        {comments_text_block}

        **INSTRUCCIONES Y REGLAS DE ORO:**
        1. ATENCIÓN A LLAMADOS A LA ACCIÓN: Si el autor del post pidió comentar una palabra clave (ejemplo: 'VUELO', 'INFO', 'GUIA', 'PROMPTS', 'PRECIO' o emojis solicitados), los comentarios con esa palabra SON PROSPECTOS CALIENTES (Hot Leads) con alta intención comercial. NO LOS DESCARTES ni los consideres spam.
        2. Selecciona entre 5 y 10 prospectos con mayor potencial de respuesta.
        3. Para cada prospecto genera 3 Openers que conecten lo que comentó con la solución que ofrezco, manteniendo un tono natural, empático y profesional (sin sonar a robot ni a spam agresivo).

        **FORMATO DE SALIDA (JSON Únicamente):**
        {{
          "leads": [
            {{
              "username": "usuario_sin_arroba",
              "comment_text": "texto exacto del comentario",
              "comment": "texto exacto del comentario",
              "pain_point_identified": "Dolor o necesidad comercial identificada",
              "intent": "Interés explícito manifestado",
              "potential_score": 9,
              "confidence": 90,
              "suggested_openers": [
                "Opener 1: Saludo empático conectando con su comentario",
                "Opener 2: Pregunta estratégica sobre su desafío actual",
                "Opener 3: Enfoque directo ofreciendo la solución"
              ],
              "openers": [
                "Opener 1: Saludo empático conectando con su comentario",
                "Opener 2: Pregunta estratégica sobre su desafío actual",
                "Opener 3: Enfoque directo ofreciendo la solución"
              ]
            }}
          ]
        }}
    """
    try:
        res = generate_ai_json(prompt)
        if isinstance(res, str):
            import json
            res = json.loads(res)
        print("Análisis de congruencia y comentarios completado.")
        return res
    except Exception as e:
        print(f"Error en analyze_comments_with_ai: {e}")
        return {"leads": []}


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
        
        spanish_markers = {" el ", " la ", " y ", " que ", " para ", " con ", " por ", " tu ", " tus ", " los ", " las ", " es ", " más ", " este ", " esta ", " ventas ", " cómo "}
        portuguese_markers = {" não ", " você ", " seus ", " sua ", " suas ", " com ", " negócio ", " negócios ", " gestão ", " muito ", " também ", " foi ", " são ", " estão ", " maior ", " evento ", " história "}
        
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
            has_es = sum(1 for m in spanish_markers if m in cap_lower)
            has_pt = sum(1 for m in portuguese_markers if m in cap_lower)
            is_spanish = 1 if (has_es >= 2 and has_pt == 0) or (has_es > has_pt) else 0
            
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
            
        # Filtro estricto: solo publicaciones que tengan al menos 1 comentario
        selected_posts = [p for p in all_posts if p.get("commentsCount", 0) >= 1]

        if not selected_posts:
            print("Ninguna publicación encontrada tiene comentarios para prospectar.")
            return []

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
        prof = profile_analysis if isinstance(profile_analysis, dict) else {}
        prof = profile_analysis if isinstance(profile_analysis, dict) else {}
        return {
            "post": post_details,
            "profile": prof,
            "profile_analysis": prof,
            "caption": post_details.get("caption", ""),
            "ownerUsername": post_details.get("ownerUsername", ""),
            "likesCount": post_details.get("likesCount", 0),
            "commentsCount": post_details.get("commentsCount", 0),
            "niche": prof.get("niche", "General"),
            "avatar": prof.get("avatar", "Audiencia interesada"),
            "profesion": prof.get("profesion", ""),
            "objetivos": prof.get("objetivos", []),
            "puntos_de_dolor": prof.get("puntos_de_dolor", [])
        }

    except Exception as e:
        print(f"Error en get_post_details: {e}")
        return None