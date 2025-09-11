from flask import Flask, render_template, request, redirect, url_for
from models import Usuario
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from db import db
import hashlib 
from flask import request



app = Flask(__name__)
app.secret_key = 'lancode'
lm = LoginManager(app)
lm.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///database.db'
db.init_app(app)






def hash(txt):
    hash_obj = hashlib.sha256(txt.encode('utf-8'))
    return hash_obj.hexdigest()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        nome = request.form['nomeForm']
        senha = request.form['senhaForm']

        user = db.session.query(Usuario).filter_by(nome=nome, senha=hash(senha)).first()
        if user:
            login_user(user)
            return redirect(url_for('home'))
        else:
            error = "Nome ou senha incorretos"
    return render_template('login.html', error=error)

@lm.user_loader
def user_loader(id):
    usuario = db.session.query(Usuario).filter_by(id=id).first()
    return usuario

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        nome = request.form['nomeForm']
        senha = request.form['senhaForm']

        # Verifica se já existe usuário com este nome
        usuario_existente = db.session.query(Usuario).filter_by(nome=nome).first()
        if usuario_existente:
            error = "Esse nome já esta sendo usado"
            return render_template('registrar.html', error=error)
        
        novo_usuario = Usuario(nome=nome, senha=hash(senha))
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)

        return redirect(url_for('home'))
    return render_template('registrar.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)