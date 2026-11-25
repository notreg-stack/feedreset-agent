# FeedReset

**Tire do feed o que prende você contra a sua vontade. Abra espaço para o que você quer cultivar na vida.** Sua IA examina o Instagram, o YouTube, o TikTok ou o X, faz perguntas para descobrir o que entraria no lugar e procura conteúdo que ajude você a pôr essa escolha em prática.

## Comece com esta mensagem

> Abra https://github.com/notreg-stack/feedreset-agent e siga skills/feedreset/SKILL.md. Identifique o que me prende e eu gostaria de cortar. Me ajude, com perguntas, a descobrir o que vale cultivar no lugar, mesmo que hoje isso nem apareça nas minhas redes. Procure fontes concretas para a minha resposta, aplique minhas escolhas onde tiver acesso e cuide delas diariamente.

No Codex ou Claude Code, abra a pasta do projeto. Em um chat como Grok ou Claude, você pode anexar o arquivo da skill e a pasta `references`. Se o chat não enxerga seu iPhone, bastam algumas capturas consecutivas da página inicial para começar. Você pode ocultar nomes, mensagens e notificações.

## Como a conversa muda o resultado

> **Agente:** “Vi rumores de contratação voltando ao seu feed. Quando você continua vendo esses vídeos, o que acaba deixando para depois?”
>
> **Pessoa:** “Queria fazer mais coisas com minha filha. Só não sei o quê.”
>
> **Agente:** “Você sente mais falta de conversar com calma ou de fazer algo juntos?”
>
> **Pessoa:** “De fazer algo juntos. Ela sempre pede para cozinhar comigo. Podíamos fazer o café de sábado.”

Nesse exemplo, o agente passa a cortar os rumores e procura uma receita que os dois consigam preparar juntos. Encontra uma em que a filha pode medir os ingredientes e misturar a massa. Na revisão seguinte, a pergunta é “Vocês conseguiram fazer o café juntos?”. [Receita usada na demonstração](https://www.jamieoliver.com/recipes/healthy-breakfast-ideas/buddys-one-cup-pancakes/) · [Guia da entrevista](skills/feedreset/references/interview.md)

## O que acontece depois

- O agente registra suas escolhas por rede e conta. Um clique acidental não muda uma preferência explícita.
- Com acesso compatível, ele aplica as ações autorizadas e verifica o resultado. No iPhone, agrupa em uma mensagem os ajustes que precisam de um toque seu.
- No YouTube, pode propor remover um vídeo específico do histórico. No Instagram e no TikTok, uma redefinição ampla começa com a sua decisão sobre aquela conta.
- A revisão diária mede uma nova amostra, mostra o que reapareceu e sugere conteúdo concreto para ocupar esse espaço. Se uma rede estiver inacessível, o relatório identifica a pendência.

**Experimente sem conectar contas** com `python3 demo.py` na pasta do projeto. Os cinco itens são fictícios. Para agendar no computador, siga o exemplo do [guia de execução](README.md#what-happens-tomorrow). [Baixar a skill](https://github.com/notreg-stack/feedreset-agent/releases/latest) · [Controles por rede](skills/feedreset/references/platforms.md)
