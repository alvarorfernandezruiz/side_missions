from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, random
from urllib.parse import parse_qs
from threading import Lock

STATE_FILE = "game_state.json"
LOCK = Lock()
ADMIN_AGENT = "itadmin"

AGENT_NAMES = [
    "bola","ocho","tigre","peine","gato","perro","mesa","silla","libro","calle",
    "parque","vaso","plato","techo","suelo","cable","foco","nube","lluvia","cubo",
    "coche","moto","barco","vapor","planta","piedra","cuadro","puerta","mapa","clave",
    "notas","perfil","torre","reloj","metal","papel","cinta","radio","farol","cesto",
    "casco","guante","caja","filtro","motor","banco","campo","sello","traje","plomo",
]

MISSIONS = [
    "Consigue que alguien diga la palabra 'vale'.",
    "Haz que alguien diga 'mañana'.",
    "Logra que alguien diga 'si' sin que se lo pidas directamente.",
    "Consigue que alguien diga 'no' en respuesta a algo tuyo.",
    "Haz que alguien mencione 'Madrid'.",
    "Consigue que alguien diga 'secreto'.",
    "Haz que alguien diga 'azul'.",
    "Haz que alguien diga 'verde'.",
    "Consigue que alguien diga 'codigo'.",
    "Haz que alguien diga 'idea'.",
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
# Lógica
# -------------------------

def generate_agents():
    return {
        name: {
            "player": None,
            "missions": [
                {"text": random.choice(MISSIONS), "status": "pending"}
                for _ in range(5)
            ]
        } for name in AGENT_NAMES
    }

def assign_agent(state, player):
    for agent, data in state["agents"].items():
        if data["player"] is None:
            data["player"] = player
            state["players"][player] = agent
            return agent
    return None

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
                self.page_register()

        elif path == "/agent":
            self.page_agent(state)

        elif path == "/admin":
            self.page_admin(state)

        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(length).decode())
        state = load_state()

        if self.path == "/login":
            agent = data.get("agent", [""])[0].strip().casefold()
            if agent == ADMIN_AGENT:
                self.redirect("/admin")
                return
            if not state["active"] or agent not in state["agents"]:
                self.redirect("/?error=Agente incorrecto")
                return
            self.redirect(f"/agent?name={agent}")

        elif self.path == "/register":
            name = data.get("name", [""])[0].strip()
            if not name:
                self.redirect("/register")
                return
            agent = assign_agent(state, name)
            save_state(state)
            self.page_assigned(agent)

        elif self.path == "/toggle":
            agent = data["agent"][0]
            idx = int(data["idx"][0])
            m = state["agents"][agent]["missions"][idx]
            m["status"] = (
                "completed" if m["status"] == "pending"
                else "failed" if m["status"] == "completed"
                else "pending"
            )
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
            self.redirect("/")

    # -------------------------
    # Páginas
    # -------------------------

    def page_home(self, error):
        self.html(f"""
        <h1>Side Missions</h1>
        {f"<div class='error'>{error}</div>" if error else ""}
        <form method="post" action="/login">
            <input name="agent" placeholder="Nombre de agente">
            <button>Entrar</button>
        </form>
        <a class="link" href="/register">Registrarse</a>
        """)

    def page_register(self):
        self.html("""
        <h2>Registro</h2>
        <form method="post" action="/register">
            <input name="name" placeholder="Tu nombre real">
            <button>OK</button>
        </form>
        """)

    def page_assigned(self, agent):
        self.html(f"""
        <h2>Tu agente secreto es</h2>
        <div class="agent">{agent}</div>
        <a class="link" href="/">Volver</a>
        """)

    def page_agent(self, state):
        agent = parse_qs(self.path.split("?")[1]).get("name", [""])[0]
        data = state["agents"].get(agent)
        if not data:
            self.redirect("/")
            return

        cards = ""
        for i, m in enumerate(data["missions"]):
            cards += f"""
            <div class="card {m['status']}" onclick="toggle({i})">
                {m['text']}
            </div>
            """

        self.html(f"""
        <h2>Agente {agent}</h2>
        {cards}
        <script>
        function toggle(i){{
            fetch("/toggle", {{
                method:"POST",
                headers:{{"Content-Type":"application/x-www-form-urlencoded"}},
                body:"agent={agent}&idx="+i
            }}).then(()=>location.reload())
        }}
        </script>
        """)

    def page_admin(self, state):
        players = ""
        modals = ""

        for player, agent in state["players"].items():
            players += f"""
            <div class="player" onclick="openModal('{player}')">
                {player}
            </div>
            """

            cards = ""
            for m in state["agents"][agent]["missions"]:
                cards += f"<div class='card {m['status']}'>{m['text']}</div>"

            modals += f"""
            <div id="modal-{player}" class="modal">
                <div class="modal-content">
                    <h3>{agent}</h3>
                    <p class="subtitle">{player}</p>
                    <div class="modal-cards">{cards}</div>
                    <button class="danger" onclick="closeModal('{player}')">Cerrar</button>
                </div>
            </div>
            """

        self.html(f"""
        <h2>Admin</h2>
        <div class="list">{players}</div>
        {modals}
        <form method="post" action="/start"><button>Nueva Partida</button></form>
        <form method="post" action="/end"><button class="danger">Terminar partida</button></form>

        <script>
        function openModal(p){{
            document.getElementById("modal-"+p).style.display="flex";
        }}
        function closeModal(p){{
            document.getElementById("modal-"+p).style.display="none";
        }}
        </script>
        """)

    # -------------------------
    # HTML base (RESPONSIVE + FIX)
    # -------------------------

    def html(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Side Missions</title>
<style>
* {{
    box-sizing: border-box;
}}

body {{
    background:#0e0e11;
    color:#fff;
    font-family:system-ui, sans-serif;
    text-align:center;
    padding:16px;
    margin:0;
}}

h1 {{ font-size:clamp(28px, 6vw, 40px); }}
h2 {{ font-size:clamp(22px, 5vw, 32px); }}

input, button {{
    width:100%;
    max-width:420px;
    padding:14px 16px;
    border-radius:18px;
    border:none;
    font-size:18px;
    margin:10px auto;
    display:block;
}}

button {{
    background:#5865f2;
    color:white;
}}

.danger {{ background:#d33; }}

.link {{
    color:#aaa;
    display:block;
    margin-top:20px;
}}

.agent {{
    font-size:clamp(32px, 8vw, 48px);
    margin:24px;
}}

.card {{
    background:#f2f2f2;
    color:#111;
    padding:20px;
    margin:12px auto;
    border-radius:20px;
    max-width:480px;
    width:100%;
}}

.completed {{ background:#2ecc71; }}
.failed {{ background:#e74c3c; }}

.player {{
    background:#1e1e2a;
    padding:16px;
    border-radius:16px;
    margin:10px auto;
    max-width:420px;
    cursor:pointer;
}}

.list {{
    max-height:60vh;
    overflow-y:auto;
}}

.modal {{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.75);
    display:none;
    align-items:center;
    justify-content:center;
}}

.modal-content {{
    background:#111;
    padding:24px;
    border-radius:24px;
    width:90%;
    max-width:500px;
    max-height:80vh;
    overflow-y:auto;
}}

.subtitle {{
    color:#aaa;
    margin-bottom:16px;
}}

.error {{
    color:#f66;
    margin-bottom:12px;
}}
</style>
</head>
<body>
{body}
</body>
</html>
""".encode())

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

# -------------------------
# Server
# -------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    HTTPServer(("", port), Handler).serve_forever()
