import tempfile
from pathlib import Path
from openai import AsyncOpenAI
from database import get_settings


async def transcrever_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Recebe bytes de áudio e retorna transcrição em PT-BR via Whisper.
    """
    settings = get_settings()
    cliente = AsyncOpenAI(api_key=settings.openai_api_key)

    # Salva áudio em arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcricao = await cliente.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                response_format="text"
            )
        return transcricao.strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)
