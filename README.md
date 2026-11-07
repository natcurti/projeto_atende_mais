# atende+

Sistema web de tickets de suporte. Clientes abrem pedidos de ajuda, a equipe de atendimento
acompanha cada um até a solução, e a gestão vê indicadores do atendimento.

Projeto da disciplina do curso de **Análise e Desenvolvimento de Sistemas — FATEC**.

**Versão atual:** `v1.0.0` (release candidate). Cadastro e login, tickets do cliente, fila e atendimento pela equipe,
notas internas, prioridade com prazo, avaliação do atendimento, painel de indicadores e administração.
Veja o [Checkpoint 5](docs/12-release/).

**Sistema publicado:** https://natcurti.pythonanywhere.com (usuários de exemplo em [Como rodar](#como-rodar))

**Protótipo navegável:** https://natcurti.github.io/projeto_atende_mais/03-ux-ui/prototipo/

## Etapas do projeto

| Etapa | Entrega | Situação | Onde está |
| --- | --- | --- | --- |
| 1 | Entrega 1: levantamento de requisitos | Concluída | [docs/01-requisitos](docs/01-requisitos/) |
| 2 | Entrega 2: wireframes | Concluída | [docs/02-wireframes](docs/02-wireframes/) |
| 3 | Entrega 3: UX/UI e protótipo navegável | Concluída | [docs/03-ux-ui](docs/03-ux-ui/) |
| 4 | Entrega 4: banco de dados | Concluída | [docs/04-banco-de-dados](docs/04-banco-de-dados/) |
| 5 | Entrega 5: repositório e versionamento | Concluída | [docs/05-repositorio](docs/05-repositorio/) |
| 6 | Entrega 6: arquitetura e padrões | Concluída | [docs/06-arquitetura](docs/06-arquitetura/) |
| 7 | Entrega 7: gerenciamento do projeto | Não realizada | — |
| 8 | Checkpoint 1: definição do MVP | Concluída | [docs/08-mvp](docs/08-mvp/) |
| 9 | Checkpoint 2: MVP funcional (`v0.1.0`) | Concluída | [docs/09-mvp-funcional](docs/09-mvp-funcional/) |
| 10 | Checkpoint 3: evolução | Concluída | [docs/10-evolucao](docs/10-evolucao/) |
| 11 | Checkpoint 4: nova versão (`v0.2.0`) | Concluída | [docs/10-evolucao](docs/10-evolucao/) |
| 12 | Entrega 8: plano e execução de testes | Concluída | [docs/11-testes](docs/11-testes/) |
| 13 | Checkpoint 5: release candidate (`v1.0.0`) | Concluída | [docs/12-release](docs/12-release/) |
| 14 | Entrega 9: relatório técnico | Concluída | [docs/13-relatorio-tecnico](docs/13-relatorio-tecnico/) |

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.10 a 3.13 (recomendado 3.12 ou mais recente) |
| Framework web | Django 5.2 LTS |
| Banco de dados | SQLite (arquivo único, sem servidor) |
| Interface | HTML, CSS e JavaScript, a partir do protótipo da Entrega 3 |
| Versionamento | Git e GitHub |

Detalhes da arquitetura em [docs/06-arquitetura](docs/06-arquitetura/).

## Como rodar

