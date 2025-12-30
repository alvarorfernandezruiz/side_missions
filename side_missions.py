
# SideMissions.py (v4.3 - Render ready)
# Mini-web para jugar a “misiones secretas” tipo party game.
# Adaptada para entorno público (Render): PORT desde entorno, 0.0.0.0, ping/health y servidor en modo multihilo.

import socket
import random
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

# --- Configuración de acceso ---
ADMIN_USERNAME = "itadmin"

# --- Estado de partida en memoria ---
GAME_STATE = {
    "active": False,
    "agents": [],         # lista de 50 agentes (minúsculas)
    "assignments": {},    # dict: agente -> [5 misiones]
    "statuses": {},       # dict: agente -> [0=pending, 1=done, 2=failed]
    "registrations": {},  # dict: agente -> nombre_jugador
}

# --- Lista de 50 agentes (sustantivos, minúsculas) ---
AGENTES_CANDIDATOS = [
    "bola", "ocho", "tigre", "peine", "gato", "perro", "mesa", "silla", "libro", "calle",
    "parque", "vaso", "plato", "techo", "suelo", "cable", "foco", "nube", "lluvia", "cubo",
    "coche", "moto", "barco", "vapor", "planta", "piedra", "cuadro", "puerta", "mapa", "clave",
    "notas", "perfil", "torre", "reloj", "metal", "papel", "cinta", "radio", "farol", "cesto",
    "casco", "guante", "caja", "filtro", "motor", "banco", "campo", "sello", "traje", "plomo",
]

