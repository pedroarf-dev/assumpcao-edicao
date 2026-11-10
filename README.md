# assumpcao-edicao

Robô de edição dos Reels do @assumpcao_pedro (roda no VPS da Hostinger, em Docker).

## O que faz
Bruto em `/dados/entrada` → corta pausas (Auto-Editor) → transcreve em pt (faster-whisper) → gera `.srt`, `.txt`, `.json`, projeto do Premiere → renderiza versão final com legenda (branca, palavra falada em amarelo #FFCC00) e vinheta (assinatura amarela + som da caneta) → resultado em `/dados/prontos/<nome>/`. O bruto vai para `/dados/usados`.

## Pastas
- `edicao/` — `pipeline.py` (um vídeo) e `vigia.py` (loop que vigia a entrada)
- marca (assinatura animada e som) fica fora do repositório, em `/dados/marca` no VPS
- `capas/` — scripts de capa e marcas (identidade 10/11/2026)
- `legado/` — scripts antigos (backup de 09/11/2026)

## Ajustes
Variáveis no `docker-compose.yml`: `WHISPER_MODEL` (small/medium), `CORTE_MARGEM`, `CORTE_LIMIAR`, `INTERVALO`.

## Teste manual
`docker compose run --rm editor python /app/edicao/pipeline.py /dados/entrada/video.mp4 /dados/prontos`