Você precisa do [Python](https://www.python.org/downloads/) 3.10 ou mais recente e do [Git](https://git-scm.com/).
Não é preciso instalar banco de dados: o SQLite já vem com o Python.

**1. Baixar o projeto**

```bash
git clone https://github.com/natcurti/projeto_atende_mais.git
cd projeto_atende_mais
```

**2. Criar e ativar um ambiente virtual** (isola as bibliotecas do projeto)

| Sistema | Criar | Ativar |
| --- | --- | --- |
| Windows | `py -m venv .venv` | `.venv\Scripts\activate` |
| Linux / macOS | `python3 -m venv .venv` | `source .venv/bin/activate` |

Com o ambiente ativo, o terminal mostra `(.venv)` no começo da linha.

**3. Instalar as dependências, criar o banco e carregar os dados de exemplo**

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py carregar_dados_exemplo
```

**4. Iniciar o sistema**

```bash
python manage.py runserver
```

Abra **http://127.0.0.1:8000** no navegador: a tela de entrada aparece, com login e cadastro de cliente.
Para parar o servidor, use `Ctrl + C` no terminal.

**Usuários de exemplo** (senha de todos: `atende123`):

| Perfil | E-mail | Começa em |
| --- | --- | --- |
| Administradora | juliana@empresa.com | Fila; também acessa *Painel* e *Administração* |
| Atendente | carlos@empresa.com | Fila de atendimento |
| Atendente | ana@empresa.com | Fila de atendimento |
| Cliente | maria@souzacomercio.com.br | Meus tickets |

O roteiro de demonstração passo a passo está em [docs/09-mvp-funcional](docs/09-mvp-funcional/#4-roteiro-de-demonstração),
e o das funcionalidades da `v0.2.0` em [docs/10-evolucao](docs/10-evolucao/#5-como-ver-a-nova-versão).

Todos os dados também podem ser vistos na área técnica do Django, em http://127.0.0.1:8000/admin,
entrando como a administradora.

**Testes automatizados**

```bash
python manage.py test
```

O plano de testes, os casos, os resultados e o registro de bugs estão em [docs/11-testes](docs/11-testes/).

**Configuração opcional:** sem nenhuma configuração, o sistema roda em modo de desenvolvimento.
Para mudar as opções (como no servidor de publicação), copie `.env.exemplo` com o nome `.env` e ajuste os valores.

**Recomeçar o banco do zero:** apague o arquivo `db.sqlite3` e repita os comandos `migrate` e `carregar_dados_exemplo`.

## Casos de teste para a apresentação

Roteiro para demonstrar o sistema ao vivo em https://natcurti.pythonanywhere.com, ou na máquina local.
Cada caso diz o que fazer e o que deve acontecer. A ordem conta a história de um atendimento completo.
Os 33 casos completos, com os testes automatizados que verificam cada um, estão em [docs/11-testes](docs/11-testes/#2-casos-de-teste).

Senha de todos os usuários: `atende123`.

| Pessoa | E-mail |
| --- | --- |
| Maria (cliente) | maria@souzacomercio.com.br |
| Carlos (atendente) | carlos@empresa.com |
| Ana (atendente) | ana@empresa.com |
| Juliana (administradora) | juliana@empresa.com |

Antes da apresentação, recomece os dados de exemplo para que os tickets estejam como descrito abaixo.
O passo a passo está em [docs/12-release](docs/12-release/#37-manutenção-do-plano-gratuito).

### Cliente

**CT-A01 · Cadastro de cliente** (RF01)
1. Na tela de entrada, preencha *Criar conta* com nome, e-mail novo, empresa e uma senha de 8 caracteres ou mais.
2. Clique em *Criar conta*.

✅ **Esperado:** a conta é criada e a pessoa já entra em *Meus tickets*, que mostra o convite para abrir o primeiro ticket.

**CT-A02 · Abrir ticket em até 3 cliques** (RF06, RN01, RN03, RN09, RNF05)
1. Entre como **Maria**.
2. Clique em *Abrir ticket*.
3. Preencha título, categoria e descrição.
4. Clique em *Enviar ticket*.

✅ **Esperado:** aparece o aviso "Ticket #10xx enviado". O ticket aparece na lista como *Aberto*, com prioridade *Média* (prazo de 3 dias) e ainda sem atendente.

**CT-A03 · Cliente só vê o que é seu** (RN08, RNF04)
1. Ainda como Maria, digite na barra de endereço `/fila/`.
2. Depois digite `/meus-tickets/1005/`, que é um ticket de outra cliente.

✅ **Esperado:** a fila mostra "Esta página não é do seu perfil" (erro 403). O ticket de outra cliente mostra "não encontrado" (404), como se não existisse.

### Atendimento

**CT-A04 · Fila com atrasados primeiro** (RF08, RN10)
1. Entre como **Carlos**.
2. Veja a *Fila*.
3. Filtre por *Categoria: Financeiro* e clique em *Filtrar*.

✅ **Esperado:** o #1006 (Urgente, aberto há mais de 4 horas) aparece no topo, com a marca vermelha de *Atrasado*. O filtro mostra só os tickets de Financeiro.

**CT-A05 · Assumir e responder** (RF10, RF12, RN04, RN13)
1. Na fila, clique em *Assumir* no ticket aberto no CT-A02.
2. Escreva uma *Mensagem ao cliente* e envie.

✅ **Esperado:** o ticket fica com Carlos e passa para *Em atendimento*. A conversa mostra o evento "Carlos Lima assumiu o atendimento" e a mensagem.

**CT-A06 · Nota interna que o cliente não vê** (RF13, RN08)
1. Como Carlos, abra o #1003.
2. Escolha *Nota interna*, escreva e envie.
3. Entre como Maria e abra o mesmo #1003.

✅ **Esperado:** para Carlos, a nota aparece em amarelo, com o aviso "só a equipe vê". Para Maria, a nota não aparece.

**CT-A07 · Só o responsável altera o ticket** (RN05)
1. Entre como **Ana**.
2. Abra o #1003, que está com Carlos.

✅ **Esperado:** aparece "Este ticket está com Carlos Lima. Só a pessoa responsável ou um administrador pode alterá-lo." Ana não vê o painel de gerenciar e só pode deixar nota interna.

**CT-A08 · Prioridade recalcula o prazo** (RF17, RN09, RN10)
1. Como Carlos, abra o #1003.
2. Em *Gerenciar ticket*, mude a prioridade para *Urgente* e clique em *Salvar alterações*.

✅ **Esperado:** o prazo passa a ser 4 horas depois da abertura. Como o ticket foi aberto há mais de um dia, ele fica *Atrasado* e sobe para o topo da fila. O histórico registra "Prioridade alterada de Média para Urgente".

**CT-A09 · Resposta do cliente reativa o ticket** (RN06)
1. Como Maria, abra o #1002, que está *Aguardando cliente*.
2. Responda.

✅ **Esperado:** o ticket volta sozinho para *Em atendimento*, e o histórico registra a mudança.

**CT-A10 · Resolver e avaliar uma única vez** (RF11, RF16, RN11)
1. Como Maria, abra o #1001 (*Resolvido*).
2. Escolha 5 estrelas, escreva um comentário e clique em *Enviar avaliação*.
3. Entre como Carlos e abra o #1001 pela fila, com o filtro *Situação: Resolvido*.

✅ **Esperado:** aparece "Obrigado pela avaliação", e o formulário dá lugar à nota dada, sem opção de avaliar de novo. Carlos vê a avaliação nos detalhes do ticket.

### Gestão

**CT-A11 · Painel de indicadores** (RF18)
1. Entre como **Juliana**.
2. Abra o *Painel*.
3. Troque entre *7 dias*, *30 dias* e *90 dias*.
4. Abra *Ver em tabela*.

✅ **Esperado:** os números e o gráfico mudam com o período. As tabelas por categoria e por atendente mostram o desempenho de cada um. Carlos e Maria não veem o menu *Painel*.

**CT-A12 · Desativar em vez de excluir** (RF04, RF05, RN12)
1. Saia e tente entrar como `pedro@empresa.com`, que é um atendente desativado.
2. Entre como Juliana, vá em *Administração* e desative a categoria *Dúvida*.
3. Entre como Maria e abra *Abrir ticket*.
4. Reative a categoria no final.

✅ **Esperado:** Pedro não entra e vê o aviso de acesso desativado. *Dúvida* some das opções de novo ticket, mas continua aparecendo nos tickets antigos.

**CT-A13 · Testes automatizados** (Entrega 8)
1. Na máquina local, rode `python manage.py test`.

✅ **Esperado:** `Ran 141 tests` e `OK`, em cerca de 20 segundos.

## Organização do repositório

```
projeto_atende_mais/
├── config/                configurações do Django e rotas principais
├── contas/                app de usuários (cliente, atendente, administrador)
├── tickets/               app de atendimento (tickets, mensagens, regras de negócio)
├── painel/                app do painel de indicadores
├── templates/             páginas HTML
├── static/                CSS e JavaScript
├── manage.py              comando de administração do Django
├── requirements.txt       dependências
├── .env.exemplo           modelo de configuração local
├── docs/                  documentação de cada entrega
│   ├── 01-requisitos/
│   ├── 02-wireframes/
│   ├── 03-ux-ui/          inclui o protótipo navegável
│   ├── 04-banco-de-dados/
│   ├── 05-repositorio/
│   ├── 06-arquitetura/
│   ├── 08-mvp/            Checkpoint 1: definição do MVP
│   ├── 09-mvp-funcional/  Checkpoint 2: MVP funcional, com capturas de tela
│   ├── 10-evolucao/       Checkpoints 3 e 4: evolução e versão v0.2.0
│   ├── 11-testes/         Entrega 8: plano, casos, execução e registro de bugs
│   ├── 12-release/        Checkpoint 5: versão v1.0.0 e publicação no PythonAnywhere
│   └── 13-relatorio-tecnico/  Entrega 9: relatório técnico (também em PDF)
├── .github/               modelo de pull request
├── .coveragerc            configuração da medição de cobertura dos testes
├── .editorconfig          estilo dos arquivos
├── .gitattributes         quebras de linha padronizadas
└── .gitignore             arquivos que não vão para o repositório
```

## Como contribuir

O projeto usa as branches `main` (versões entregues) e `develop` (desenvolvimento), uma branch por tarefa
e mensagens de commit no padrão *Conventional Commits*. As regras completas estão em
[docs/05-repositorio](docs/05-repositorio/).

## Autoria

Desenvolvido por [@natcurti](https://github.com/natcurti).
