from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, random
from urllib.parse import parse_qs
from threading import Lock

STATE_FILE = "game_state.json"
LOCK = Lock()
ADMIN_AGENT = "itadmin"

AGENT_NAMES = [
    "Bola","Ocho","Tigre","Peine","Gato","Perro","Mesa","Silla","Libro","Calle",
    "Parque","Vaso","Plato","Techo","Suelo","Cable","Foco","Nube","Lluvia","Cubo",
    "Coche","Moto","Barco","Vapor","Planta","Piedra","Cuadro","Puerta","Mapa","Clave",
    "Notas","Perfil","Torre","Reloj","Metal","Papel","Cinta","Radio","Farol","Cesto",
    "Casco","Guante","Caja","Filtro","Motor","Banco","Campo","Sello","Traje","Plomo",
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
            agent_input = data.get("agent", [""])[0].strip()
            agent_key = agent_input.casefold()

            if agent_key == ADMIN_AGENT:
                self.redirect("/admin")
                return

            agent_match = next(
                (a for a in state["agents"] if a.casefold() == agent_key),
                None
            )

            if not state["active"] or not agent_match:
                self.redirect("/?error=Agente incorrecto")
                return

            self.redirect(f"/agent?name={agent_match}")

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
        <h1>SIDE MISSIONS</h1>
        {f"<div class='error'>{error}</div>" if error else ""}
        <div class="panel">
            <form method="post" action="/login">
                <input name="agent" placeholder="Nombre de agente secreto">
                <button>Entrar</button>
            </form>
            <a class="link" href="/register">Registrarse</a>
        </div>
        """)

    def page_register(self):
        self.html("""
        <h2>Registro</h2>
        <div class="panel">
            <form method="post" action="/register">
                <input name="name" placeholder="Tu nombre real">
                <button>OK</button>
            </form>
        </div>
        """)

    def page_assigned(self, agent):
        self.html(f"""
        <h2>Tu agente secreto es</h2>
        <div class="panel">
            <div class="agent">{agent}</div>
            <a class="link" href="/">Volver</a>
        </div>
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
        <div class="panel">{cards}</div>
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
                    {cards}
                    <button class="danger" onclick="closeModal('{player}')">Cerrar</button>
                </div>
            </div>
            """

        self.html(f"""
        <h2>Admin</h2>
        <div class="panel list">{players}</div>
        {modals}
        <div class="panel">
            <form method="post" action="/start"><button>Nueva Partida</button></form>
            <form method="post" action="/end"><button class="danger">Terminar partida</button></form>
        </div>
        <script>
        function openModal(p){{document.getElementById("modal-"+p).style.display="flex";}}
        function closeModal(p){{document.getElementById("modal-"+p).style.display="none";}}
        </script>
        """)

    # -------------------------
    # HTML base (NUEVO ESTILO)
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
* {{ box-sizing: border-box; }}

body {{
    margin:0;
    font-family:system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    background:linear-gradient(180deg, #9adcf7, #cfefff);
    color:#033;
    text-align:center;
    padding:20px;
}}

h1 {{
    font-size:clamp(32px, 7vw, 52px);
    letter-spacing:4px;
    color:#045;
    margin-bottom:24px;
}}

h2 {{
    font-size:clamp(22px, 5vw, 32px);
    color:#045;
}}

.panel {{
    background:rgba(255,255,255,0.75);
    backdrop-filter: blur(8px);
    border-radius:32px;
    padding:24px;
    margin:20px auto;
    max-width:500px;
    box-shadow:0 20px 40px rgba(0,0,0,0.1);
}}

input, button {{
    width:100%;
    max-width:420px;
    padding:14px 16px;
    border-radius:24px;
    border:none;
    font-size:18px;
    margin:10px auto;
    display:block;
}}

button {{
    background:#1b8cff;
    color:white;
    font-weight:600;
}}

.danger {{ background:#e74c3c; }}

.link {{
    color:#045;
    display:block;
    margin-top:16px;
}}

.agent {{
    font-size:42px;
    font-weight:700;
    color:#1b8cff;
}}

.card {{
    background:white;
    border-radius:24px;
    padding:18px;
    margin:12px 0;
    box-shadow:0 10px 20px rgba(0,0,0,0.08);
}}

.completed {{ background:#b9f3d0; }}
.failed {{ background:#f7b4b4; }}

.player {{
    background:#e9f7ff;
    padding:16px;
    border-radius:20px;
    margin:10px auto;
    cursor:pointer;
}}

.modal {{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,0.4);
    display:none;
    align-items:center;
    justify-content:center;
}}

.modal-content {{
    background:white;
    padding:24px;
    border-radius:32px;
    max-width:520px;
    width:90%;
    max-height:80vh;
    overflow-y:auto;
}}

.subtitle {{ color:#666; margin-bottom:12px; }}
.error {{ color:#c00; }}
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
