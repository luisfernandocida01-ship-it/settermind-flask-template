import unicodedata
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
    print("Iniciando análisis de CONGRUENCIA con OpenAI (Fórmula Gancho + Dolor + CTA)...")
    comments_lines = []
    for c in comments:
        if isinstance(c, dict):
            comments_lines.append(f"[@{c.get('username', 'usuario')}]: {c.get('text', '')}")
        else:
            comments_lines.append(f"- {c}")
    comments_text_block = "\n".join(comments_lines)

    prompt = f"""
        **IDENTIDAD:** Eres SetterMind AI, estratega de prospección y cualificación comercial por mensaje directo (DM).

        **CONTEXTO DEL PRODUCTO:**
        * Nicho/Producto: {context.get('niche', 'No especificado')}
        * Cliente Ideal (Avatar): {context.get('avatar', 'No especificado')}

        **CONTEXTO DEL POST:**
        * Descripción del Post (Caption): {context.get('caption', 'No especificada')}

        **COMENTARIOS A ANALIZAR:**
        {comments_text_block}

                **INSTRUCCIONES ESTRATÉGICAS DE GENERACIÓN DE OPENERS:**
        1. Para cada prospecto, extrae el **Dolor / Necesidad comercial principal** basado en su comentario o en su intención manifestada.
        2. Determina un **potential_score** numérico de 1 a 10 (donde 10 es máxima intención de compra / afinidad).
        3. Para cada prospecto redacta 3 Openers con esta fórmula exacta:
           - **GANCHO:** Saludo personalizado llamándolo por su usuario o nombre deducible (Ej: "Hola @nombre_usuario!"), haciendo mención a lo que escribió.
           - **CONTENIDO / VALOR:** Conecta con empatía sobre el dolor o dilema que planteó en su comentario.
                      - **REGLA DE FORMATO:** NO incluyas etiquetas ni prefijos como "Opener 1:", "Opener 2:", "Paso 1:". Devuelve únicamente el texto directo listo para enviar o comentar.
           - **CTA CONECTADO A TU PRODUCTO/OFERTA:** Cierra OBLIGATORIAMENTE con una pregunta conversacional orientada al **Contexto del Producto / Solución que ofrezco** ({context.get('niche', 'mi oferta')} / {context.get('avatar', 'mi cliente ideal')}), sondeando sutilmente su apertura para explorar dicha solución.

        **FORMATO DE SALIDA (JSON Únicamente):**
        {{
          "leads": [
            {{
              "username": "usuario_sin_arroba",
              "comment_text": "texto exacto del comentario",
              "comment": "texto exacto del comentario",
              "pain_point_identified": "Dolor o necesidad comercial identificada",
              "intent": "Interés comercial detectado",
              "potential_score": 9,
              "confidence": 90,
              "suggested_openers": [
                "Hola @nombre_usuario! Saludo empático conectando con dolor y pregunta final",
                "Qué tal @nombre_usuario! Perspectiva con dolor y pregunta abierta",
                "Hola @nombre_usuario! Directo al grano sobre el dolor y pregunta abierta"
              ],
              "openers": [
                "Hola @nombre_usuario! Saludo empático conectando con dolor y pregunta final",
                "Qué tal @nombre_usuario! Perspectiva con dolor y pregunta abierta",
                "Hola @nombre_usuario! Directo al grano sobre el dolor y pregunta abierta"
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
        print("Análisis y openers generados con éxito.")
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
    Eres un estratega senior de High-Ticket Setting e Instagram Architecture.
    Tu tarea es redactar el manual de guiones completo para las 5 Historias Destacadas (Highlights) del perfil de Instagram del negocio.
    
    REGLA OBLIGATORIA:
    No resumas ninguna carpeta. Debes entregar las 5 carpetas desarrolladas HISTORIA POR HISTORIA (con su número, indicación visual exacta, texto en pantalla, guion de audio palabra por palabra y sticker interactivo). Reemplaza todos los datos genéricos por la información real del cliente.

    DATOS DEL NEGOCIO:
    - Marca / Experto: {name}
    - Misión / Transformación: {mission}
    - Método Central: {method_name}
    - Prueba / Caso de Éxito: {result_example}

    ESTRUCTURA EXACTA A GENERAR:

    ================================================================================
    HIGHLIGHT 1: EMPIEZA AQUÍ 🚀 (Filtro y Bienvenida)
    - Portada: Fondo oscuro sólido con tipografía blanca "EMPIEZA AQUÍ" y el logo o nombre.
    * HISTORIA 1 (El Gancho): Video/Selfie hablando a cámara. Texto en pantalla que mencione el dolor principal. Guion exacto de 15 seg. Sticker: flecha o mención.
    * HISTORIA 2 (Quiebre de Creencias): Imagen con texto de alto contraste rompiendo la solución tradicional errónea. Guion de reflexión. Sticker de encuesta de validación.
    * HISTORIA 3 (El Mecanismo): Video frente a pizarra o tablet presentando {method_name}. Guion explicando por qué este vehículo es predecible.
    * HISTORIA 4 (La Prueba): Captura real de métricas o chat del resultado ({result_example}). Guion validando que es replicable.
    * HISTORIA 5 (Llamado a la Acción): Video corto. Texto: "Comenta ORIGEN". Guion exacto para invitar al DM y abrir conversación.

    ================================================================================
    HIGHLIGHT 2: MÉTODO ⚙️ (Desglose del Gran Mecanismo)
    - Portada: Fondo oscuro con ícono técnico o diagrama y la palabra "MÉTODO".
    * HISTORIA 1 (Visión General): Diagrama o esquema del sistema completo {method_name}. Guion explicando por qué consta de 3 fases.
    * HISTORIA 2 (Fase 1 - Atracción/Conversión): Imagen o video mostrando cómo captar prospectos calificados orgánicamente.
    * HISTORIA 3 (Fase 2 - Cualificación): Gráfica o captura de criterios para filtrar prospectos no aptos.
    * HISTORIA 4 (Fase 3 - Cierre/Llamada): Explicación de la entrega de solución y transición a agenda de diagnóstico.
    * HISTORIA 5 (Entrega del Diagrama): Texto en pantalla: "Responde 'METODO'". Guion exacto ofreciendo enviar el diagrama en PDF/alta resolución por mensaje privado.

    ================================================================================
    HIGHLIGHT 3: RESULTADOS 📈 (Prueba Social Irrefutable)
    - Portada: Fondo oscuro con gráfica de crecimiento y la palabra "RESULTADOS".
    * HISTORIA 1 (Punto de Partida): Captura de pantalla o testimonio mostrando el punto de dolor inicial del cliente antes de {method_name}.
    * HISTORIA 2 (El Punto de Inflexión): Qué ajuste técnico se aplicó con {result_example}.
    * HISTORIA 3 (El Resultado Final): Capturas de métricas o mensajes de felicitación del cliente.
    * HISTORIA 4 (CTA de Auditoría): Video o selfie. Texto: "Comenta REVISION". Guion para evaluar si el prospecto califica para el mismo resultado.

    ================================================================================
    HIGHLIGHT 4: RECURSOS 📥 (Lead Magnets y Activos Gratuitos)
    - Portada: Fondo oscuro con ícono de documento o regalo y la palabra "RECURSOS".
    * HISTORIA 1 (El Problema Específico): Explicación de un error común que comete el avatar a diario.
    * HISTORIA 2 (El Activo de Solución): Presentación visual (mockup o captura de pantalla) de la guía, plantilla o cheatsheet gratuita disponible.
    * HISTORIA 3 (Qué incluye): Desglose en 3 puntos clave de lo que aprenderá en el recurso.
    * HISTORIA 4 (Entrega por DM): Texto: "Responde 'PLANTILLA'". Guion directo para que el Setter entregue el PDF en privado.

    ================================================================================
    HIGHLIGHT 5: AGENDAR 📅 (Filtro para Llamada de Diagnóstico)
    - Portada: Fondo oscuro con ícono de calendario y la palabra "AGENDAR".
    * HISTORIA 1 (Propósito de la Sesión): Explicación de qué es la llamada de diagnóstico de 15 minutos.
    * HISTORIA 2 (Para quién SÍ es): Requisitos claros de experiencia o facturación requerida.
    * HISTORIA 3 (Para quién NO es): Filtro estricto contra curiosos o personas que buscan atajos sin compromiso.
    * HISTORIA 4 (El Acceso): Sticker con link a Calendly / formulario y texto: "O responde AGENDA si prefieres que te ayudemos a elegir horario".
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando highlights: {e}")
        return None


def generate_content_ideas_logic(topic: str):
    prompt = f"""
    Actúa como Director Editorial y Estratega de Conversión Orgánica para Setters y Consultores High-Ticket.
    Diseña un Sistema Editorial Diario de 5 piezas de contenido altamente accionables y diferenciadas sobre el tema: '{topic}'.

    OBJETIVO:
    Generar curiosidad, autoridad y quiebre de objeciones para que los prospectos calificados comenten una palabra clave y el Setter inicie una conversación de venta consultiva en DM.

    REGLAS DE TONO Y ESTILO:
    - CERO clichés de marketing barato ("revoluciona tus ventas", "duplica tus ingresos en 30 días", etc.).
    - Tono profesional, estratégico, enfocado en criterio, sistemas y proceso humano asistido por tecnología.
    - Español neutro latinoamericano profesional.

    ESTRUCTURA EXACTA DE LAS 5 IDEAS:
    Entrega 5 ideas, cada una cubriendo un ángulo editorial distinto:
    1. Ángulo 1: Quiebre de Creencia (Desmontar una verdad asumida o error común).
    2. Ángulo 2: El Error Silencioso (La fuga oculta que quema prospectos o baja la tasa de respuesta).
    3. Ángulo 3: Micro-Caso de Transformación (El antes caótico vs el después con método estructurado).
    4. Ángulo 4: Desglose Táctico (Mini-sistema de 3 fases o pasos directos).
    5. Ángulo 5: Filtro de Calificación / Diagnóstico (Identificar si el prospecto califica para la solución).

    FORMATO POR CADA IDEA:
    ==================================================
    ## IDEA [N]: [TÍTULO IMPACTANTE] — [ÁNGULO EDITORIAL]
    - **Formato Sugerido:** [Reel Cara a Cámara (9:16) / Carrusel Técnico / B-Roll Cinematográfico]
    - **Hook en Pantalla (Texto grande primeros 3s):** "[Texto corto de alto impacto]"
    - **Hook Hablado / Entrada:** "[Frase inicial que frena el scroll sin sonar a venta]"
    - **Desarrollo (Estructura PAS: Problema, Agitación, Solución):**
      [Guion o punteo de 4 a 6 líneas con datos concretos, fricciones reales y criterio estratégico]
    - **Llamado a la Acción (CTA en DM):** "Comenta '[PALABRA_CLAVE]' y te envío [recurso/auditoría/diagrama] por mensaje directo."
    - **Disparador para el Setter (Mensaje de apertura en DM):** "[Primer mensaje consultivo que el setter envía cuando el usuario comenta la palabra]"
    ==================================================
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando ideas de contenido: {e}")
        return None
