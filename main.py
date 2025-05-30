from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db_connection
import datetime

app = FastAPI()


class Interessado(BaseModel):
    nome: str
    email: str
    whatsapp: str
    cnpj: str


@app.get("/")
def home():
    return {"status": "online"}


@app.post("/cadastrar")
def cadastrar(interessado: Interessado):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO interessados_nousmei (nome, email, whatsapp, cnpj, data_cadastro)
            VALUES (%s, %s, %s, %s, %s)
        """
        valores = (
            interessado.nome,
            interessado.email,
            interessado.whatsapp,
            interessado.cnpj,
            datetime.datetime.now()
        )
        cursor.execute(sql, valores)
        conn.commit()
        return {"status": "ok", "mensagem": "Cadastro realizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
