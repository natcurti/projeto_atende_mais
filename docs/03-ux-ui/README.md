# Entrega 3 — UX/UI, usabilidade e navegação

Esta entrega transforma os wireframes da Entrega 2 em um **protótipo navegável** com identidade visual
e registra as decisões de experiência do usuário (UX) do atende+.

**Protótipo online:** https://natcurti.github.io/projeto_atende_mais/03-ux-ui/prototipo/

O protótipo é feito em HTML e CSS, abre em qualquer navegador e usa dados fictícios. Nada é salvo.

## 1. Como navegar pelo protótipo

Na tela inicial, use os atalhos **Entrar como cliente**, **Entrar como atendente** ou **Entrar como administrador**.
Sugestão de roteiro para a apresentação (cerca de 3 minutos):

1. **Cliente:** entre como cliente, clique em *Abrir ticket*, tente enviar o formulário vazio (o navegador indica os campos obrigatórios), preencha e envie. O sistema volta para *Meus tickets* com a confirmação.
2. **Cliente:** abra o ticket *#1042* para ver a conversa. Depois volte e abra o *#1031* (resolvido) para avaliar com estrelas ou reabrir.
3. **Atendente:** saia, entre como atendente e veja a fila com o ticket atrasado em destaque. Clique em *Assumir*.
4. **Atendente:** abra o *#1042*, troque para *Nota interna* e veja o campo mudar de cor. Altere a prioridade no painel *Gerenciar ticket*.
5. **Administrador:** saia, entre como administrador e note o menu extra *Administração*, com equipe e categorias.

| Tela | Arquivo | Perfil |
| --- | --- | --- |
| Entrada (login e cadastro) | `index.html` | Todos |
| Meus tickets | `cliente-tickets.html` | Cliente |
| Abrir ticket | `cliente-novo-ticket.html` | Cliente |
| Ticket em atendimento | `cliente-ticket.html` | Cliente |
| Ticket resolvido (avaliar ou reabrir) | `cliente-ticket-resolvido.html` | Cliente |
| Fila de atendimento | `equipe-fila.html` | Atendente, Administrador |
| Ticket na visão da equipe | `equipe-ticket.html` | Atendente, Administrador |
| Administração | `admin.html` | Administrador |
| Guia de estilo | `guia-de-estilo.html` | Referência visual |

## 2. Princípios de experiência

As decisões de UX partem de uma pergunta para cada perfil:

| Perfil | Pergunta que a tela precisa responder | Como o atende+ responde |
| --- | --- | --- |
| Cliente | "Meu problema está andando?" | A situação de cada ticket aparece em destaque, com cor e nome. A conversa mostra quem respondeu e quando. |
| Atendente | "O que eu atendo agora?" | A fila já vem ordenada: atrasados primeiro, depois o prazo mais próximo. Assumir é um clique. |
| Administrador | "A equipe está dando conta?" | Os contadores no topo da fila mostram o volume por situação. O painel de indicadores (RF18) vem depois do MVP. |

Princípios aplicados em todas as telas:

- **Situação sempre visível:** todo ticket mostra sua situação em uma etiqueta colorida com o nome escrito.
- **Uma ação principal por tela:** só um botão preenchido (petróleo) por tela, para a ação mais provável.
- **Linguagem do cliente:** termos simples como "Abrir ticket", "Responder" e "Reabrir ticket", sem jargão técnico.
- **Confirmação de toda ação:** depois de enviar, salvar ou assumir, aparece um aviso dizendo o que aconteceu.
- **Nada some:** pessoas e categorias são desativadas, nunca excluídas (RN12), e toda mudança vira um evento na conversa (RN13).

## 3. Identidade visual

O guia completo está em [`prototipo/guia-de-estilo.html`](prototipo/guia-de-estilo.html), e todos os valores ficam
como variáveis CSS em [`prototipo/assets/style.css`](prototipo/assets/style.css), prontos para uso nos templates do Django.

| Elemento | Escolha | Motivo |
| --- | --- | --- |
| Cor principal | Petróleo `#0F5E6E` | Transmite confiança e se diferencia do azul padrão de sistemas. Contraste de 7,4:1 com branco. |
| Cor de destaque | Sinal `#F2B705` | Usada só no "+" da marca e nas notas internas, como um post-it da equipe. |
| Fundo | Papel `#F3F6F6` | Cinza levemente frio, para os painéis brancos se destacarem sem sombras. |
| Fonte | Atkinson Hyperlegible | Criada pelo Braille Institute para máxima legibilidade, inclusive para pessoas com baixa visão. |
| Situações | 6 cores (aberto, em atendimento, aguardando, resolvido, fechado, atrasado) | Cada situação tem cor própria, mas o nome sempre aparece escrito. |
| Prioridade | Barras de 1 a 4 + nome | A intensidade é lida de relance; "Urgente" ganha vermelho. |