def generate_lead_magnet_logic(resource_type: str):
    prompt = f"""
    Actúa como Consultor Senior y Arquitecto de Contenidos High-Ticket.
    Tu objetivo es redactar el CONTENIDO COMPLETO Y DESARROLLADO de un Lead Magnet operativo sobre: '{resource_type}'.

    REGLAS DE DESARROLLO (CERO RESÚMENES NI ÍNDICES VACÍOS):
    - No te limites a enumerar pasos: redacta las explicaciones técnicas, ejemplos concretos y pasos de acción de cada sección.
    - El documento debe ser un activo listo para que el usuario lo copie, maquete en Canva/Notion/PDF y lo entregue a sus prospectos con valor inmediato.
    - Tono profesional, práctico y consultivo en español neutro.

    ESTRUCTURA COMPLETA DEL ENTREGABLE:
    ==================================================
    # DOCUMENTO MAESTRO: [TÍTULO IMPACTANTE DEL RECURSO]
    - **Formato:** Guía Táctica / Workbook / SOP de Implementación
    - **Promesa Central:** [Resultado específico medible]
    - **Palabra Clave (CTA para DM):** [Ej: 'SISTEMA', 'GUIA', 'PASOAPASO']

    ---
    ## INTRODUCCIÓN Y DIAGNÓSTICO
    [Texto introductorio de 2 párrafos exponiendo el quiebre de creencia del sector y la metodología que soluciona el problema]

    ## DESARROLLO ÍNTEGRO DEL RECURSO (PASO A PASO EXHAUSTIVO)
    [Desarrolla detalladamente de 5 a 7 pasos o fases. Para CADA PASO incluye:
     1. Objetivo Táctico.
     2. Qué hacer paso a paso (instrucción procedimental real).
     3. Herramientas o prompts recomendados.
     4. Ejemplo de aplicación práctica o caso concreto.]

    ## CONCLUSIÓN Y SIGUIENTE PASO ESTRATÉGICO
    [Cierre del documento con llamado a la acción para agendar una sesión de auditoría o diagnóstico 1 a 1 para implementar el sistema]

    ---
    ## SECUENCIA DE CONVERSIÓN PARA EL SETTER (CHAT DM)
    - **Mensaje 1 (Entrega inmediata del link):**
      "¡Hola [Nombre]! Aquí tienes el acceso a [Nombre del Recurso]: [Enlace]. Te recomiendo revisar directo el paso [X] que es donde la mayoría se traba."
    - **Mensaje 2 (Calificación / Seguimiento a las 24h):**
      "[Pregunta de diagnóstico sobre la fase más crítica del documento]"
    - **Mensaje 3 (Transición a Llamada de Diagnóstico):**
      "[Propuesta consultiva para revisar sus números en una sesión de 15 min]"
    ==================================================
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando lead magnet: {e}")
        return None
def generate_engagement_poll_logic(question: str):
    prompt = f"""
    Actúa como Estratega de Engagement y Conversión en Historias de Instagram para Setters y Consultores High-Ticket.
    Diseña una SECUENCIA COMPLETA DE INTERACCIÓN Y PROSPECCIÓN (5 Historias Consecutivas) basada en la temática o pregunta central: '{question}'.

    OBJETIVO:
    Transformar votantes pasivos de stickers en conversaciones cualificadas en DM para el Setter.

    REGLAS DE DISEÑO:
    - Diseñado para formato vertical 9:16 de Historias de Instagram.
    - Cada historia DEBE usar un sticker nativo interactivo diferente.
    - CERO preguntas genéricas aburridas; enfócate en fricciones reales del mercado.

    FORMATO OBLIGATORIO DE SALIDA:
    ==================================================
    # SECUENCIA DE ENGAGEMENT: [TÍTULO DE LA DINÁMICA]
    - **Tema Central:** {question}
    - **Objetivo del Embudo:** [Qué cualifica el Setter con esta secuencia]

    ---
    ## HISTORIA 1: LA ENCUESTA POLARIZANTE (FILTRO DE DOLOR)
    - **Visual:** Foto o video casual / fondo oscuro limpio (#0F172A).
    - **Texto en Pantalla:** "[Pregunta directa al grano que despierte curiosidad]"
    - **Sticker Interactivo:** Encuesta Binaria (Poll Sticker).
      - Opción A: "[Respuesta dolor/fricción]"
      - Opción B: "[Respuesta ideal/aspiracional]"
    - **Guion del Setter (Apertura por DM a quienes votaron):**
      - Si votó Opción A: "[Mensaje de apertura consultivo]"
      - Si votó Opción B: "[Pregunta de validación]"

    ## HISTORIA 2: EL SLIDER DE TERMÓMETRO (INTENSIDAD DEL PROBLEMA)
    - **Visual:** Captura de métrica, pantalla o foto de trabajo.
    - **Texto en Pantalla:** "[Contexto breve explicando por qué este problema frena los resultados]"
    - **Sticker Interactivo:** Emoji Slider (Calibrador de 0 a 100%).
      - Pregunta: "[¿Qué tanto te está pasando esto hoy?]"
    - **Guion del Setter (Apertura por DM según intensidad):**
      "[Mensaje directo rompiendo el hielo empáticamente]"

    ## HISTORIA 3: EL CUESTIONARIO DE DIAGNÓSTICO (QUIZ MULTI-OPCIÓN)
    - **Visual:** Gráfico simple, carátula o video breve explicativo.
    - **Texto en Pantalla:** "[Identifica qué tipo de obstáculo tienes]"
    - **Sticker Interactivo:** Quiz (3 opciones).
      - Opción 1: "[Falta de proceso/método]"
      - Opción 2: "[Falta de tiempo/herramientas]"
      - Opción 3: "[Incertidumbre de por dónde empezar]"
    - **Guion del Setter (Para abordar según la opción elegida):**
      "[Respuesta personalizada a la opción ganadora del usuario]"

    ## HISTORIA 4: LA CAJA DE DESAHOGO (QUESTION BOX)
    - **Visual:** Foto frente a cámara con espacio superior despejado.
    - **Texto en Pantalla:** "[Invita a que escriban su duda específica]"
    - **Sticker Interactivo:** Caja de Preguntas (Question Box).
      - Placeholder del Sticker: "[Cuéntame tu mayor duda con X...]"
    - **Acción del Setter:** [Cómo responder públicamente y llevarlo al privado]

    ## HISTORIA 5: EL PUENTE DE CONVERSIÓN (LLAMADO A LA ACCIÓN FINAL)
    - **Visual:** Reel corto o carátula de alto contraste.
    - **Texto en Pantalla:** "[Ofrecimiento del activo/solución para resolver lo votado en las historias anteriores]"
    - **Sticker Interactivo:** Sticker de Mensaje Directo o Reacción Rápida.
    - **Llamado a la Acción (CTA):** "Toca aquí o responde con la palabra '[CLAVE]' y te envío el diagnóstico / recurso."
    ==================================================
    """
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando dinamica de engagement: {e}")
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


def generate_multimedia_prompts_logic(highlight_title: str, script_content: str):
    is_resource = "Arsenal" in highlight_title or "Lead Magnet" in highlight_title or "Recurso" in highlight_title
    is_engagement = "Engagement" in highlight_title or "Encuestas" in highlight_title or "Laboratorio" in highlight_title

    if is_resource:
        prompt = f"""
        Eres un Director de Arte de Producto Digital y Mockups 3D experto en Midjourney v6.1 y Canva.
        Genera la SUITE DE PROMPTS MULTIMEDIA PARA PROMOCIONAR Y VENDER ESTE RECURSO.
        DOCUMENTO BASE:
        {script_content}
        (Generar Mockup 3D principal, Bundle Digital promocional y Ficha técnica de maquetación en Canva).
        """
    elif is_engagement:
        prompt = f"""
        Eres un Director de Arte y Creador de Contenido Vertical experto en Google Veo 3.1, Runway Gen-3 y Canva para Instagram Stories.
        Transforma esta SECUENCIA DE ENGAGEMENT en PROMPTS TÉCNICOS DE PRODUCCIÓN 1 A 1 para cada una de las 5 Historias.

        SECUENCIA DE ENTRADA:
        {script_content}

        REGLAS TÉCNICAS:
        1. Para historias en video (Veo 3.1 / Runway):
           - Aspecto 9:16 vertical, lente 35mm f/1.8, sujeto hablando a cámara o encuadre de trabajo.
           - ZONA SEGURA: Especificar encuadre medio/cerrado con tercio superior despejado y centro libre para albergar el sticker interactivo de Instagram.
           - Diálogo Íntegro: En español neutro sincronizado ('saying: "[texto]"').
        2. Para historias gráficas (Canva):
           - Especificar paleta oscura (#0F172A), tipografía legible grande y área delimitada para el sticker de encuesta/cuestionario.

        FORMATO POR CADA HISTORIA:
        ==================================================
        ## HISTORIA X: [TÍTULO Y TIPO DE STICKER]
        - **Formato:** Video Veo 3.1 (9:16) / Gráfico Canva (9:16)
        - **Prompt Técnico de Producción (Inglés cinematográfico):**
          "[Prompt en inglés con diálogo o textos entre comillas en español neutro]"
        - **Directiva de Montaje en Instagram / Canva:**
          - Tipo de Sticker: [Encuesta / Slider / Quiz / Caja de Preguntas]
          - Posición recomendada: [Centro / Tercio Inferior / Lateral]
        ==================================================
        """
    else:
        prompt = f"""
        Eres un Director de Arte y Prompt Engineer para Google Veo 3.1, Runway Gen-3, Midjourney v6.1 y Canva.
        Transforma el siguiente guion en prompts técnicos de producción 1 a 1.
        ORIGEN: {highlight_title}
        GUION:
        {script_content}
        """

    try:
        return generate_ai_text(prompt)
    except Exception as e:
        print(f"Error generando prompts multimedia: {e}")
        return None