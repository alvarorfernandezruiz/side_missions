from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import random
from urllib.parse import parse_qs
from threading import Lock

STATE_FILE = "game_state.json"
state_lock = Lock()

DEFAULT_STATE = {
    "active": False,
    "agents": {},
    "players": {}
}

AGENT_NAMES = [
    "bola", "ocho", "tigre", "peine", "gato", "perro", "mesa", "silla", "libro", "calle",
    "parque", "vaso", "plato", "techo", "suelo", "cable", "foco", "nube", "lluvia", "cubo",
    "coche", "moto", "barco", "vapor", "planta", "piedra", "cuadro", "puerta", "mapa", "clave",
    "notas", "perfil", "torre", "reloj", "metal", "papel", "cinta", "radio", "farol", "cesto",
    "casco", "guante", "caja", "filtro", "motor", "banco", "campo", "sello", "traje", "plomo",
]

MISSIONS = [
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


# ------------------------
# Estado persistente
# ------------------------

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE.copy()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with state_lock:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)


# ------------------------
# Helpers
# ------------------------

def generate_agents():
    agents = {}
    for name in AGENT_NAMES:
        agents[name] = {
            "player": None,
            "missions": [
                {"text": random.choice(MISSIONS), "status": "pending"}
                for _ in range(5)
            ]
        }
    return agents


def free_agent(state):
    for name, agent in state["agents"].items():
        if agent["player"] is None:
            return name
    return None


# ------------------------
# HTTP Handler
# ------------------------

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        state = load_state()
        path = self.path.split("?")[0]

        if path == "/":
            self.page_home(state)
        elif path == "/admin":
            self.page_admin(state)
        elif path == "/agent":
            self.page_agent(state)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(length).decode())
        state = load_state()

        if self.path == "/start":
            state["active"] = True
            state["agents"] = generate_agents()
            state["players"] = {}
            save_state(state)
            self.redirect("/admin")

        elif self.path == "/end":
            save_state(DEFAULT_STATE.copy())
            self.redirect("/")

        elif self.path == "/register":
            name = data.get("name", [""])[0]
            if name and state["active"]:
                agent = free_agent(state)
                if agent:
                    state["players"][name] = agent
                    state["agents"][agent]["player"] = name
                    save_state(state)
                    self.redirect(f"/agent?name={agent}")
                    return
            self.redirect("/")

        elif self.path == "/mission":
            agent = data["agent"][0]
            index = int(data["index"][0])
            state["agents"][agent]["missions"][index]["status"] = data["status"][0]
            save_state(state)
            self.send_response(204)
            self.end_headers()

    # ------------------------
    # Pages
    # ------------------------

    def page_home(self, state):
        self.html(f"""
        <h1>Side Missions</h1>
        {"<p>Partida activa</p>" if state["active"] else "<p>No hay partida</p>"}
        <form method="post" action="/register">
            <input name="name" placeholder="Tu nombre" required>
            <button>Entrar</button>
        </form>
        <a href="/admin">Admin</a>
        """)

    def page_admin(self, state):
        body = "<h1>Admin</h1>"
        if not state["active"]:
            body += """
            <form method="post" action="/start">
                <button>Iniciar partida</button>
            </form>
            """
        else:
            body += "<h2>Agentes</h2>"
            for a, info in state["agents"].items():
                if info["player"]:
                    body += f"<p><b>{a}</b> – {info['player']}</p>"
                    for m in info["missions"]:
                        body += f"<li>{m['text']} ({m['status']})</li>"
            body += """
            <form method="post" action="/end">
                <button>Terminar partida</button>
            </form>
            """
        self.html(body)

    def page_agent(self, state):
        params = parse_qs(self.path.split("?")[1])
        name = params.get("name", [""])[0]
        agent = state["agents"].get(name)

        if not agent:
            self.redirect("/")
            return

        body = f"<h1>Agente {name}</h1>"
        for i, m in enumerate(agent["missions"]):
            body += f"""
            <p>{m['text']} – {m['status']}
            <button onclick="update({i}, 'completed')">✔</button>
            <button onclick="update({i}, 'failed')">✖</button></p>
            """

        body += f"""
        <script>
        function update(i, s) {{
            fetch("/mission", {{
                method: "POST",
                headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                body: "agent={name}&index="+i+"&status="+s
            }}).then(()=>location.reload());
        }}
        </script>
        """

        self.html(body)

    # ------------------------
    # Utils
    # ------------------------

    def html(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()


# ------------------------
# Server
# ------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    HTTPServer(("", port), Handler).serve_forever()