# --- Lista de 250 misiones (estilo Don't Get Got) ---
MISIONES = [
    # Conversación / palabras clave (1-40)
    "Consigue que alguien diga la palabra 'vale'.",
    "Haz que alguien diga 'mañana'.",
    "Logra que alguien diga 'si' sin que se lo pidas directamente.",
    "Consigue que alguien diga 'no' en respuesta a algo tuyo.",
    "Haz que alguien mencione 'Madrid'.",
    "Logra que alguien diga 'secreto'.",
    "Consigue que alguien diga 'mision'.",
    "Haz que alguien diga 'azul'.",
    "Haz que alguien diga 'verde'.",
    "Consigue que alguien diga 'codigo'.",
    "Logra que alguien diga 'equipo'.",
    "Haz que alguien mencione 'tiempo'.",
    "Consigue que alguien diga 'problema'.",
    "Haz que alguien diga 'solucion'.",
    "Consigue que alguien diga 'idea'.",
    "Logra que alguien diga 'importante'.",
    "Haz que alguien diga 'normal'.",
    "Consigue que alguien diga 'raro'.",
    "Haz que alguien diga 'rapido'.",
    "Consigue que alguien diga 'lento'.",
    "Haz que alguien diga 'arriba'.",
    "Consigue que alguien diga 'abajo'.",
    "Logra que alguien diga 'izquierda'.",
    "Logra que alguien diga 'derecha'.",
    "Haz que alguien diga 'primero'.",
    "Haz que alguien diga 'ultimo'.",
    "Consigue que alguien diga 'siempre'.",
    "Consigue que alguien diga 'nunca'.",
    "Logra que alguien diga 'cerca'.",
    "Logra que alguien diga 'lejos'.",
    "Haz que alguien diga 'nuevo'.",
    "Haz que alguien diga 'viejo'.",
    "Consigue que alguien diga 'grande'.",
    "Consigue que alguien diga 'pequeno'.",
    "Haz que alguien diga 'perfecto'.",
    "Logra que alguien diga 'casi'.",
    "Haz que alguien diga 'listo'.",
    "Consigue que alguien diga 'espera'.",
    "Logra que alguien diga 'ahora'.",
    "Haz que alguien diga 'luego'.",
    # Pedir / prestar / objetos (41-80)
    "Consigue que alguien te preste un boligrafo.",
    "Logra que alguien te deje una hoja de papel.",
    "Pide y consigue un cargador para movil.",
    "Consigue que alguien te ofrezca una silla.",
    "Logra que alguien te alcance una chaqueta.",
    "Pide y consigue una botella de agua.",
    "Consigue que alguien te ofrezca chicle o caramelo.",
    "Logra que alguien te preste sus gafas por un momento.",
    "Pide y consigue una servilleta.",
    "Consigue que alguien te alcance la sal o azucar.",
    "Logra que alguien te ofrezca un post-it.",
    "Pide y consigue una cinta adhesiva.",
    "Consigue que alguien te deje su movil para una foto.",
    "Logra que alguien te preste un marcador o rotulador.",
    "Pide y consigue un encendedor (aunque no fumes).",
    "Consigue que alguien te ofrezca una mascarilla.",
    "Logra que alguien te preste un libro por un minuto.",
    "Pide y consigue un abridor o destapador.",
    "Consigue que alguien te alcance un vaso.",
    "Logra que alguien te preste un paraguas.",
    "Pide y consigue un clip o broche.",
    "Consigue que alguien te ofrezca un caramelito de menta.",
    "Logra que alguien te preste su reloj un segundo.",
    "Pide y consigue un cable USB.",
    "Consigue que alguien te ofrezca un pañuelo.",
    "Logra que alguien te alcance un plato.",
    "Pide y consigue un mechero (sin usarlo).",
    "Consigue que alguien te preste una gorra.",
    "Logra que alguien te ofrezca una bolsa.",
    "Pide y consigue una llave (sin usarla).",
    "Consigue que alguien te alcance el control remoto.",
    "Logra que alguien te preste un cuaderno.",
    "Pide y consigue una regla.",
    "Consigue que alguien te preste un lapiz.",
    "Logra que alguien te alcance un tenedor.",
    "Pide y consigue una cuchara.",
    "Consigue que alguien te ofrezca un juego de cartas.",
    "Logra que alguien te preste un dispensador de gel.",
    "Pide y consigue una etiqueta.",
    "Consigue que alguien te preste una bateria externa.",
    # Acciones / microeventos (81-120)
    "Haz que alguien abra una ventana.",
    "Logra que alguien cierre una puerta.",
    "Consigue que alguien encienda una luz.",
    "Haz que alguien apague una luz.",
    "Logra que alguien se levante por tu comentario.",
    "Consigue que alguien se siente por tu comentario.",
    "Haz que alguien haga un brindis.",
    "Logra que alguien aplauda.",
    "Consigue que alguien silbe.",
    "Haz que alguien cante una frase.",
    "Logra que alguien cuente hasta cinco.",
    "Consigue que alguien haga una foto.",
    "Haz que alguien mire su movil por tu frase.",
    "Logra que alguien se ponga de pie y vuelva a sentarse.",
    "Consigue que alguien se acerque a la ventana.",
    "Haz que alguien te haga una pregunta abierta.",
    "Logra que alguien te pida repetir algo.",
    "Consigue que alguien se ría por un juego de palabras.",
    "Haz que alguien te salude con la mano.",
    "Logra que alguien haga un gesto de OK.",
    "Consigue que alguien haga una seña de silencio.",
    "Haz que alguien choque la mano contigo.",
    "Logra que alguien te choque los puños.",
    "Consigue que alguien te haga una reverencia divertida.",
    "Haz que alguien mueva una silla de sitio.",
    "Logra que alguien cambie de asiento contigo.",
    "Consigue que alguien se estire como si estuviera cansado.",
    "Haz que alguien bostece (sin sugerirlo directamente).",
    "Logra que alguien haga un dibujo rapido.",
    "Consigue que alguien escriba una palabra por ti.",
    "Haz que alguien tararee una melodia.",
    "Logra que alguien haga un conteo regresivo del 3 al 1.",
    "Consigue que alguien toque la mesa con los nudillos.",
    "Haz que alguien cierre los ojos por un segundo.",
    "Logra que alguien haga una mueca graciosa.",
    "Consigue que alguien imite un sonido.",
    "Haz que alguien se ponga de espaldas un instante.",
    "Logra que alguien se quite y vuelva a poner algo (ej. gafas).",
    "Consigue que alguien se quite la gorra y la vuelva a poner.",
    "Haz que alguien te de la mano como presentacion.",
    # Mirar / señalar / orientación (121-160)
    "Consigue que alguien mire hacia arriba.",
    "Haz que alguien mire hacia abajo.",
    "Logra que alguien mire hacia la izquierda.",
    "Logra que alguien mire hacia la derecha.",
    "Consigue que alguien mire al techo.",
    "Haz que alguien mire al suelo.",
    "Logra que alguien mire por la ventana.",
    "Consigue que alguien mire un reloj.",
    "Haz que alguien mire una planta.",
    "Logra que alguien mire una pared concreta.",
    "Consigue que alguien señale una puerta.",
    "Haz que alguien señale una silla.",
    "Logra que alguien apunte con el dedo a un objeto.",
    "Consigue que alguien busque algo con la mirada.",
    "Haz que alguien mire dentro de una caja.",
    "Logra que alguien revise su bolsillo.",
    "Consigue que alguien se mire los zapatos.",
    "Haz que alguien observe un cuadro.",
    "Logra que alguien vea un mapa contigo.",
    "Consigue que alguien lea un cartel en voz alta.",
    "Haz que alguien toque su nariz.",
    "Logra que alguien toque su oreja.",
    "Consigue que alguien se toque el cabello.",
    "Haz que alguien señale una ventana concreta.",
    "Logra que alguien mire un color específico (elige en el momento).",
    "Consigue que alguien cuente objetos en la mesa.",
    "Haz que alguien intente medir algo con la mano.",
    "Logra que alguien mire debajo de la mesa.",
    "Consigue que alguien compare dos objetos.",
    "Haz que alguien busque un enchufe.",
    "Logra que alguien mire un enchufe.",
    "Consigue que alguien señale una lampara (si hay).",
    "Haz que alguien identifique un sonido raro.",
    "Logra que alguien mire el techo y sonria.",
    "Consigue que alguien haga zoom en una foto.",
    "Haz que alguien lea un nombre en voz alta.",
    "Logra que alguien se fije en un logo.",
    "Consigue que alguien cuente personas en la sala.",
    "Haz que alguien intente recordar un cartel.",
    "Logra que alguien diga el numero de una mesa cercana.",
    # Interacción / preguntas / cortesía (161-200)
    "Consigue que alguien te pregunte la hora.",
    "Haz que alguien te pregunte tu nombre.",
    "Logra que alguien te pregunte a que te dedicas.",
    "Consigue que alguien te pregunte de donde eres.",
    "Haz que alguien te pregunte si necesitas algo.",
    "Logra que alguien te pregunte si todo bien.",
    "Consigue que alguien te felicite por algo menor.",
    "Haz que alguien te de las gracias por algo pequeño.",
    "Logra que alguien se disculpe contigo sin conflicto.",
    "Consigue que alguien te recomiende una cancion.",
    "Haz que alguien te recomiende una serie.",
    "Logra que alguien te recomiende un restaurante.",
    "Consigue que alguien te recomiende una app.",
    "Haz que alguien te pida una opinion.",
    "Logra que alguien te pida consejo.",
    "Consigue que alguien te cuente un chiste.",
    "Haz que alguien te cuente una anecdota.",
    "Logra que alguien te diga un apodo.",
    "Consigue que alguien te diga 'buen trabajo'.",
    "Haz que alguien te diga 'gracias' dos veces.",
    "Logra que alguien te haga una pregunta trampa.",
    "Consigue que alguien te hable del tiempo.",
    "Haz que alguien te pregunte por la comida.",
    "Logra que alguien te pregunte por el lugar.",
    "Consigue que alguien te haga una pregunta por escrito.",
    "Haz que alguien te escriba una palabra en un papel.",
    "Logra que alguien diga que le gusta tu camisa.",
    "Consigue que alguien diga que le gusta tu reloj.",
    "Haz que alguien diga que le gustan tus zapatos.",
    "Logra que alguien te pregunte por tus planes.",
    "Consigue que alguien te pregunte por el fin de semana.",
    "Haz que alguien te pregunte por tus hobbies.",
    "Logra que alguien te pregunte por tu equipo favorito.",
    "Consigue que alguien te recomiende un libro.",
    "Haz que alguien te recomiende una pelicula.",
    "Logra que alguien te recomiende un podcast.",
    "Consigue que alguien te recomiende un lugar para viajar.",
    "Haz que alguien te pregunte por tu telefono (sin darlo).",
    "Logra que alguien te pregunte la edad de otra persona.",
    "Consigue que alguien te pregunte la fecha.",
    # Cambios / intercambios / pequeños retos (201-230)
    "Consigue cambiar de sitio con alguien sin explicacion larga.",
    "Haz que alguien use tu boligrafo y tu el suyo.",
    "Logra intercambiar tu vaso por otro (vacio).",
    "Consigue que alguien te deje su asiento un minuto.",
    "Haz que alguien lleve un objeto de un lugar a otro.",
    "Logra que alguien coloque un objeto en una esquina concreta.",
    "Consigue que alguien esconda un objeto sencillo por ti.",
    "Haz que alguien te ayude a contar objetos.",
    "Logra que alguien junte dos sillas.",
    "Consigue que alguien separe dos sillas.",
    "Haz que alguien cambie el volumen de algo (si aplica).",
    "Logra que alguien ajuste una persiana.",
    "Consigue que alguien te traiga una servilleta.",
    "Haz que alguien ordene tres cosas en fila.",
    "Logra que alguien mezcle cartas o papeles.",
    "Consigue que alguien haga un nudo simple.",
    "Haz que alguien ate un lazo improvisado.",
    "Logra que alguien doble un papel en tres.",
    "Consigue que alguien apile tres objetos.",
    "Haz que alguien dibuje un circulo y un cuadrado.",
    "Logra que alguien escriba una flecha.",
    "Consigue que alguien te alcance un objeto sin levantarse.",
    "Haz que alguien se levante para alcanzarte algo.",
    "Logra que alguien te indique un atajo.",
    "Consigue que alguien te explique una regla simple.",
    "Haz que alguien cuente una historia en 10 segundos.",
    "Logra que alguien explique algo con gestos.",
    "Consigue que alguien haga una rima corta.",
    "Haz que alguien diga una palabra inventada.",
    "Logra que alguien diga el alfabeto hasta la letra G.",
    # Miscelánea / diversión sutil (231-250)
    "Consigue que alguien diga su color favorito.",
    "Haz que alguien diga su comida favorita.",
    "Logra que alguien adivine un numero entre 1 y 5.",
    "Consigue que alguien elija entre dos opciones que proposes.",
    "Haz que alguien cante feliz cumpleaños muy breve.",
    "Logra que alguien haga una prediccion de algo trivial.",
    "Consigue que alguien haga una lista de tres cosas.",
    "Haz que alguien decida lanzando una moneda (si hay).",
    "Logra que alguien cuente un dato curioso.",
    "Consigue que alguien pregunte por la hora exacta.",
    "Haz que alguien intente traducir una palabra.",
    "Logra que alguien haga un juego de manos contigo.",
    "Consigue que alguien haga una pose divertida.",
    "Haz que alguien imite un animal (solo sonido).",
    "Logra que alguien diga 'trampa' sin contexto.",
    "Consigue que alguien diga 'bien jugado'.",
    "Haz que alguien haga una mini encuesta.",
    "Logra que alguien identifique una cancion con tarareo.",
    "Consigue que alguien diga 'no me lo creo'.",
    "Haz que alguien diga 'puede ser'.",
]

