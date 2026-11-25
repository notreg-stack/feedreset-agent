# FeedReset

Entregue à sua IA uma tarefa diária: manter o feed alinhado com o que você escolheu ver. O agente começa por um diagnóstico do seu Instagram, YouTube, TikTok ou X. Você vê exemplos reais, corrige o julgamento da IA e decide o que incentivar, cortar ou proteger.

## Comece com esta mensagem

> Abra https://github.com/notreg-stack/feedreset-agent e siga skills/feedreset/SKILL.md. Comece pela rede que mais uso. Examine recomendações consecutivas, mostre o que parece construtivo, dispersivo ou incerto e explique com exemplos. Depois me pergunte o que quero incentivar, reduzir ao máximo e sempre preservar. Aplique minhas escolhas e configure a manutenção diária se você puder executá-la.

No Codex ou Claude Code, abra a pasta do projeto. Em um chat como Grok ou Claude, você pode anexar o arquivo da skill e os dois guias da pasta `references`. Se o chat não enxerga seu iPhone, bastam algumas capturas consecutivas da página inicial para começar. Você pode ocultar nomes, mensagens e notificações.

## O que acontece depois

- O agente registra suas escolhas por rede e conta. Um clique acidental não muda uma preferência explícita.
- Com acesso compatível, ele aplica as ações autorizadas e verifica o resultado. No iPhone, agrupa em uma mensagem os ajustes que precisam de um toque seu.
- No YouTube, pode propor remover um vídeo específico do histórico. No Instagram e no TikTok, uma redefinição ampla começa com a sua decisão sobre aquela conta.
- A revisão diária mede uma nova amostra, mostra o que reapareceu e sugere conteúdo concreto para ocupar esse espaço. Se uma rede estiver inacessível, o relatório identifica a pendência.

**Experimente sem conectar contas** com `python3 demo.py` na pasta do projeto. Os cinco itens são fictícios. Para agendar no computador, siga o exemplo do [guia de execução](README.md#what-happens-tomorrow). [Baixar a skill](https://github.com/notreg-stack/feedreset-agent/releases/latest) · [Controles por rede](skills/feedreset/references/platforms.md)
