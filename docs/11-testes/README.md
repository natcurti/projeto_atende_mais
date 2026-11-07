# Entrega 8 — Plano e execução de testes

Este documento mostra como o atende+ foi testado:
- o que se testa e como (plano);
- quais casos verificam cada requisito (casos de teste);
- o resultado da rodada final (execução);
- os defeitos encontrados durante o projeto e como foram corrigidos (registro de bugs).

**Resumo da execução de 07/11/2026:**

| O que foi feito | Resultado |
| --- | --- |
| Testes automatizados | 141, todos passando |
| Cobertura do código pelos testes | 96% |
| Testes manuais nas telas | 9 de 9 passando |
| Defeitos registrados no projeto | 12, todos corrigidos. Três deles foram encontrados nesta rodada. |

## 1. Plano de testes

### Objetivo

Confirmar que:
- os 15 requisitos funcionais entregues até a `v0.2.0` funcionam como descrito na [Entrega 1](../01-requisitos/);
- as regras de negócio são respeitadas mesmo quando alguém tenta contorná-las (por exemplo, enviando um formulário alterado);
- cada perfil acessa só o que é seu.

### Escopo

| Entra | Fica de fora (e por quê) |
| --- | --- |
| RF01, RF02, RF04 a RF13, RF16 a RF18 | RF03, RF14, RF15, RF19, RF20, RF21: estão no backlog e ainda não foram construídos |
| RN01 a RN06, RN08 a RN13 | RN07 e RN14 dependem do RF15 e do RF14 |
| RNF03 a RNF08 | RNF01, RNF02 e RNF09 são verificados olhando o repositório; o RNF10 (publicação) é do Checkpoint 5 |

### Níveis e tipos de teste

| Nível | O que verifica | Como |
| --- | --- | --- |
| **Unidade** | Regras isoladas: cálculo do prazo, restrições do banco, validação dos formulários | Testes automatizados do Django |
| **Integração** | As camadas juntas (tela, regra e banco): por exemplo, enviar o formulário de resposta e conferir a situação gravada | Testes automatizados com o cliente de teste do Django, que simula o navegador |
| **Sistema** | O sistema rodando de verdade, como o usuário vê: layout, teclado, celular, páginas de erro | Roteiro manual no navegador (seção 3.2) |
| **Aceitação** | Os critérios de aceite do MVP | Checklist do [Checkpoint 1](../08-mvp/) e o roteiro de demonstração |

Além do comportamento esperado, os testes cobrem três tipos de caso:
- **Negativos:** o que deve ser recusado, como nota 6, um ticket de outra cliente ou um atendente mudando o ticket de um colega.
- **Segurança:** acesso por perfil, proteção contra envio de formulário de outro site (CSRF) e código malicioso digitado num campo (XSS).
- **Desempenho:** tempo das listas com mais de 1.000 tickets.

### Ambiente

| Item | Valor |
| --- | --- |
| Sistema | Linux; os mesmos comandos funcionam no Windows e no macOS |
| Python e Django | Python 3.13 e Django 5.2.19 |
| Banco | SQLite. Os testes automatizados criam e apagam um banco próprio, sem tocar no `db.sqlite3`. |
| Navegador | Chromium, que é a base do Chrome e do Edge, em 360 px, 375 px e 1280 px de largura |
| Dados | `python manage.py carregar_dados_exemplo`: 52 tickets. Para o teste de desempenho, 1.100 tickets. |

### Critérios

- **Para começar:** o código instala do zero com `pip install -r requirements.txt` e roda com `migrate`.
- **Para encerrar:** todos os testes automatizados passam, nenhum defeito fica aberto, e cada requisito do escopo tem pelo menos um caso de teste.
- **Gravidade dos defeitos:**

| Gravidade | Definição |
| --- | --- |
| Alta | Impede o uso ou quebra uma regra de negócio |
| Média | Atrapalha, mas tem contorno |
| Baixa | Visual ou texto |

### Riscos

| Risco | Como foi tratado |
| --- | --- |
| Regra de negócio checada só na tela e burlada por um envio direto | As regras ficam em `services.py` e no banco, e há testes que enviam dados alterados direto para o servidor |
| Uma mudança quebrar algo que já funcionava | Os testes rodam inteiros antes de cada pull request; foi assim que a regressão do BUG-11 apareceu |
| Diferenças entre navegadores | Só HTML e CSS padrão, quase sem JavaScript. O teste no Firefox fica no roteiro manual da seção 3.2. |

## 2. Casos de teste

Os casos automatizados ficam em `contas/tests.py`, `tickets/tests.py` e `painel/tests.py`. Cada linha abaixo
indica a classe de teste que verifica o caso, e o nome de cada teste já descreve o que ele confere.

