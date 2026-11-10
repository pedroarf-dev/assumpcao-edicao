# Implantação no VPS (Hostinger, projeto Docker "assumpcao-editor")

Dois contêineres:
- **editor** (python:3.11-slim): instala ffmpeg, Auto-Editor e faster-whisper na partida, clona este repositório em `/cache/app` (atualiza com `git pull` a cada reinício), baixa o modelo `small` e roda `edicao/vigia.py`.
- **sync** (rclone): a cada 60 s copia vídeos novos de `01 Brutos` (Drive, pasta Videos sincronizada do PC) para `/dados/entrada`, devolve `/dados/prontos` para `02 Prontos` e traz a assinatura e o som de `04 Acervo/Marca`.

Dados no VPS: `/opt/assumpcao/dados` (entrada, prontos, usados, marca, processados.txt) e `/opt/assumpcao/cache` (pip, modelo, código).

Variável que o Pedro coloca no painel (nunca no repositório): `GDRIVE_TOKEN` (saída de `rclone authorize "drive"`).
Para atualizar o código: push no GitHub + "Restart" do projeto no painel.
