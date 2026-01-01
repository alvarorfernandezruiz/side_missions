from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, random
from urllib.parse import parse_qs
from threading import Lock

STATE_FILE = "game_state.json"
LOCK = Lock()
ADMIN_AGENT = "itadmin"

# -------------------------
# Nombres de agentes secretos
# -------------------------
AGENT_NAMES = [
    "Clave","Sombra","Código","Rastro","Eco","Pulso","Trama","Fuga","Señal","Vector",
    "Padrino","Golpe","Dólar","Bala","Farsa","Robo","Tiro","Cruce","Alias","Filtro",
    "Impacto","Choque","Corte","Falla","Giro","Ruido","Salto","Quiebre","Derrape","Alerta",
    "Niebla","Rayo","Lobo","Cuervo","Bruma","Fuego","Hielo","Viento","Sismo","Delta",
    "Enigma","Secreto","Silencio","Control","Sello","Prisma","Mente","Origen","Núcleo"
]

# -------------------------
# Misiones actualizadas con tildes y español de España
# -------------------------
MISSIONS = [
    "Consigue que alguien diga la palabra 'vale'.",
    "Haz que alguien diga 'mañana'.",
    "Logra que alguien diga 'sí' sin que se lo pidas directamente.",
    "Consigue que alguien diga 'no' en respuesta a algo tuyo.",
    "Haz que alguien mencione 'Madrid'.",
    "Logra que alguien diga 'secreto'.",
    "Consigue que alguien diga 'misión'.",
    "Haz que alguien diga 'azul'.",
    "Haz que alguien diga 'verde'.",
    "Consigue que alguien diga 'código'.",
    "Consigue que alguien te preste un bolígrafo.",
    "Logra que alguien te deje una hoja de papel.",
    "Pide y consigue un cargador para el móvil.",
    "Consigue que alguien te ofrezca una silla.",
    "Logra que alguien te alcance una chaqueta.",
    "Pide y consigue una botella de agua.",
    "Consigue que alguien te ofrezca chicle o caramelo.",
    "Logra que alguien te preste sus gafas por un momento.",
    "Pide y consigue una servilleta.",
    "Consigue que alguien te alcance la sal o azúcar.",
    "Logra que alguien te ofrezca un post-it.",
    "Pide y consigue cinta adhesiva.",
    "Consigue que alguien te deje su móvil para una foto.",
    "Logra que alguien te preste un marcador o rotulador.",
    "Pide y consigue un mechero (aunque no fumes).",
    "Consigue que alguien te ofrezca una mascarilla.",
    "Logra que alguien te preste un libro por un minuto.",
    "Pide y consigue un abridor o destapador.",
    "Consigue que alguien te alcance un vaso.",
    "Logra que alguien te preste un paraguas.",
    "Pide y consigue un clip o broche.",
    "Consigue que alguien te ofrezca un caramelo de menta.",
    "Logra que alguien te preste su reloj un segundo.",
    "Pide y consigue un cable USB.",
    "Consigue que alguien te ofrezca un pañuelo.",
    "Logra que alguien te alcance un plato.",
    "Pide y consigue un mechero (sin usarlo).",
    "Consigue que alguien te preste una gorra.",
    "Logra que alguien te ofrezca una bolsa.",
    "Pide y consigue una llave (sin usarla).",
    "Consigue que alguien te alcance el mando de la TV.",
    "Logra que alguien te preste un cuaderno.",
    "Pide y consigue una regla.",
    "Consigue que alguien te preste un lápiz.",
    "Logra que alguien te alcance un tenedor.",
    "Pide y consigue una cuchara.",
    "Consigue que alguien te ofrezca un juego de cartas.",
    "Logra que alguien te preste un dispensador de gel.",
    "Pide y consigue una etiqueta.",
    "Consigue que alguien te preste una batería externa.",
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
    "Haz que alguien mire su móvil por tu frase.",
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
]

DEFAULT_STATE = {"active": False, "agents": {}, "players": {}}

# -------------------------
# Persistencia
# -------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with LOCK:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

# -------------------------
# Lógica de asignación
# -------------------------
def generate_agents():
    names = AGENT_NAMES[:]
    random.shuffle(names)
    return {
        name: {
            "player": None,
            "missions": [
                {"text": random.choice(MISSIONS), "status": "pending"} for _ in range(5)
            ]
        } for name in names
    }

def assign_agent(state, player):
    free_agents = [a for a, d in state["agents"].items() if d["player"] is None]
    if not free_agents:
        return None
    agent = random.choice(free_agents)
    state["agents"][agent]["player"] = player
    state["players"][player] = agent
    return agent

# -------------------------
# HTTP Handler
# -------------------------
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        state = load_state()
        path, _, qs = self.path.partition("?")
        params = parse_qs(qs)

        if path == "/":
            self.page_home(params.get("error", [""])[0])
        elif path == "/register":
            if not state["active"]:
                self.redirect("/?error=No hay partida iniciada")
            else:
                self.page_register(params.get("error", [""])[0])
        elif path == "/agent":
            self.page_agent(state)
        elif path == "/admin":
            if not state["active"]:
                self.page_admin_start()
            else:
                self.page_admin(state)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(length).decode())
        state = load_state()

        if self.path == "/login":
            agent_input = data.get("agent", [""])[0].strip()
            key = agent_input.casefold()
            if key == ADMIN_AGENT:
                self.redirect("/admin")
                return
            agent_match = next((a for a in state["agents"] if a.casefold() == key), None)
            if not state["active"] or not agent_match:
                self.redirect("/?error=Agente incorrecto")
                return
            self.redirect(f"/agent?name={agent_match}")

        elif self.path == "/register":
            name = data.get("name", [""])[0].strip()
            if not name:
                self.redirect("/register")
                return
            if any(p.casefold() == name.casefold() for p in state["players"]):
                self.redirect("/register?error=Ya hay un agente con este nombre en la partida")
                return
            agent = assign_agent(state, name)
            save_state(state)
            self.page_assigned(agent)

        elif self.path == "/toggle":
            agent = data["agent"][0]
            idx = int(data["idx"][0])
            m = state["agents"][agent]["missions"][idx]
            m["status"] = ("completed" if m["status"]=="pending" else "failed" if m["status"]=="completed" else "pending")
            save_state(state)
            self.send_response(204)
            self.end_headers()

        elif self.path == "/start":
            state["active"] = True
            state["agents"] = generate_agents()
            state["players"] = {}
            save_state(state)
            self.redirect("/admin")

        elif self.path == "/end":
            save_state(DEFAULT_STATE.copy())
            self.redirect("/admin")

    # -------------------------
    # Páginas
    # -------------------------
    # Aquí van las funciones page_home, page_register, page_assigned, page_agent, page_admin_start, page_admin
    # Con HTML, CSS, modal, etc., exactamente igual que la última versión que teníamos completa

# -------------------------
# Servidor
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    HTTPServer(("", port), Handler).serve_forever()