| Caso | Requisito | Situação testada | Resultado esperado | Onde (classe de teste) |
| --- | --- | --- | --- | --- |
| CT01 | RF01 | Cliente se cadastra com dados válidos | Conta criada e já entra no sistema | `CadastroViewTests` |
| CT02 | RF01 | E-mail repetido (com outras maiúsculas), empresa vazia, senhas diferentes ou curtas | Cadastro recusado com a mensagem do erro | `CadastroViewTests`, `CriacaoDeUsuarioTests` |
| CT03 | RF02 | Entrar com e-mail e senha | Cliente vai para *Meus tickets*; equipe vai para a *Fila* | `EntrarSairTests` |
| CT04 | RF02 | Senha errada; usuário desativado | Não entra; só revela "desativado" se a senha estiver certa | `EntrarSairTests` |
| CT05 | RF02 | Sair | Sessão encerrada; sair só por POST | `EntrarSairTests` |
| CT06 | RNF03 | Senha gravada | No banco há só o hash, nunca a senha | `CriacaoDeUsuarioTests` |
| CT07 | RNF04 | Cada perfil tenta abrir telas de outro | 403 ou volta para a entrada; o menu mostra só o que é do perfil | `PermissaoPorPerfilTests`, `AdministracaoEquipeTests`, `PainelTests` |
| CT08 | RF04 | Administrador cadastra e edita atendente | Pessoa criada já consegue entrar; senha em branco mantém a atual | `AdministracaoEquipeTests` |
| CT09 | RF04, RN12 | Desativar pessoa | Não entra mais e perde a sessão aberta; o nome continua nos tickets antigos; ninguém desativa a si mesmo | `AdministracaoEquipeTests` |
| CT10 | RF05, RN12 | Criar, renomear e desativar categoria | Categoria desativada some da abertura, mas fica nos tickets antigos; nome repetido é recusado, inclusive com acento | `AdministracaoCategoriasTests` |
| CT11 | RF06, RN01, RN03, RN09 | Cliente abre ticket | Número a partir de 1000, situação *Aberto*, sem atendente, prioridade *Média* e prazo de 3 dias | `AbrirTicketTests`, `TicketTests` |
| CT12 | RF06 | Campos vazios, categoria inativa, descrição com mais de 5.000 caracteres | Recusado com o erro no campo | `AbrirTicketTests` |
| CT13 | RF07, RN08 | Cliente lista os tickets | Só os dela, com filtro por situação e aviso dos que esperam resposta | `MeusTicketsTests` |
| CT14 | RN08, RNF04 | Cliente abre o endereço de um ticket de outra cliente | 404, como se não existisse | `DetalheDoTicketClienteTests` |
| CT15 | RF08, RN10 | Fila de atendimento | Só tickets em aberto, atrasados primeiro, depois por prazo | `FilaTests` |
| CT16 | RF08 | Filtros por situação, categoria, prioridade, atendente e atrasados, combinados e com valor inválido na URL | Filtra corretamente; valor inválido é ignorado sem derrubar os outros filtros | `FilaTests` |
| CT17 | RNF07 | Fila com muitos tickets | O número de consultas ao banco não cresce com a fila | `FilaTests` |
| CT18 | RF09, RN13 | Detalhe do ticket | Conversa e eventos do histórico em ordem | `DetalheDoTicketClienteTests`, `ServicoResponderTests` |
| CT19 | RF10, RN04 | Atendente assume ticket aberto | Passa a ser o responsável, a situação vira *Em atendimento* e fica no histórico | `AssumirEAtribuirTests` |
| CT20 | RF10 | Assumir ticket que já tem dono; administrador passa o ticket para alguém | Recusado; o administrador só pode passar para alguém da equipe ativa | `AssumirEAtribuirTests` |
| CT21 | RF11, RN05 | Responsável e administrador mudam a situação; outro atendente tenta | Os dois primeiros conseguem; o outro é recusado e vê o motivo | `MudarSituacaoTests`, `TelaDeAtendimentoTests` |
| CT22 | RF11, RN02 | Transições proibidas (ex.: de *Resolvido* para *Aberto*) | Recusadas | `MudarSituacaoTests` |
| CT23 | RF12, RN06 | Cliente responde ticket *Aguardando cliente* | Mensagem gravada e o ticket volta para *Em atendimento* | `DetalheDoTicketClienteTests` |
| CT24 | RF12 | Resposta vazia, com mais de 5.000 caracteres ou em ticket resolvido | Recusada | `DetalheDoTicketClienteTests` |
| CT25 | RF13, RN08 | Nota interna | A equipe vê e o cliente não; a nota não muda a "última atualização" do cliente | `NotasInternasTests` |
| CT26 | RF13, RN05 | Atendente que não é o responsável | Pode deixar nota, mas não responde ao cliente | `NotasInternasTests` |
| CT27 | RF17, RN09, RN10 | Mudar a prioridade | Prazo recalculado a partir da abertura; um ticket antigo que vira *Urgente* fica atrasado | `PrioridadeTests` |
| CT28 | RF17, RN05 | Quem pode mudar a prioridade | Responsável e administrador sim, inclusive na triagem de um ticket aberto; outro atendente não; ticket resolvido não | `PrioridadeTests` |
| CT29 | RF16, RN11 | Cliente avalia ticket resolvido | Nota de 1 a 5 gravada, e a equipe vê a avaliação | `AvaliacaoTests` |
| CT30 | RF16, RN11 | Avaliar duas vezes, nota fora de 1 a 5, ticket não resolvido, outra pessoa avaliando | Tudo recusado | `AvaliacaoTests` |
| CT31 | RF18 | Painel nos períodos de 7, 30 e 90 dias | Números conferidos com dados montados no teste; sem dados não quebra; período inválido volta para 30 dias | `PainelTests` |
| CT32 | RN01 a RN13 | Gravar dados que violam as regras direto no banco (ex.: ticket aberto com atendente, nota 6, mensagem vazia) | O banco recusa | `TicketTests`, `CriacaoDeUsuarioTests` |
| CT33 | Todos | Ciclo completo: abrir, assumir, pedir informação, responder, resolver | Cada passo grava a situação e o histórico certos | `CicloCompletoTests` |