# --- Paleta y estilos base ---
def base_styles():
    return {
        "fondo": "#87CEEB",
        "verde": "#28a745",
        "verde_hover": "#218838",
        "rojo": "#dc3545",
        "negro": "#0b1e2d",
        "card_bg": "rgba(255,255,255,0.94)",
        "card_shadow": "0 10px 25px rgba(0,0,0,0.15)",
        "verde_soft": "#d8f5dc",
        "rojo_soft": "#ffd9d9",
        "verde_borde": "#9bd39f",
        "rojo_borde": "#f1a5a5",
        "azul_btn": "#1c88c9",
        "azul_btn_hover": "#177bb5",
    }

# --- Portada ---
def render_page(error: str | None = None, agente: str = "") -> str:
    s = base_styles()
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Side Missions</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{ background: {s['fondo']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {s['negro']}; display: flex; align-items: center; justify-content: center; }}
    .card {{ width: min(640px, 92vw); background: {s['card_bg']}; border-radius: 16px; box-shadow: {s['card_shadow']}; padding: 32px 28px 22px; }}
    .title {{ font-size: clamp(28px, 6vw, 48px); font-weight: 800; text-align: center; letter-spacing: 0.5px; margin: 0 0 18px 0; }}
    .subtitle {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; }}
    .row {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; }}
    input[type=text] {{ padding: 12px 14px; border: 2px solid #cfe7f6; border-radius: 10px; font-size: 16px; outline: none; transition: border-color .2s ease, box-shadow .2s ease; background: #f7fbff; }}
    input[type=text]:focus {{ border-color: #6fbdf2; box-shadow: 0 0 0 4px rgba(111,189,242,0.2); }}
    button {{ padding: 12px 20px; border: none; border-radius: 10px; background: {s['verde']}; color: white; font-weight: 700; font-size: 16px; cursor: pointer; transition: background .15s ease, transform .05s ease; }}
    button:hover {{ background: {s['verde_hover']}; }}
    button:active {{ transform: translateY(1px); }}
    .error {{ margin-top: 16px; color: {s['rojo']}; font-weight: 800; text-align: center; font-size: 15px; }}
    .actions {{ display: flex; justify-content: center; margin-top: 18px; }}
    .btn-blue {{ padding: 10px 16px; border: none; border-radius: 10px; background: {s['azul_btn']}; color: white; font-weight: 700; cursor: pointer; }}
    .btn-blue:hover {{ background: {s['azul_btn_hover']}; }}
  </style>
</head>
<body>
  <main class="card">
    <h1 class="title">Side Missions</h1>
    <form method="post" action="">
      <label class="subtitle" for="agente">Agente Secreto:</label>
      <div class="row">
        <input id="agente" name="agente" type="text" value="{agente}" placeholder="Introduce tu nombre de agente" autocomplete="off" />
        <button type="submit">OK</button>
      </div>
      {f'<div class="error">{error}</div>' if error else ''}
    </form>
    <div class="actions">
      <form method="post" action="" style="display:inline-block;">
        <input type="hidden" name="action" value="go_register" />
        <button class="btn-blue" type="submit">Crear Nuevo Agente</button>
      </form>
    </div>
  </main>
</body>
</html>
"""

# --- Panel de administrador (crear partida) ---
def render_admin_page(msg: str | None = None) -> str:
    s = base_styles()
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Acceso de Administrador</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{ background: {s['fondo']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {s['negro']}; display: flex; align-items: center; justify-content: center; }}
    .card {{ width: min(700px, 92vw); background: rgba(255,255,255,0.96); border-radius: 16px; box-shadow: 0 12px 28px rgba(0,0,0,0.18); padding: 36px 30px 30px; text-align: center; }}
    .title {{ font-size: clamp(28px, 6vw, 46px); font-weight: 800; text-align: center; letter-spacing: 0.6px; margin: 0 0 8px 0; }}
    .subtitle {{ font-size: 16px; text-align: center; color: #3a4a59; margin: 0 0 18px 0; }}
    .actions {{ display: flex; justify-content: center; }}
    .btn {{ text-decoration: none; padding: 12px 18px; border-radius: 10px; background: #28a745; color: white; font-weight: 700; border: none; cursor: pointer; }}
    .btn:hover {{ background: #218838; }}
    .msg {{ margin-top: 12px; text-align: center; color: {s['negro']}; font-weight: 600; }}
  </style>
</head>
<body>
  <main class="card">
    <h1 class="title">Acceso de Administrador</h1>
    <p class="subtitle">Crea y supervisa una partida única.</p>
    <div class="actions">
      <form method="post" action="">
        <input type="hidden" name="action" value="create_game" />
        <button class="btn" type="submit">Crear Partida</button>
      </form>
    </div>
    {f'<div class="msg">{msg}</div>' if msg else ''}
  </main>
</body>
</html>
"""

# --- Página de registro de jugador ---
def render_register_page(error: str | None = None, nombre: str = "") -> str:
    s = base_styles()
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Registrar jugador</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{ background: {s['fondo']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {s['negro']}; display: flex; align-items: center; justify-content: center; }}
    .card {{ width: min(640px, 92vw); background: {s['card_bg']}; border-radius: 16px; box-shadow: {s['card_shadow']}; padding: 32px 28px 24px; }}
    .title {{ font-size: clamp(26px, 5.5vw, 42px); font-weight: 800; text-align: center; margin: 0 0 10px 0; }}
    .subtitle {{ font-size: 16px; text-align: center; color: #3a4a59; margin: 0 0 18px 0; }}
    .row {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; }}
    input[type=text] {{ padding: 12px 14px; border: 2px solid #cfe7f6; border-radius: 10px; font-size: 16px; outline: none; transition: border-color .2s ease, box-shadow .2s ease; background: #f7fbff; }}
    input[type=text]:focus {{ border-color: #6fbdf2; box-shadow: 0 0 0 4px rgba(111,189,242,0.2); }}
    .btn-green {{ padding: 12px 20px; border: none; border-radius: 10px; background: #28a745; color: white; font-weight: 700; font-size: 16px; cursor: pointer; }}
    .error {{ margin-top: 12px; color: #dc3545; font-weight: 800; text-align: center; font-size: 15px; }}
  </style>
</head>
<body>
  <main class="card">
    <h1 class="title">Registro de jugador</h1>
    <p class="subtitle">Introduce tu nombre para asignarte un agente secreto aleatorio.</p>
    <form method="post" action="">
      <div class="row">
        <input id="nombre" name="nombre" type="text" value="{nombre}" placeholder="Tu nombre" autocomplete="off" />
        <button class="btn-green" type="submit">OK</button>
      </div>
      {f'<div class="error">{error}</div>' if error else ''}
    </form>
  </main>
</body>
</html>
"""

# --- Página de confirmación de asignación ---
def render_assigned_page(player_name: str, agent_name: str) -> str:
    s = base_styles()
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agente asignado</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{ background: {s['fondo']}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {s['negro']}; display: flex; align-items: center; justify-content: center; }}
    .card {{ width: min(640px, 92vw); background: rgba(255,255,255,0.96); border-radius: 16px; box-shadow: 0 12px 28px rgba(0,0,0,0.18); padding: 36px 30px 26px; text-align: center; }}
    .title {{ font-size: clamp(26px, 6vw, 44px); font-weight: 800; margin: 0 0 10px 0; }}
    .text {{ font-size: 16px; color: #3a4a59; }}
    .btn-green {{
      display: inline-block;
      margin-top: 16px;
      padding: 12px 20px;
      border: none;
      border-radius: 10px;
      background: #28a745;
      color: white;
      font-weight: 700;
      font-size: 16px;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1 class="title">¡Hola, {player_name}!</h1>
    <p class="text">Tu nombre de agente secreto es <strong>{agent_name}</strong>.</p>
    <p class="text">Recuérdalo: lo necesitarás para entrar a tu panel de misiones.</p>
    <!-- action="" para postear a ESTA MISMA URL sin mostrar texto espurio -->
    <form method="post" action="">
      <input type="hidden" name="action" value="assigned_ok" />
      <input type="hidden" name="agent" value="{agent_name}" />
      <button class="btn-green" type="submit">OK</button>
    </form>
  </main>
</body>
</html>
"""

# --- Página de partida (admin): SOLO agentes registrados ---
def render_game_page() -> str:
    s = base_styles()
    registered_agents = [a for a in GAME_STATE["agents"] if a in GAME_STATE["registrations"]]
    agents_li = "\n".join(
        f'<li class="agent-item" data-agent="{name}" tabindex="0">{name}</li>'
        for name in registered_agents
    )
    assignments_json = json.dumps(GAME_STATE["assignments"], ensure_ascii=False)
    statuses_json = json.dumps(GAME_STATE["statuses"], ensure_ascii=False)
    registrations_json = json.dumps(GAME_STATE["registrations"], ensure_ascii=False)
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Partida en curso</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{
      background: {s['fondo']};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: {s['negro']};
      display: flex; align-items: center; justify-content: center;
    }}
    .card {{
      width: min(900px, 94vw);
      background: rgba(255,255,255,0.96);
      border-radius: 16px;
      box-shadow: 0 12px 28px rgba(0,0,0,0.18);
      padding: 30px;
    }}
    .title {{ font-size: clamp(26px, 5.5vw, 44px); font-weight: 800; text-align: center; margin: 0 0 8px 0; }}
    .subtitle {{ font-size: 16px; text-align: center; color: #3a4a59; margin: 0 0 18px 0; }}
    .layout {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    @media (max-width: 840px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    .list-wrap {{
      max-height: 60vh; overflow-y: auto; background: {s['card_bg']};
      border: 2px solid #cfe7f6; border-radius: 12px; padding: 10px 12px;
    }}
    ul {{ list-style: none; margin: 0; padding: 0; }}
    .agent-item {{
      padding: 10px 12px; margin: 6px 0; background: #f7fbff; border: 1px solid #d9eefb;
      border-radius: 10px; font-weight: 600; cursor: pointer; outline: none;
    }}
    .agent-item:hover {{ background: #eef7ff; }}
    .agent-item.selected {{ background: #e0f2ff; border-color: #bde3fa; }}
    .details {{
      background: {s['card_bg']}; border: 2px solid #cfe7f6; border-radius: 12px; padding: 12px 14px; min-height: 220px;
    }}
    .details-title {{ margin: 0 0 6px 0; font-weight: 800; font-size: 18px; }}
    .player-name {{ margin: 0 0 12px 0; color: #3a4a59; font-size: 14px; }}
    .missions {{ list-style: none; padding: 0; margin: 0; }}
    .mission-item {{
      padding: 8px 10px; margin: 6px 0; background: #f7fbff; border: 1px solid #d9eefb; border-radius: 8px; font-size: 14px;
    }}
    .mission-item.st-done {{ background: {s['verde_soft']}; border-color: {s['verde_borde']}; }}
    .mission-item.st-failed {{ background: {s['rojo_soft']}; border-color: {s['rojo_borde']}; }}
    .actions {{ display: flex; justify-content: center; gap: 12px; margin-top: 16px; }}
    .btn-red {{ padding: 12px 16px; border: none; border-radius: 10px; background: {s['rojo']}; color: white; font-weight: 800; cursor: pointer; }}
    .btn-red:hover {{ filter: brightness(0.95); }}
    .legend {{ margin-top: 8px; text-align: center; color: #3a4a59; font-size: 13px; }}
  </style>
  <script>
    const ASSIGNMENTS = {assignments_json};
    const STATUSES = {statuses_json}; // dict: agente -> [0,1,2]
    const REGISTRATIONS = {registrations_json}; // dict: agente -> jugador
    function esc(s) {{
      return String(s).replace(/&/g,"&").replace(/</g,"<").replace(/>/g,">").replace(/\\"/g,"\"").replace(/'/g,"&#39;");
    }}
    function statusClass(v) {{ if (v===1) return "st-done"; if (v===2) return "st-failed"; return ""; }}
    function renderMissions(agent) {{
      const title = document.getElementById("misiones-title");
      const pname = document.getElementById("player-name");
      const list = document.getElementById("misiones-list");
      if (!agent || !ASSIGNMENTS[agent]) {{
        title.textContent = "Selecciona un agente";
        pname.textContent = "";
        list.innerHTML = "";
        return;
      }}
      const jugador = REGISTRATIONS[agent] || "(sin asignar)";
      title.textContent = "Misiones de " + agent;
      pname.textContent = "Jugador: " + jugador;
      const sts = (STATUSES[agent] || []).slice(0, (ASSIGNMENTS[agent] || []).length);
      const items = ASSIGNMENTS[agent].map(function(m, i) {{
        const cls = statusClass(sts[i] || 0);
        return '<li class="mission-item ' + cls + '">' + esc(m) + '</li>';
      }}).join('');
      list.innerHTML = items;
    }}
    function onAgentClick(e) {{
      const li = e.target.closest(".agent-item");
      if (!li) return;
      document.querySelectorAll(".agent-item.selected").forEach(el => el.classList.remove("selected"));
      li.classList.add("selected");
      renderMissions(li.dataset.agent);
    }}
    function terminarPartida() {{
      if (confirm("¿Seguro que quieres terminar la partida?")) {{
        document.getElementById("end-form").submit();
      }}
    }}
    document.addEventListener("DOMContentLoaded", () => {{
      const ul = document.getElementById("agent-list");
      ul.addEventListener("click", onAgentClick);
      ul.addEventListener("keydown", (e) => {{ if (e.key === "Enter") onAgentClick(e); }});
      renderMissions("");
    }});
  </script>
</head>
<body>
  <main class="card">
    <h1 class="title">Partida en curso</h1>
    <p class="subtitle">Agentes secretos registrados:</p>
    <div class="layout">
      <div class="list-wrap">
        <ul id="agent-list">
          {agents_li}
        </ul>
      </div>
      <div class="details">
        <h3 id="misiones-title" class="details-title">Selecciona un agente</h3>
        <p id="player-name" class="player-name"></p>
        <ul id="misiones-list" class="missions"></ul>
        <p class="legend">Estados: <strong>Verde</strong> = completada · <strong>Rojo</strong> = fallada · <strong>Normal</strong> = pendiente (solo lectura en este panel).</p>
      </div>
    </div>
    <div class="actions">
      <form id="end-form" method="post" action="">
        <input type="hidden" name="action" value="end_game" />
        <button class="btn-red" type="button" onclick="terminarPartida()">Terminar partida</button>
      </form>
    </div>
  </main>
</body>
</html>
"""

# --- Panel del agente (interactivo) ---
def render_agent_panel(agent_name: str, missions: list[str]) -> str:
    s = base_styles()
    statuses = GAME_STATE["statuses"].get(agent_name, [0, 0, 0, 0, 0])
    player_name = GAME_STATE["registrations"].get(agent_name, "")
    assignments_json = json.dumps(missions, ensure_ascii=False)
    statuses_json = json.dumps(statuses, ensure_ascii=False)
    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agente: {agent_name}</title>
  <style>
    html, body {{ height: 100%; margin: 0; }}
    body {{
      background: {s['fondo']};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: {s['negro']};
      display: flex; align-items: center; justify-content: center;
    }}
    .card {{
      width: min(720px, 92vw);
      background: rgba(255,255,255,0.96);
      border-radius: 16px;
      box-shadow: 0 12px 28px rgba(0,0,0,0.18);
      padding: 34px 30px 24px;
    }}
    .title {{ font-size: clamp(26px, 6vw, 44px); font-weight: 800; text-align: center; margin: 0 0 6px 0; }}
    .subtitle {{ font-size: 14px; text-align: center; color: #3a4a59; margin: 0 0 14px 0; }}
    .missions {{ list-style: none; padding: 0; margin: 0; }}
    .mission-item {{
      padding: 10px 12px; margin: 8px 0; background: #f7fbff; border: 1px solid #d9eefb; border-radius: 10px;
      font-size: 15px; cursor: pointer; transition: background .15s ease, border-color .15s ease;
    }}
    .mission-item.st-done {{ background: {s['verde_soft']}; border-color: {s['verde_borde']}; }}
    .mission-item.st-failed {{ background: {s['rojo_soft']}; border-color: {s['rojo_borde']}; }}
    .help {{ margin-top: 12px; font-size: 13px; color: #415466; text-align: center; }}
  </style>
  <script>
    const AGENT = "{agent_name}";
    const MISSIONS = {assignments_json};
    let STATUSES = {statuses_json}; // 0: pendiente, 1: completada, 2: fallada
    function esc(s) {{
      return String(s).replace(/&/g,"&").replace(/</g,"<").replace(/>/g,">").replace(/\\"/g,"\"").replace(/'/g,"&#39;");
    }}
    function statusClass(v) {{ if (v===1) return "st-done"; if (v===2) return "st-failed"; return ""; }}
    function renderList() {{
      const ul = document.getElementById("missions");
      ul.innerHTML = MISSIONS.map(function(m, i) {{
        return '<li class="mission-item ' + statusClass(STATUSES[i]) + '" data-idx="' + i + '">' + esc(m) + '</li>';
      }}).join('');
    }}
    function cycle(idx) {{ STATUSES[idx] = (STATUSES[idx] + 1) % 3; }}
    async function persist(idx) {{
      try {{
        const body = 'action=toggle&name=' + encodeURIComponent(AGENT) + '&idx=' + encodeURIComponent(idx);
        await fetch('/agent', {{ method:'POST', headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }}, body }});
      }} catch(e){{}}
    }}
    function onClick(e) {{
      const li = e.target.closest('.mission-item'); if (!li) return;
      const idx = Number(li.getAttribute('data-idx'));
      cycle(idx);
      li.classList.remove('st-done','st-failed');
      const cls = statusClass(STATUSES[idx]); if (cls) li.classList.add(cls);
      persist(idx);
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      renderList();
      document.getElementById('missions').addEventListener('click', onClick);
    }});
  </script>
</head>
<body>
  <main class="card">
    <h1 class="title">Agente: {agent_name}</h1>
    <p class="subtitle">Jugador: {player_name}</p>
    <ul id="missions" class="missions"></ul>
    <p class="help">Pulsa sobre una misión para alternar su estado: <strong>Pendiente</strong> → <strong>Completada</strong> (verde) → <strong>Fallada</strong> (rojo) → <strong>Pendiente</strong>.</p>
  </main>
</body>
</html>
"""

# --- Helpers ---
def html_escape(s: str) -> str:
    return (s.replace("&","&").replace("<","<").replace(">",">").replace("\"","\"").replace("'","&#39;"))

# --- Lógica: crear/terminar partida ---
def crear_partida():
    if GAME_STATE["active"]:
        return
    agents = AGENTES_CANDIDATOS.copy()
    random.shuffle(agents)
    misiones = MISIONES.copy()
    random.shuffle(misiones)
    assignments = {}
    statuses = {}
    for i, nombre in enumerate(agents):
        inicio = i * 5
        fin = inicio + 5
        assignments[nombre] = misiones[inicio:fin]
        statuses[nombre] = [0, 0, 0, 0, 0]  # inicial: todas pendientes
    GAME_STATE["active"] = True
    GAME_STATE["agents"] = agents
    GAME_STATE["assignments"] = assignments
    GAME_STATE["statuses"] = statuses
    GAME_STATE["registrations"] = {}

def terminar_partida():
    GAME_STATE["active"] = False
    GAME_STATE["agents"] = []
    GAME_STATE["assignments"] = {}
    GAME_STATE["statuses"] = {}
    GAME_STATE["registrations"] = {}

# --- Utilidad: IP local preferida (ya no se usa en Render, pero lo dejamos para uso local) ---
def get_local_ip() -> str:
    ip = "127.0.0.1"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    return ip

# --- Handler HTTP ---
class SideMissionsHandler(BaseHTTPRequestHandler):
    def _send_html(self, html: str, status: int = 200):
        data = html.encode("utf-8")
        self.send_response(status)
        # Anti-caché
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: int = 200):
        data = text.encode("utf-8")
        self.send_response(status)
        # Anti-caché también en texto/JSON
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str, status: int = 303):
        self.send_response(status)
        self.send_header("Location", location)
        # Anti-caché en redirecciones
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

    # Compara SOLO el path (sin query) y sin barra final
    def _path_is(self, *candidates):
        current_path = urlparse(self.path).path.rstrip("/")
        targets = {urlparse(c).path.rstrip("/") for c in candidates}
        return current_path in targets

    # --- GET routing ---
    def do_GET(self):
        # Health check / ping (para mantener activo en Render con monitores externos)
        if self._path_is("/ping", "/health"):
            self._send_text("ok", status=200)
            return

        # Admin
        if self._path_is("/admin"):
            if GAME_STATE["active"]:
                self._redirect("/game", status=303)
            else:
                self._send_html(render_admin_page())
            return

        # Admin game
        if self._path_is("/game"):
            if GAME_STATE["active"]:
                self._send_html(render_game_page())
            else:
                self._send_html(render_admin_page(msg="No hay partida activa"))
            return

        # Registro
        if self._path_is("/register"):
            if not GAME_STATE["active"]:
                # Mostrar portada con error, sin redirigir
                self._send_html(render_page(error="No hay partida activa. Pide al admin crear una."))
                return
            self._send_html(render_register_page())
            return

        # Confirmación de asignación (GET muestra la página)
        if self._path_is("/assigned"):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            agent = (qs.get("agent", [""])[0]).strip().lower()
            player = GAME_STATE["registrations"].get(agent, "")
            if not (GAME_STATE["active"] and agent in GAME_STATE["agents"] and player):
                self._send_html(render_page(error="Asignación no válida o sesión caducada."))
                return
            self._send_html(render_assigned_page(player_name=player, agent_name=agent))
            return

        # Panel de agente directo
        if urlparse(self.path).path.startswith("/agent"):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            name = (qs.get("name", [""])[0]).strip().lower()
            if GAME_STATE["active"] and name in GAME_STATE["agents"]:
                missions = GAME_STATE["assignments"].get(name, [])
                self._send_html(render_agent_panel(agent_name=name, missions=missions))
            else:
                self._send_html(render_page(error="No se encuentra este agente secreto"))
            return

        # Portada
        self._send_html(render_page())

    # --- POST routing ---
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        data = parse_qs(raw, keep_blank_values=True)

        # Admin
        if self._path_is("/admin"):
            action = (data.get("action", [""])[0]).strip().lower()
            if action == "create_game":
                crear_partida()
                self._redirect("/game")
                return
            self._send_html(render_admin_page())
            return

        # Game
        if self._path_is("/game"):
            action = (data.get("action", [""])[0]).strip().lower()
            if action == "end_game":
                terminar_partida()
                self._redirect("/admin")
                return
            if GAME_STATE["active"]:
                self._send_html(render_game_page())
            else:
                self._send_html(render_admin_page())
            return

        # Registro
        if self._path_is("/register"):
            if not GAME_STATE["active"]:
                self._send_html(render_page(error="No hay partida activa. Pide al admin crear una."))
                return
            nombre = (data.get("nombre", [""])[0]).strip()
            if not nombre:
                self._send_html(render_register_page(error="Debes introducir tu nombre.", nombre=nombre))
                return
            libres = [a for a in GAME_STATE["agents"] if a not in GAME_STATE["registrations"]]
            if not libres:
                self._send_html(render_register_page(error="No hay agentes disponibles ahora mismo.", nombre=nombre))
                return
            agent = random.choice(libres)
            GAME_STATE["registrations"][agent] = nombre
            self._redirect(f"/assigned?agent={agent}")
            return

        # Confirmación OK -> volver a la portada (NO al panel del agente)
        if self._path_is("/assigned"):
            action = (data.get("action", [""])[0]).strip().lower()
            agent = (data.get("agent", [""])[0]).strip().lower()
            if action == "assigned_ok":
                if GAME_STATE["active"] and agent in GAME_STATE["agents"]:
                    self._redirect("/")  # vuelve a la portada
                    return
            self._send_html(render_page(error="Asignación no válida o sesión caducada."))
            return

        # Panel agente: toggle estados via fetch
        if self._path_is("/agent"):
            action = (data.get("action", [""])[0]).strip().lower()
            name = (data.get("name", [""])[0]).strip().lower()
            if action == "toggle" and GAME_STATE["active"] and name in GAME_STATE["agents"]:
                idx_str = (data.get("idx", [""])[0]).strip()
                try:
                    idx = int(idx_str)
                except Exception:
                    self._send_text("bad request", status=400)
                    return
                statuses = GAME_STATE["statuses"].get(name)
                missions = GAME_STATE["assignments"].get(name)
                if not statuses or not missions or not (0 <= idx < len(missions)):
                    self._send_text("bad request", status=400)
                    return
                # Alterna estado y persiste en memoria
                statuses[idx] = (statuses[idx] + 1) % 3
                GAME_STATE["statuses"][name] = statuses
                self._send_text("ok", status=200)
                return
            self._send_text("bad request", status=400)
            return

        # Portada: botón Crear Nuevo Agente (action=go_register) o acceso por agente/admin
        action = (data.get("action", [""])[0]).strip().lower()
        if action == "go_register":
            if not GAME_STATE["active"]:
                self._send_html(render_page(error="No hay partida activa. Pide al admin crear una."))
                return
            self._redirect("/register")
            return

        # Portada: validación agente / admin
        agente = (data.get("agente", [""])[0]).strip()
        if not agente:
            self._send_html(render_page(error="No has introducido un nombre de agente secreto", agente=agente))
            return
        if agente.lower() == ADMIN_USERNAME:
            self._redirect("/game" if GAME_STATE["active"] else "/admin")
            return
        name = agente.lower()
        if GAME_STATE["active"] and name in GAME_STATE["agents"]:
            missions = GAME_STATE["assignments"].get(name, [])
            self._send_html(render_agent_panel(agent_name=name, missions=missions))
            return
        self._send_html(render_page(error="No se encuentra este agente secreto", agente=agente))

    def log_message(self, format, *args):
        # Silenciar logs por defecto (puedes habilitar para diagnóstico en Render)
        return


# --- Run server ---
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run_server(host: str, port: int):
    httpd = ThreadingHTTPServer((host, port), SideMissionsHandler)
    print(f"Side Missions iniciado: http://{host}:{port}")
    print("Pulsa Ctrl+C para detenerlo.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Servidor detenido.")

if __name__ == "__main__":
    # En Render, PORT viene desde el entorno. Default 8000 para local.
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    run_server(host, port)
