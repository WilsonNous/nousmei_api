from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, validator
from database import get_db_connection
import datetime
import re

app = FastAPI(title="API NousMEI",
              description="API para cadastro de MEIs que desejam receber lembretes do DAS",
              version="1.0.0")

# Configuração de CORS (em produção, restrinja os domínios!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class Interessado(BaseModel):
    nome: constr(min_length=3, max_length=100, strip_whitespace=True)
    email: EmailStr | None = None
    whatsapp: constr(min_length=11, max_length=11)
    cnpj: constr(min_length=14, max_length=14)

    @validator('nome')
    def validate_nome(cls, v):
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', v):
            raise ValueError('Nome deve conter apenas letras e espaços')
        return v.title()

    @validator('whatsapp')
    def validate_whatsapp(cls, v):
        if not v.isdigit():
            raise ValueError('WhatsApp deve conter apenas números')
        if not v.startswith(('55')):
            v = f'55{v}'  # Adiciona código do Brasil se faltar
        return v

    @validator('cnpj')
    def validate_cnpj(cls, v):
        if not v.isdigit():
            raise ValueError('CNPJ deve conter apenas números')
        # Adicione aqui validação de dígitos verificadores se necessário
        return v

@app.get("/", tags=["Health Check"])
async def health_check():
    return {
        "status": "online",
        "versao": "1.0.0",
        "documentacao": "/docs"
    }

@app.post("/cadastrar", 
          status_code=status.HTTP_201_CREATED,
          tags=["Cadastro"],
          summary="Cadastra novo MEI",
          response_description="Cadastro realizado com sucesso")
async def cadastrar(interessado: Interessado):
    """
    Endpoint para cadastro de MEIs que desejam receber lembretes do DAS.
    
    - **nome**: Nome completo (mín. 3 caracteres)
    - **email**: Opcional
    - **whatsapp**: Com DDI brasileiro (55)
    - **cnpj**: 14 dígitos
    """
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
            (nome, email, whatsapp, cnpj, data_cadastro)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
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
        novo_id = cursor.fetchone()['id']
        
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
            detail="Erro interno no servidor"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
