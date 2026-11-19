import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
from werkzeug.security import check_password_hash
from hashlib import md5
from dotenv import load_dotenv
from functools import wraps
from database import consultar, executar, conectar_banco

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=30)

def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)

    return verificar

@app.route("/")
def login():
    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    return render_template("login.html")

@app.route("/login", methods=["POST"])
def entrar():
    email = request.form["email"]
    senha = request.form["senha"]
    usuario = consultar(
        "SELECT * FROM usuario WHERE email = %s",
        (email,)
    )

    if usuario and check_password_hash(usuario[0]["senha"], senha):
        session.clear()
        session.permanent = True
        session["usuario_id"] = usuario[0]["id"]
        session["usuario_nome"] = usuario[0]["nome"]
        return redirect(url_for("inicio"))
    flash("E-mail ou senha incorretos.")

    return redirect(url_for("login"))

@app.route("/inicio")
@login_obrigatorio
def inicio():
    return render_template(
        "inicio.html",
        usuario=session["usuario_nome"]
    )

@app.route("/sair")
@login_obrigatorio
def sair():
    session.clear()
    return redirect(url_for("login"))

@app.route("/tutores")
@login_obrigatorio
def tutores():
    busca = request.args.get("busca", "").strip()
    cpf_busca = re.sub(r"\D", "", busca)
    cpf_hash = md5(cpf_busca.encode()).hexdigest() if len(cpf_busca) == 11 else ""
    lista = consultar("""
        SELECT id, nome, telefone, email
        FROM tutores
        WHERE nome ILIKE %s
        OR telefone ILIKE %s
        OR email ILIKE %s
        OR cpf = %s
        ORDER BY nome
    """, (
        f"%{busca}%",
        f"%{busca}%",
        f"%{busca}%",
        cpf_hash
    ))

    return render_template(
        "tutores.html",
        tutores=lista,
        busca=busca
    )

@app.route("/tutores/cadastrar", methods=["GET", "POST"])
@login_obrigatorio
def cadastrar_tutor():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        cpf = re.sub(r"\D", "", request.form["cpf"])
        telefone = request.form["telefone"].strip()
        email = request.form["email"].strip()

        if len(cpf) != 11:
            flash("O CPF deve conter 11 números.")
            return redirect(url_for("cadastrar_tutor"))
        cpf = md5(cpf.encode()).hexdigest()

        try:
            executar("""
                INSERT INTO tutores (nome, cpf, telefone, email)
                VALUES (%s, %s, %s, %s)
            """, (nome, cpf, telefone, email))

            flash("Tutor cadastrado com sucesso!")
            return redirect(url_for("tutores"))

        except Exception:
            flash("Não foi possível cadastrar. Verifique se o CPF já existe.")

    return render_template("formulario_tutor.html", tutor=None)

@app.route("/tutores/editar/<int:id>", methods=["GET", "POST"])
@login_obrigatorio
def editar_tutor(id):
    tutor = consultar(
        "SELECT * FROM tutores WHERE id = %s",
        (id,)
    )

    if not tutor:
        flash("Tutor não encontrado.")
        return redirect(url_for("tutores"))

    if request.method == "POST":
        nome = request.form["nome"].strip()
        cpf = re.sub(r"\D", "", request.form.get("cpf", ""))
        telefone = request.form["telefone"].strip()
        email = request.form["email"].strip()

        if cpf:
            if len(cpf) != 11:
                flash("O CPF deve conter 11 números.")
                return render_template(
                    "formulario_tutor.html",
                    tutor=tutor[0]
                )
            cpf = md5(cpf.encode()).hexdigest()
        else:
            cpf = tutor[0]["cpf"]

        try:
            executar("""
                UPDATE tutores
                SET nome = %s, cpf = %s, telefone = %s, email = %s
                WHERE id = %s
            """, (nome, cpf, telefone, email, id))
            flash("Tutor atualizado com sucesso!")
            return redirect(url_for("tutores"))
        except Exception:
            flash("Não foi possível atualizar o tutor.")

    return render_template(
        "formulario_tutor.html",
        tutor=tutor[0]
    )

