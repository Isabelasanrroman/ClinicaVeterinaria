import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def conectar_banco():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def consultar(sql, valores=()):
    conexao = conectar_banco()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, valores)
    resultado = cursor.fetchall()
    cursor.close()
    conexao.close()

    return resultado

def executar(sql, valores=()):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute(sql, valores)
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()
