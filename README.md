# Caça ao Token

Ferramenta pessoal para acompanhar a caçada ao token de Pirate Shop Access no evento Treasure Hunters do Fortnite (de 1º de novembro a 5 de dezembro de 2026).

Ela lê o seu perfil do Fortnite direto da Epic e mostra:

- **Painel:** baús abertos no total, hoje e nesta sessão, ritmo por hora, contagem regressiva para o reset e gráfico por dia.
- **Prêmios da semana:** checklist do pool da semana, marcado sozinho quando o item cai na conta, e o histórico com o número do baú em que cada item caiu.
- **Agenda:** Treasure Hours, Captain's Days, resets e encerramento em horário de Brasília.
- **Calculadora de sorte:** chance de já ter tirado o token em três cenários. A chance real não foi divulgada.
- **Contadores:** todos os números do seu perfil, para escolher qual deles conta os baús.

## Como usar

1. Baixe o `CacaAoToken.exe` em [Releases](../../releases).
2. Abra o arquivo. Na primeira vez, o Windows pode mostrar "O Windows protegeu o computador". Isso acontece porque o arquivo não tem assinatura paga. Clique em **Mais informações** e depois em **Executar assim mesmo**.
3. Em **Conta Epic**, clique em **Abrir página da Epic**, copie o texto que aparecer e cole na ferramenta.
4. Em **Contadores**, abra 1 ou 2 baús no jogo, clique em **Atualizar** e marque a linha que subiu.

A ferramenta atualiza sozinha a cada 90 segundos.

## Privacidade

- O login fica salvo só no seu PC, em `%APPDATA%\CacaAoToken\login.json`. Esse arquivo dá acesso à sua conta: não envie para ninguém.
- A ferramenta só lê o perfil. Ela não compra nem muda nada.
- Ela conversa com a Epic, com o `fortnite-api.com` (para mostrar os nomes dos itens) e com este repositório (para baixar a lista de prêmios).
- **Desconectar** apaga o login do PC e também o remove da sua conta Epic.

Esta ferramenta não é oficial da Epic. Ela usa as mesmas rotas que outros rastreadores da comunidade.

## Atualizar os prêmios da semana

Edite `data/evento.json` aqui no GitHub e adicione os itens em `semanas`. Quem abrir a ferramenta depois recebe a lista nova, sem baixar outra versão.

## Para desenvolver

```bash
pip install -r requirements.txt
python app/main.py              # abre o app (precisa do Windows ou de um sistema com WebView)
python tools/dev_server.py      # testa a tela no navegador com uma conta falsa
python -m unittest discover -s tests
```

Para publicar uma versão nova do .exe, mude `VERSION` em `app/main.py` e envie para a `main`. O GitHub Actions gera o arquivo e coloca em Releases.