## 3. Execução

### 3.1 Testes automatizados

```bash
python manage.py test
```

```
Found 141 test(s).
...
Ran 141 tests in 15.7s

OK
```

| App | Testes | Cobertura |
| --- | --- | --- |
| `contas` | 40 | 98% |
| `tickets` | 93 | 95% |
| `painel` | 8 | 100% |
| `config` | — | 92% |
| **Total** | **141** | **96%** |

A cobertura mede quanto do código é executado pelos testes. Para gerar o relatório:

```bash
pip install coverage
coverage run manage.py test
coverage report
```

As configurações ficam em `.coveragerc`. Os 4% sem cobertura são, em sua maioria, mensagens de defesa que as telas
já impedem de acontecer (por exemplo, o serviço recusando um ticket que a tela nem oferece) e partes da área técnica `/admin`.

### 3.2 Testes manuais (sistema)

Executados em 07/11/2026, com o sistema rodando em modo de produção (`DEBUG=False`) e os dados de exemplo.

| Caso | O que foi feito | Resultado | Evidência |
| --- | --- | --- | --- |
| M01 | Entrar usando só o teclado | Passou: o foco começa no e-mail, o contorno de foco é visível e Enter envia | [captura](imagens/m01-foco-teclado.png) |
| M02 | Abrir um ticket no celular (375 px) | Passou: aviso de envio, ticket na lista e nenhuma rolagem lateral | [captura](imagens/m02-ticket-celular.png) |
| M03 | Atendente assume pela fila, responde e pede retorno | Passou | — |
| M04 | Cliente responde o ticket *Aguardando cliente* | Passou: o ticket voltou para *Em atendimento* (RN06) | — |
| M05 | Atendente resolve; cliente avalia usando as setas do teclado | Passou: as setas mudam a estrela marcada e a avaliação é gravada | [captura](imagens/m05-avaliacao-teclado.png) |
| M06 | Abrir telas proibidas e um ticket inexistente | Passou: páginas 403 e 404 próprias, sem detalhes técnicos | — |
| M07 | Sair e tentar voltar para a fila | Passou: pede login de novo | — |
| M08 | Painel no celular e *Ver em tabela* | Passou: a tabela mostra os 30 dias, sem rolagem lateral | — |
| M09 | Título e descrição com um link enorme, no celular | Passou depois da correção do BUG-09 | [captura](imagens/m09-texto-longo.png) |

No M01, a primeira execução do roteiro automatizado acusou falha. O problema estava no roteiro, que conferia o endereço
antes de a página terminar de carregar; o sistema estava certo. Depois de corrigir a espera, o caso passou.

**Testes de segurança feitos à parte:**
- O título `<script>alert(1)</script>` aparece como texto em todas as telas, sem executar.
- Um formulário enviado sem o código de proteção (CSRF) é recusado com 403.
- Um link de retorno para outro site depois do login (`?next=//outro-site.com`) é ignorado.

**Desempenho (RNF07), com 1.100 tickets:**

| Tela | Tempo (mediana de 5 medições) |
| --- | --- |
| Fila | 10 ms |
| Meus tickets | 97 ms |
| Painel de 90 dias | 15 ms |

O limite do requisito é de 2 segundos.

**Navegadores (RNF08):** os testes foram feitos no Chromium, a base do Chrome e do Edge. No Firefox, repita os
casos M01, M02 e M05 na sua máquina antes da apresentação.

