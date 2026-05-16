import json
import re
from pathlib import Path
from typing import Optional
import anthropic
from database import get_settings

# Carrega banco de patologias em memória — zero custo de API
_banco_patologias = None

def carregar_banco() -> list:
    global _banco_patologias
    if _banco_patologias is None:
        caminho = Path(__file__).parent.parent / "banco_patologias_laudoai_v3.json"
        if caminho.exists():
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                _banco_patologias = data.get("patologias", [])
        else:
            _banco_patologias = []
    return _banco_patologias


def buscar_patologia(transcricao: str) -> Optional[dict]:
    """
    Busca no banco de patologias por palavras-chave.
    Retorna a patologia mais próxima ou None se não encontrar.
    """
    banco = carregar_banco()
    if not banco:
        return None

    palavras = set(re.findall(r'\w+', transcricao.lower()))
    melhor_score = 0
    melhor_patologia = None

    for patologia in banco:
        keywords = set(k.lower() for k in patologia.get("palavras_chave", []))
        if not keywords:
            continue

        # Jaccard entre palavras da transcrição e keywords da patologia
        inter = palavras & keywords
        union = palavras | keywords
        score = len(inter) / len(union) if union else 0

        if score > melhor_score:
            melhor_score = score
            melhor_patologia = patologia

    # Threshold mínimo de 0.10 pra considerar match
    if melhor_score >= 0.10:
        return melhor_patologia

    return None


async def gerar_texto_tecnico(transcricao: str, comodo: str) -> dict:
    """
    Chama o Claude API quando a patologia não está no banco.
    Retorna JSON estruturado com texto técnico.
    """
    settings = get_settings()
    cliente = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    system_prompt = """Você é o motor técnico do LaudoAI, especializado em laudos de vistoria predial brasileiros.

Converta a descrição informal do engenheiro em registro técnico estruturado.

REGRAS:
- Nunca invente medidas não mencionadas
- Use terminologia técnica precisa conforme NBR
- Linguagem formal, impessoal e objetiva
- Classifique urgência: ALTA (risco estrutural/saúde), MÉDIA (pode agravar), BAIXA (estético)

Responda SOMENTE com JSON válido, sem texto fora do JSON:
{
  "titulo": "título técnico curto",
  "descricao_tecnica": "parágrafo técnico formal de 2-3 frases",
  "classificacao": "categoria técnica da patologia",
  "urgencia": "ALTA | MÉDIA | BAIXA",
  "norma_abnt": "NBR XXXXX",
  "recomendacao": "ação técnica em 1 frase",
  "prazo_intervencao_dias": número
}"""

    user_message = f"Cômodo: {comodo}\nDescrição do engenheiro: \"{transcricao}\""

    response = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    text = response.content[0].text
    clean = text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


async def processar_anomalia(transcricao: str, comodo: str) -> dict:
    """
    Fluxo principal:
    1. Busca no banco de patologias (grátis)
    2. Se não achar, chama Claude API
    Retorna dados estruturados da anomalia.
    """
    # Tenta banco primeiro
    patologia = buscar_patologia(transcricao)

    if patologia:
        return {
            "fonte": "banco",
            "titulo": patologia.get("titulo"),
            "descricao_tecnica": patologia.get("descricao_tecnica"),
            "classificacao": patologia.get("subcategoria"),
            "urgencia": patologia.get("urgencia"),
            "norma_abnt": patologia.get("norma_principal"),
            "recomendacao": patologia.get("recomendacao"),
            "prazo_intervencao_dias": patologia.get("prazo_intervencao_dias"),
            "patologia_id": patologia.get("id"),
            "profissional_responsavel": patologia.get("profissional_responsavel"),
        }

    # Não achou no banco — chama Claude
    resultado = await gerar_texto_tecnico(transcricao, comodo)
    resultado["fonte"] = "claude"
    resultado["patologia_id"] = None
    return resultado
