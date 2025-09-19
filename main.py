from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from cryptography.fernet import Fernet

# ======== CRIPTOGRAFIA =========
with open("fernet.key", "rb") as f:
    FERNET_KEY = f.read().strip()
fernet = Fernet(FERNET_KEY)

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_MENSAGENS = "mensagens.json"

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {}
    try:
        with open(ARQUIVO_USUARIOS, "rb") as f:
            data = f.read()
        decrypted = fernet.decrypt(data)
        return json.loads(decrypted.decode("utf-8"))
    except Exception:
        return {}

def salvar_usuarios(users):
    data = json.dumps(users, indent=2, ensure_ascii=False).encode("utf-8")
    encrypted = fernet.encrypt(data)
    with open(ARQUIVO_USUARIOS, "wb") as f:
        f.write(encrypted)

def carregar_mensagens():
    if not os.path.exists(ARQUIVO_MENSAGENS):
        return []
    try:
        with open(ARQUIVO_MENSAGENS, "rb") as f:
            data = f.read()
        decrypted = fernet.decrypt(data)
        return json.loads(decrypted.decode("utf-8"))
    except Exception:
        return []

def salvar_mensagens(mensagens):
    data = json.dumps(mensagens, indent=2, ensure_ascii=False).encode("utf-8")
    encrypted = fernet.encrypt(data)
    with open(ARQUIVO_MENSAGENS, "wb") as f:
        f.write(encrypted)

# ======== FLASK APP ==========
app = Flask(__name__)
app.secret_key = "chave-super-secreta"

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, nome):
        self.id = nome
        self.nome = nome

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    usuarios = carregar_usuarios()
    if user_id in usuarios:
        return User(user_id)
    return None

@app.route("/", methods=["GET", "POST"])
def home():
    mensagens = carregar_mensagens()
    if request.method == "POST" and current_user.is_authenticated:
        conteudo = request.form["conteudo"]
        novo_id = (max([m["id"] for m in mensagens], default=0)) + 1
        mensagens.append({
            "id": novo_id,
            "autor": current_user.nome,
            "conteudo": conteudo,
        })
        salvar_mensagens(mensagens)
        return redirect(url_for("home"))
    return render_template("home.html", mensagens=mensagens[::-1])

@app.route("/deletar_mensagem/<int:msg_id>", methods=["POST"])
@login_required
def deletar_mensagem(msg_id):
    mensagens = carregar_mensagens()
    mensagens = [m for m in mensagens if not (m["id"] == msg_id and m["autor"] == current_user.nome)]
    salvar_mensagens(mensagens)
    return redirect(url_for("home"))

@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        nome = request.form["nomeForm"]
        senha = request.form["senhaForm"]
        usuarios = carregar_usuarios()
        user = usuarios.get(nome)
        if user:
            try:
                senha_salva = fernet.decrypt(user["senha"].encode()).decode()
                if senha_salva == senha:
                    login_user(User(nome))
                    return redirect(url_for("home"))
            except Exception:
                pass
        error = "Usuário ou senha inválidos."
    return render_template("login.html", error=error)

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    error = None
    if request.method == "GET":
        return render_template("registrar.html", error=error)
    elif request.method == "POST":
        nome = request.form["nomeForm"]
        senha = request.form["senhaForm"]
        usuarios = carregar_usuarios()
        if nome in usuarios:
            error = "Usuário já existe."
            return render_template("registrar.html", error=error)
        # Criptografa a senha
        senha_cripto = fernet.encrypt(senha.encode()).decode()
        usuarios[nome] = {"senha": senha_cripto}
        salvar_usuarios(usuarios)
        return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)