@app.route("/tutores/excluir/<int:id>", methods=["POST"])
@login_obrigatorio
def excluir_tutor(id):
    tutor = consultar(
        "SELECT id FROM tutores WHERE id = %s",
        (id,)
    )

    if not tutor:
        flash("Tutor não encontrado.")
        return redirect(url_for("tutores"))
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            DELETE FROM agendamentos
            WHERE pet_id IN (
                SELECT id FROM pet WHERE tutor_id = %s
            )
        """, (id,))
        cursor.execute(
            "DELETE FROM pet WHERE tutor_id = %s",
            (id,)
        )
        cursor.execute(
            "DELETE FROM tutores WHERE id = %s",
            (id,)
        )
        conexao.commit()
        flash("Tutor e seus pets foram excluídos com sucesso!")

    except Exception:
        conexao.rollback()
        flash("Não foi possível excluir o tutor.")

    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for("tutores"))

@app.route("/pets", methods=["GET", "POST"])
@login_obrigatorio
def pets():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        especie = request.form["especie"]
        raca = request.form["raca"].strip()
        idade = request.form["idade"]
        tutor_id = request.form["tutor_id"]

        if not tutor_id:
            flash("Selecione um tutor.")
            return redirect(url_for("pets"))

        try:
            idade = int(idade)
            tutor_id = int(tutor_id)

            if idade < 0:
                flash("A idade não pode ser negativa.")
                return redirect(url_for("pets"))
            executar("""
                INSERT INTO pet (nome, especie, raca, idade, tutor_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, especie, raca, idade, tutor_id))
            flash("Pet cadastrado com sucesso!")

        except Exception:
            flash("Não foi possível cadastrar o pet. Verifique os dados.")

        return redirect(url_for("pets"))

    lista = consultar("""
        SELECT pet.*, tutores.nome AS tutor_nome
        FROM pet
        INNER JOIN tutores ON pet.tutor_id = tutores.id
        ORDER BY pet.nome
    """)
    tutores_lista = consultar("""
        SELECT id, nome
        FROM tutores
        ORDER BY nome
    """)

    return render_template(
        "pets.html",
        pets=lista,
        tutores=tutores_lista,
        mostrar_formulario=request.args.get("novo") == "1"
    )

@app.route("/agendamentos", methods=["GET", "POST"])
@login_obrigatorio
def agendamentos():
    if request.method == "POST":
        data = request.form["data"]
        horario = request.form["horario"]
        motivo = request.form["motivo"].strip()
        pet_id = request.form["pet_id"]

        try:
            pet_id = int(pet_id)

            executar("""
                INSERT INTO agendamentos (data, horario, motivo, pet_id)
                VALUES (%s, %s, %s, %s)
            """, (data, horario, motivo, pet_id))
            flash("Agendamento cadastrado com sucesso!")

        except Exception:
            flash("Não foi possível cadastrar o agendamento.")

        return redirect(url_for("agendamentos"))

    lista = consultar("""
        SELECT
            agendamentos.id,
            agendamentos.data,
            agendamentos.horario,
            agendamentos.motivo,
            pet.nome AS pet_nome,
            pet.especie,
            pet.raca,
            pet.idade,
            tutores.nome AS tutor_nome,
            tutores.telefone,
            tutores.email
        FROM agendamentos
        INNER JOIN pet ON agendamentos.pet_id = pet.id
        INNER JOIN tutores ON pet.tutor_id = tutores.id
        ORDER BY EXTRACT(MONTH FROM agendamentos.data),
                 agendamentos.data,
                 agendamentos.horario
    """)
    pets_lista = consultar("""
        SELECT id, nome
        FROM pet
        ORDER BY nome
    """)

    return render_template(
        "agendamentos.html",
        agendamentos=lista,
        pets=pets_lista,
        mostrar_formulario=request.args.get("novo") == "1"
    )

@app.route("/agendamentos/editar/<int:id>", methods=["POST"])
@login_obrigatorio
def editar_agendamento(id):
    data = request.form["data"]

    try:
        executar("""
            UPDATE agendamentos
            SET data = %s
            WHERE id = %s
        """, (data, id))

        flash("Data do agendamento atualizada com sucesso!")

    except Exception:
        flash("Não foi possível atualizar a data.")

    return redirect(url_for("agendamentos"))

if __name__ == "__main__":
    app.run(debug=True)