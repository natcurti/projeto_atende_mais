# atende+

Sistema web de tickets de suporte. Clientes abrem pedidos de ajuda, a equipe de atendimento
acompanha cada um até a solução, e a gestão vê indicadores do atendimento.

Projeto da disciplina do curso de **Análise e Desenvolvimento de Sistemas — FATEC**.

**Protótipo navegável:** https://natcurti.github.io/projeto_atende_mais/03-ux-ui/prototipo/

## Entregas

| Nº | Entrega | Situação | Onde está |
| --- | --- | --- | --- |
| 1 | Levantamento de requisitos | Concluída | [docs/01-requisitos](docs/01-requisitos/) |
| 2 | Wireframes | Concluída | [docs/02-wireframes](docs/02-wireframes/) |
| 3 | UX/UI e protótipo navegável | Concluída | [docs/03-ux-ui](docs/03-ux-ui/) |
| 4 | Banco de dados | Concluída | [docs/04-banco-de-dados](docs/04-banco-de-dados/) |
| 5 | Repositório e versionamento | Concluída | [docs/05-repositorio](docs/05-repositorio/) |
| 6 | Arquitetura e padrões | A fazer | — |
| 7 | Gerenciamento do projeto | A fazer | — |
| 8 | Plano e execução de testes | A fazer | — |
| 9 | Relatório técnico | A fazer | — |

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python |
| Framework web | Django |
| Banco de dados | SQLite (arquivo único, sem servidor) |
| Interface | HTML, CSS e JavaScript, a partir do protótipo da Entrega 3 |
| Versionamento | Git e GitHub |

As versões e a arquitetura são definidas na Entrega 6.

## Como rodar

O código do sistema começa a ser escrito no MVP (Checkpoint 2), e esta seção vai trazer o passo a passo completo.
Por enquanto, para baixar o projeto:

```bash
git clone https://github.com/natcurti/projeto_atende_mais.git
cd projeto_atende_mais
```

## Organização do repositório

```
projeto_atende_mais/
├── docs/                  documentação de cada entrega
│   ├── 01-requisitos/
│   ├── 02-wireframes/
│   ├── 03-ux-ui/          inclui o protótipo navegável
│   ├── 04-banco-de-dados/
│   └── 05-repositorio/
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