## 4. Registro de bugs

Defeitos encontrados durante o desenvolvimento e nesta rodada. Cada correção tem um teste automatizado ou uma
verificação que impede o defeito de voltar.

| Bug | Onde apareceu | Descrição | Gravidade | Correção | Situação |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | Entrega 4 (banco) | Na área técnica, cadastrar um cliente sem empresa mostrava um erro técnico em inglês | Baixa | Mensagens em português em todas as restrições do banco | Corrigido |
| BUG-02 | Checkpoint 2 (fila) | Os filtros da fila não eram aplicados na primeira vez que a tela abria com filtros na URL | Média | O formulário de filtros passou a sempre ler a URL | Corrigido; teste `test_filtros_combinados` |
| BUG-03 | Checkpoint 2 (atendimento) | O administrador não conseguia passar para alguém um ticket ainda *Aberto*: o painel acusava erro na situação | Alta | A validação passou a comparar com a situação original do ticket | Corrigido; teste `test_administrador_passa_ticket_aberto_pelo_painel` |
| BUG-04 | Checkpoint 2 (categorias) | Era possível criar "Dúvida" e "DÚVIDA" como categorias diferentes: o SQLite só ignora maiúsculas em letras sem acento | Média | A comparação passou a ser feita no Python, que entende acentos | Corrigido; teste `test_nome_repetido_com_outras_maiusculas_e_recusado` |
| BUG-05 | Checkpoint 2 (layout) | No celular, as tabelas de tickets saíam da tela | Média | No celular, cada linha vira um cartão | Corrigido; verificado em 360 px |
| BUG-06 | Checkpoint 2 (layout) | No computador, os títulos dos tickets ficavam espremidos em várias linhas na fila | Baixa | Largura mínima para a coluna do título | Corrigido |
| BUG-07 | Checkpoint 3 (notas internas) | Uma nota interna mudava a "última atualização" que o cliente vê, revelando que algo aconteceu | Média | Notas internas não atualizam esse campo | Corrigido; teste `test_nota_nao_muda_a_ultima_atualizacao_vista_pelo_cliente` |
| BUG-08 | **Esta rodada** | A descrição e as respostas aceitavam qualquer tamanho: uma resposta de 100 mil caracteres foi gravada | Média | Limite de 5.000 caracteres, avisado no próprio campo | Corrigido; testes `test_descricao_tem_limite_de_tamanho` e `test_resposta_tem_limite_de_tamanho` |
| BUG-09 | **Esta rodada** | Um título, um link ou um nome muito longo, sem espaços, empurrava a página para fora da tela, no celular e no computador ([antes](imagens/bug09-antes.png), [na fila](imagens/bug09-antes-fila.png), [depois](imagens/m09-texto-longo.png)) | Média | Palavras longas passam a quebrar a linha em títulos, conversas, detalhes e tabelas | Corrigido; verificado em 13 telas, em 360 px e 1280 px |
| BUG-10 | Checkpoint 3 (prioridade) | Importação circular entre `models.py` e `services.py` impedia o sistema de iniciar | Alta | A função de prazo passou a ser importada só no momento de salvar o ticket | Corrigido; percebido na hora pelos testes |
| BUG-11 | Checkpoint 3 (regressão) | Os campos novos de prioridade e de tipo de mensagem fizeram os envios antigos, sem esses campos, darem erro | Alta | Campos novos opcionais, valendo o valor atual quando não enviados | Corrigido; percebido pelos testes do MVP |
| BUG-12 | **Esta rodada** | Na fila do administrador, a 1280 px, a tabela passava 25 px da caixa e cortava o botão *Assumir* | Baixa | A coluna do atendente pode quebrar a linha | Corrigido; verificado em 1280 px e 1440 px |

**Análise:**
- **Onde surgiram:** a maioria dos defeitos foi de layout ou de entradas incomuns. Nenhum deles chegou a uma versão publicada sem ser percebido.
- **Os mais graves** (BUG-03, BUG-10 e BUG-11) foram pegos pelos testes automatizados antes do pull request, o que mostra o valor de rodar a suíte inteira a cada mudança.
- **Os três desta rodada** só apareceram ao testar entradas extremas de propósito. Os casos normais, com dados de exemplo, funcionavam.

## 5. Limitações conhecidas

- Entre 641 px e cerca de 1.100 px de largura (tablets e telas pequenas), a tabela da fila rola para o lado dentro da própria caixa. O restante da página continua parado e todas as colunas ficam acessíveis.
- O teste no Firefox fica para a rodada manual na máquina da aluna (seção 3.2).
- Funcionalidades do backlog (reabrir ticket, busca, anexos, e-mails e exportação) não foram testadas porque ainda não existem.
