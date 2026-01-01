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
    names = AGENT_NAMES[:]
    random.shuffle(names)
    return {
        name: {
            "player": None,
            "missions": [
                {"text": random.choice(MISSIONS), "status": "pending"}
                for _ in range(5)
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

            agent_match = next(
                (a for a in state["agents"] if a.casefold() == key),
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
            self.redirect("/admin")

    # -------------------------
    # Páginas
    # -------------------------

    def page_home(self, error):
        self.html(f"""
        <h1>SIDE MISSIONS</h1>
        <p class="hint">Introduce tu nombre de agente para acceder a tus misiones secretas</p>
        {f"<div class='error'>{error}</div>" if error else ""}
        <div class="panel">
            <form method="post" action="/login">
                <input name="agent" placeholder="Nombre de agente secreto">
                <button>Entrar</button>
            </form>
            <a class="link" href="/register">¿Aún no tienes agente? Regístrate</a>
        </div>
        """)

    def page_register(self, error=""):
        self.html(f"""
        <h2>Registro</h2>
        <p class="hint">Elige cómo te identificarás durante esta partida</p>
        {f"<div class='error'>{error}</div>" if error else ""}
        <div class="panel">
            <form method="post" action="/register">
                <input name="name" placeholder="Introduce tu nombre">
                <button>Continuar</button>
            </form>
        </div>
        """)

    def page_assigned(self, agent):
        self.html(f"""
        <h2>Tu nombre de agente secreto es:</h2>
        <div class="panel">
            <div class="agent big">{agent}</div>
            <p class="hint">
                Recuerda este nombre, ya que será el que uses para entrar a tu panel de misiones.
            </p>
            <form action="/" method="get">
                <button class="success">OK</button>
            </form>
        </div>
        """)

    def page_agent(self, state):
        agent = parse_qs(self.path.split("?")[1]).get("name", [""])[0]
        data = state["agents"].get(agent)
        if not data:
            self.redirect("/")
            return

        cards = "".join(
            f"<div class='card mission {m['status']}' onclick='toggle({i})'>{m['text']}</div>"
            for i, m in enumerate(data["missions"])
        )

        self.html(f"""
        <h2>Agente {agent}</h2>
        <p class="hint">Pulsa sobre una misión para marcar su progreso</p>
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

    def page_admin_start(self):
        self.html("""
        <h2>Admin</h2>
        <div class="panel">
            <form method="post" action="/start">
                <button>Nueva Partida</button>
            </form>
        </div>
        """)

    def page_admin(self, state):
        if not state["players"]:
            players_html = "<p class='empty'>Todavía no hay jugadores registrados</p>"
        else:
            players_html = "".join(
                f"<div class='player' onclick=\"openModal('{p}')\">{p}</div>"
                for p in state["players"]
            )

        modals = ""
        for player, agent in state["players"].items():
            cards = "".join(
                f"<div class='card mission {m['status']}'>{m['text']}</div>"
                for m in state["agents"][agent]["missions"]
            )
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
        <div class="panel list">{players_html}</div>
        {modals}
        <div class="panel">
            <button class="danger" onclick="openEnd()">Terminar Partida</button>
        </div>

        <div id="end-modal" class="modal">
            <div class="modal-content">
                <h3>¿Terminar partida?</h3>
                <form method="post" action="/end">
                    <button class="success">OK</button>
                </form>
                <button class="danger" onclick="closeEnd()">Cancelar</button>
            </div>
        </div>

        <script>
        function openModal(p){{document.getElementById("modal-"+p).style.display="flex";}}
        function closeModal(p){{document.getElementById("modal-"+p).style.display="none";}}
        function openEnd(){{document.getElementById("end-modal").style.display="flex";}}
        function closeEnd(){{document.getElementById("end-modal").style.display="none";}}
        </script>
        """)

    # -------------------------
    # HTML base
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
<style>
* {{ box-sizing:border-box; }}
body {{
    background:#bfe9ff;
    font-family:system-ui, sans-serif;
    text-align:center;
    padding:20px;
    margin:0;
    color:#033;
}}
h1 {{
    font-size:48px;
    letter-spacing:4px;
    color:#045;
    margin-bottom:8px;
}}
h2 {{ margin-bottom:8px; }}
.panel {{
    background:rgba(255,255,255,0.9);
    border-radius:32px;
    padding:24px;
    margin:20px auto;
    max-width:520px;
    box-shadow:0 20px 40px rgba(0,0,0,0.12);
}}
input, button {{
    width:100%;
    max-width:420px;
    padding:14px;
    border-radius:24px;
    border:none;
    margin:10px auto;
    font-size:18px;
}}
button {{
    background:#1b8cff;
    color:white;
    font-weight:600;
}}
.success {{ background:#2ecc71; }}
.danger {{ background:#e74c3c; }}

.card {{
    background:white;
    border-radius:22px;
    padding:18px;
    margin:14px 0;
    box-shadow:
        0 4px 8px rgba(0,0,0,0.08),
        0 12px 20px rgba(0,0,0,0.06);
}}

.completed {{ background:#b9f3d0; }}
.failed {{ background:#f7b4b4; }}

.player {{
    background:#e9f7ff;
    padding:14px;
    border-radius:20px;
    margin:10px 0;
    cursor:pointer;
    box-shadow:0 6px 14px rgba(0,0,0,0.08);
}}

.modal {{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,0.4);
    display:none;
    align-items:center;
    justify-content:center;
    z-index:1000;
}}

.modal-content {{
    background:white;
    border-radius:32px;
    padding:24px;
    max-width:520px;
    width:90%;
    max-height:80vh;
    overflow-y:auto;
}}

.agent {{
    font-size:36px;
    margin:16px 0;
}}

.agent.big {{
    font-size:48px;
    font-weight:700;
}}

.subtitle {{
    opacity:0.7;
    margin-bottom:16px;
}}

.hint {{
    font-size:14px;
    opacity:0.75;
    margin-bottom:12px;
}}

.empty {{
    color:#555;
    font-style:italic;
}}

.error {{ color:#c00; }}
.link {{ color:#045; }}
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
