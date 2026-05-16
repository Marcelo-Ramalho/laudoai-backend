from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_supabase

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    nome: str
    email: str
    crea: Optional[str] = None
    especialidade: Optional[str] = None
    telefone: Optional[str] = None


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    crea: Optional[str] = None
    especialidade: Optional[str] = None
    telefone: Optional[str] = None
    logo_url: Optional[str] = None
    assinatura_url: Optional[str] = None
    plano: Optional[str] = None


@router.post("/")
async def criar_user(user: UserCreate):
    """Cria um novo engenheiro."""
    sb = get_supabase()
    res = sb.table("users").insert(user.model_dump(exclude_none=True)).execute()
    if not res.data:
        raise HTTPException(500, "Erro ao criar usuário")
    return res.data[0]


@router.get("/{user_id}")
async def buscar_user(user_id: str):
    """Busca engenheiro por ID."""
    sb = get_supabase()
    res = sb.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(404, "Usuário não encontrado")
    return res.data[0]


@router.get("/email/{email}")
async def buscar_user_por_email(email: str):
    """Busca engenheiro por email — usado no login Google."""
    sb = get_supabase()
    res = sb.table("users").select("*").eq("email", email).execute()
    if not res.data:
        return None
    return res.data[0]


@router.patch("/{user_id}")
async def atualizar_user(user_id: str, user: UserUpdate):
    """Atualiza perfil do engenheiro."""
    sb = get_supabase()
    data = user.model_dump(exclude_none=True)
    res = sb.table("users").update(data).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(404, "Usuário não encontrado")
    return res.data[0]


@router.delete("/{user_id}")
async def deletar_user(user_id: str):
    """Deleta conta e todos os dados do engenheiro — LGPD."""
    sb = get_supabase()
    sb.table("users").delete().eq("id", user_id).execute()
    return {"ok": True, "mensagem": "Conta e todos os dados removidos conforme LGPD"}
