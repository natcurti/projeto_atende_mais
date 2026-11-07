# atende+

Sistema web de tickets de suporte. Clientes abrem pedidos de ajuda, a equipe de atendimento
acompanha cada um até a solução, e a gestão vê indicadores do atendimento.

Projeto da disciplina do curso de **Análise e Desenvolvimento de Sistemas — FATEC**.

**Versão atual:** `v0.1.0` (MVP), com cadastro e login, abertura e acompanhamento de tickets pelo cliente,
fila de atendimento, atendimento pela equipe e administração. Veja o [Checkpoint 2](docs/09-mvp-funcional/).

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
| 10 | Checkpoint 3: evolução | A fazer | — |
| 11 | Checkpoint 4: nova versão | A fazer | — |
| 12 | Entrega 8: plano e execução de testes | A fazer | — |
| 13 | Checkpoint 5: release candidate | A fazer | — |
| 14 | Entrega 9: relatório técnico | A fazer | — |

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
| Administradora | juliana@empresa.com | Fila; também acessa *Administração* |
| Atendente | carlos@empresa.com | Fila de atendimento |
| Atendente | ana@empresa.com | Fila de atendimento |
| Cliente | maria@souzacomercio.com.br | Meus tickets |

O roteiro de demonstração passo a passo está em [docs/09-mvp-funcional](docs/09-mvp-funcional/#4-roteiro-de-demonstração).

Todos os dados também podem ser vistos na área técnica do Django, em http://127.0.0.1:8000/admin,
entrando como a administradora.

**Testes automatizados**

```bash
python manage.py test
```

**Configuração opcional:** sem nenhuma configuração, o sistema roda em modo de desenvolvimento.
Para mudar as opções (como no servidor de publicação), copie `.env.exemplo` com o nome `.env` e ajuste os valores.

**Recomeçar o banco do zero:** apague o arquivo `db.sqlite3` e repita os comandos `migrate` e `carregar_dados_exemplo`.

## Organização do repositório

```
projeto_atende_mais/
├── config/                configurações do Django e rotas principais
├── contas/                app de usuários (cliente, atendente, administrador)
├── tickets/               app de atendimento (tickets, mensagens, regras de negócio)
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
│   └── 09-mvp-funcional/  Checkpoint 2: MVP funcional, com capturas de tela
├── .github/               modelo de pull request
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