Na conversa do ticket, a posição e a cor indicam quem falou: o **cliente** à esquerda em branco,
a **equipe** à direita em petróleo claro, a **nota interna** em amarelo com borda tracejada, ocupando a largura toda,
e os **eventos automáticos** como linhas discretas entre as mensagens.

## 4. Navegação

- Depois do login, cada perfil cai na sua tela inicial: o cliente em *Meus tickets*; atendente e administrador na *Fila*.
- O menu do topo tem no máximo dois itens por perfil, e a página atual fica destacada em branco.
- Toda tela de detalhe tem o link *Voltar* para a lista de origem.
- O cliente abre um ticket em **2 cliques** a partir da tela inicial (menu *Abrir ticket* e botão *Enviar ticket*), o que atende o RNF05 (máximo de 3).

O mapa completo de telas e caminhos está no fluxo da [Entrega 2](../02-wireframes/README.md).

## 5. Usabilidade: heurísticas de Nielsen

| Heurística | Onde aparece no atende+ |
| --- | --- |
| Visibilidade do estado do sistema | Etiquetas de situação, contadores da fila, avisos de confirmação após cada ação |
| Correspondência com o mundo real | "Ticket", "Fila", "Assumir", "Reabrir": termos usados no dia a dia do suporte |
| Controle e liberdade do usuário | Botão *Cancelar* no formulário, link *Voltar* nos detalhes, *Reabrir ticket* por 7 dias |
| Consistência e padrões | Mesmo topo, mesmos botões e mesmas cores de situação em todas as telas |
| Prevenção de erros | Campos obrigatórios marcados com *, validação antes de enviar, tipos de arquivo limitados |
| Reconhecer em vez de lembrar | Filtros em listas de opções, prazo exibido junto da prioridade, nome do cliente na fila |
| Flexibilidade e eficiência | Busca por número ou título, filtros combináveis, *Assumir* direto da fila |
| Design estético e minimalista | Só as informações necessárias para cada perfil; detalhes extras ficam na lateral |
| Ajuda a reconhecer e corrigir erros | Mensagens do navegador indicam qual campo falta; dicas abaixo dos campos explicam o formato |
| Ajuda e documentação | Dicas no formulário de abertura e o painel "O que acontece depois" |

## 6. Acessibilidade e responsividade

- Contraste de texto de pelo menos 4,5:1 em todas as combinações usadas (padrão WCAG AA). A menor delas é a etiqueta *Resolvido*, com 5,6:1.
- Cor nunca é a única informação: situações e prioridades sempre têm texto.
- Todo campo tem rótulo (`<label>`) ligado a ele, e as dicas são lidas por leitores de tela (`aria-describedby`).
- Botões e áreas clicáveis têm pelo menos 44 px de altura, e o foco do teclado aparece como contorno petróleo.
- Em telas de até 640 px, o menu e o usuário se reorganizam, as colunas viram uma só e as tabelas rolam na horizontal (RNF06).

## 7. O que mudou em relação aos wireframes

- **Menu da equipe:** "Meus atendimentos" virou a opção *Comigo* no filtro de atendente, e o "Painel" saiu do menu até ser construído (RF18, pós-MVP).
- **Tela de ticket resolvido:** avaliação e reabertura ganharam uma tela própria, em vez de uma anotação.
- **Gerenciar ticket:** a prioridade mostra o prazo correspondente (ex.: "Média (3 dias)"), para o atendente não precisar decorar a regra RN09.
- **Ações na administração:** "Adicionar pessoa" substituiu "Novo usuário", mais próximo da linguagem do administrador.

## 8. Limitações do protótipo

- Os dados são fixos: enviar um formulário mostra a confirmação, mas não cria nada.
- Todos os títulos da fila abrem o mesmo ticket (#1042), como exemplo de detalhe.
- Busca, filtros e o envio de anexos aparecem na tela, mas ainda não funcionam. Isso é implementado no Django a partir do MVP.
