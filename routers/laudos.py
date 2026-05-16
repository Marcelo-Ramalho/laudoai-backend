from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from database import get_supabase
from services.whisper import transcrever_audio
from services.ia import processar_anomalia

router = APIRouter(prefix="/laudos", tags=["laudos"])


# ─── MODELS ───────────────────────────────────────────────

class LaudoCreate(BaseModel):
    user_id: str
    titulo: Optional[str] = None
    tipo: Optional[str] = "Vistoria Predial"
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_contato: Optional[str] = None
    data_vistoria: Optional[date] = None


class LaudoUpdate(BaseModel):
    titulo: Optional[str] = None
    status: Optional[str] = None
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None


class ItemCreate(BaseModel):
    laudo_id: str
    comodo: str
    transcricao: str
    ordem: Optional[int] = 0


# ─── LAUDOS ───────────────────────────────────────────────

@router.post("/")
async def criar_laudo(laudo: LaudoCreate):
    """Cria um novo laudo em rascunho."""
    sb = get_supabase()
    data = laudo.model_dump(exclude_none=True)

    # Gera número do laudo automaticamente
    from datetime import datetime
    data["numero"] = f"LT-{datetime.now().strftime('%Y-%m%d-%H%M%S')}"
    data["status"] = "rascunho"

    res = sb.table("laudos").insert(data).execute()
    if not res.data:
        raise HTTPException(500, "Erro ao criar laudo")
    return res.data[0]


@router.get("/{laudo_id}")
async def buscar_laudo(laudo_id: str):
    """Busca laudo por ID com todos os itens."""
    sb = get_supabase()
    res = sb.table("laudos").select("*, itens_laudo(*)").eq("id", laudo_id).execute()
    if not res.data:
        raise HTTPException(404, "Laudo não encontrado")
    return res.data[0]


@router.get("/user/{user_id}")
async def listar_laudos(user_id: str):
    """Lista todos os laudos de um engenheiro."""
    sb = get_supabase()
    res = sb.table("laudos").select("*").eq("user_id", user_id).order("criado_em", desc=True).execute()
    return res.data


@router.patch("/{laudo_id}")
async def atualizar_laudo(laudo_id: str, laudo: LaudoUpdate):
    """Atualiza campos do laudo."""
    sb = get_supabase()
    data = laudo.model_dump(exclude_none=True)
    res = sb.table("laudos").update(data).eq("id", laudo_id).execute()
    if not res.data:
        raise HTTPException(404, "Laudo não encontrado")
    return res.data[0]


@router.delete("/{laudo_id}")
async def deletar_laudo(laudo_id: str):
    """Deleta laudo e todos os itens associados."""
    sb = get_supabase()
    sb.table("laudos").delete().eq("id", laudo_id).execute()
    return {"ok": True}


# ─── ITENS DO LAUDO ───────────────────────────────────────

@router.post("/{laudo_id}/itens/voz")
async def adicionar_item_por_voz(
    laudo_id: str,
    comodo: str = Form(...),
    ordem: int = Form(0),
    audio: UploadFile = File(...)
):
    """
    Recebe áudio, transcreve com Whisper,
    busca no banco de patologias ou chama Claude,
    salva o item no Supabase.
    """
    sb = get_supabase()

    # 1. Transcreve o áudio
    audio_bytes = await audio.read()
    transcricao = await transcrever_audio(audio_bytes, audio.filename)

    # 2. Busca no banco de patologias ou chama Claude
    anomalia = await processar_anomalia(transcricao, comodo)

    # 3. Salva o item no banco
    item = {
        "laudo_id": laudo_id,
        "comodo": comodo,
        "ordem": ordem,
        "transcricao": transcricao,
        "titulo": anomalia.get("titulo"),
        "descricao_tecnica": anomalia.get("descricao_tecnica"),
        "urgencia": anomalia.get("urgencia"),
        "norma_abnt": anomalia.get("norma_abnt"),
        "recomendacao": anomalia.get("recomendacao"),
        "patologia_id": anomalia.get("patologia_id"),
        "foto_urls": [],
    }

    res = sb.table("itens_laudo").insert(item).execute()
    if not res.data:
        raise HTTPException(500, "Erro ao salvar item")

    return {
        "item": res.data[0],
        "fonte": anomalia.get("fonte"),  # "banco" ou "claude"
        "transcricao": transcricao,
    }


@router.post("/{laudo_id}/itens/texto")
async def adicionar_item_por_texto(item: ItemCreate):
    """
    Versão sem áudio — recebe transcrição diretamente.
    Útil pra testes e modo offline.
    """
    sb = get_supabase()
    anomalia = await processar_anomalia(item.transcricao, item.comodo)

    novo_item = {
        "laudo_id": item.laudo_id,
        "comodo": item.comodo,
        "ordem": item.ordem,
        "transcricao": item.transcricao,
        "titulo": anomalia.get("titulo"),
        "descricao_tecnica": anomalia.get("descricao_tecnica"),
        "urgencia": anomalia.get("urgencia"),
        "norma_abnt": anomalia.get("norma_abnt"),
        "recomendacao": anomalia.get("recomendacao"),
        "patologia_id": anomalia.get("patologia_id"),
        "foto_urls": [],
    }

    res = sb.table("itens_laudo").insert(novo_item).execute()
    if not res.data:
        raise HTTPException(500, "Erro ao salvar item")

    return {
        "item": res.data[0],
        "fonte": anomalia.get("fonte"),
    }


@router.delete("/{laudo_id}/itens/{item_id}")
async def deletar_item(laudo_id: str, item_id: str):
    """Deleta um item do laudo."""
    sb = get_supabase()
    sb.table("itens_laudo").delete().eq("id", item_id).execute()
    return {"ok": True}
