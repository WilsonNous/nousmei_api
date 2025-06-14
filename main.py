from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, validator
from database import get_db_connection
from datetime import datetime, date
import re

app = FastAPI(
    title="API NousMEI",
    description="API para cadastro de MEIs que desejam receber lembretes do DAS",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://noustecnologia.com.br"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# MODELO DE DADOS
class Interessado(BaseModel):
    nome: constr(min_length=3, max_length=100, strip_whitespace=True)
    email: EmailStr | None = None
    whatsapp: constr(min_length=11, max_length=11)
    cnpj: constr(min_length=14, max_length=14)
    data_vencimento: date | None = None

    @validator('nome')
    def validate_nome(cls, v):
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', v):
            raise ValueError('Nome deve conter apenas letras e espaços')
        return v.title()

    @validator('whatsapp')
    def validate_whatsapp(cls, v):
        if not v.isdigit():
            raise ValueError('WhatsApp deve conter apenas números')
        return v

    @validator('cnpj')
    def validate_cnpj(cls, v):
        if not v.isdigit():
            raise ValueError('CNPJ deve conter apenas números')
        return v


# ENDPOINT DE STATUS
@app.get("/", tags=["Health Check"])
async def health_check():
    return {
        "status": "online",
        "versao": "1.0.0",
        "documentacao": "/docs"
    }


# LISTAR TODOS OS INTERESSADOS
@app.get("/admin/lista")
def listar_interessados():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM interessados_nousmei ORDER BY data_cadastro DESC")
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


# CADASTRAR NOVO INTERESSADO
@app.post("/cadastrar",
          status_code=status.HTTP_201_CREATED,
          tags=["Cadastro"],
          summary="Cadastra novo MEI",
          response_description="Cadastro realizado com sucesso")
async def cadastrar(interessado: Interessado):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verifica duplicidade
        cursor.execute("SELECT id FROM interessados_nousmei WHERE cnpj = %s", (interessado.cnpj,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ já cadastrado"
            )

        sql = """
            INSERT INTO interessados_nousmei 
            (nome, email, whatsapp, cnpj, data_vencimento, data_cadastro)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        valores = (
            interessado.nome,
            interessado.email,
            f"55{interessado.whatsapp}",
            interessado.cnpj,
            interessado.data_vencimento,
            datetime.now()
        )

        cursor.execute(sql, valores)
        novo_id = cursor.lastrowid
        conn.commit()

        return {
            "status": "success",
            "id": novo_id,
            "mensagem": "Cadastro realizado com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no servidor: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
