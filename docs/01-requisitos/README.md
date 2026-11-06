# atende+ — Entrega 1: Levantamento de Requisitos

## 1. Apresentação

O atende+ é um sistema web de tickets de suporte. Com ele, clientes de uma empresa de software abrem chamados e a equipe de atendimento acompanha cada um até a solução.

| Item | Definição |
| --- | --- |
| Nome do sistema | atende+ |
| Tipo | Aplicação web (navegador de desktop e celular) |
| Contexto | Suporte a clientes de uma empresa fictícia que vende um software de gestão |
| Tecnologia prevista | Python + Django, banco relacional (detalhado na Entrega 6) |
| Equipe | 1 integrante |
| Disciplina | Projeto do curso de Análise e Desenvolvimento de Sistemas — FATEC |

## 2. Problema

Hoje a empresa recebe pedidos de suporte por e-mail, WhatsApp e telefone, sem registro único. Por isso, chamados se perdem e ninguém sabe quanto tempo cada atendimento leva.

Dores identificadas:

- **Pedidos perdidos:** mensagens ficam espalhadas em canais diferentes e algumas nunca recebem resposta.
- **Falta de responsável:** não fica claro qual atendente está cuidando de cada pedido, o que gera retrabalho ou abandono.
- **Cliente sem retorno:** o cliente não consegue ver em que situação está o seu pedido e precisa cobrar novamente.
- **Sem histórico:** a conversa sobre um problema não fica registrada, então o próximo atendente começa do zero.
- **Sem indicadores:** a gestão não sabe quantos chamados chegam, quais assuntos mais aparecem nem o tempo médio de resolução.

**Objetivo do atende+:** centralizar os pedidos de suporte em um só lugar, com responsável, situação e histórico visíveis para cliente e equipe, e gerar indicadores simples para a gestão.

## 3. Público-alvo e perfis de usuário

O público-alvo são pequenas e médias empresas de software que atendem clientes e ainda não têm uma ferramenta de suporte. O sistema atende três perfis.

| Perfil | Quem é | O que faz no sistema |
| --- | --- | --- |
| Cliente | Usuário do software da empresa que precisa de ajuda | Abre tickets, acompanha a situação, comenta e avalia o atendimento |
| Atendente | Funcionário da equipe de suporte | Assume tickets, responde, muda a situação e resolve |
| Administrador | Coordenador do suporte | Gerencia usuários e categorias, redistribui tickets e consulta indicadores |

Um usuário tem exatamente um perfil. O administrador também pode atender tickets, se necessário.

## 4. Requisitos funcionais

São 21 requisitos funcionais: 11 essenciais, 6 importantes e 4 desejáveis. A prioridade segue três níveis: **Essencial** (sem ele o sistema não funciona), **Importante** (agrega muito valor) e **Desejável** (entra se houver tempo).

| Código | Requisito | Perfil | Prioridade |
| --- | --- | --- | --- |
| RF01 | Cadastrar-se como cliente informando nome, e-mail, empresa e senha | Cliente | Essencial |
| RF02 | Entrar e sair do sistema com e-mail e senha | Todos | Essencial |
| RF03 | Recuperar a senha por e-mail | Todos | Desejável |
| RF04 | Cadastrar, editar e desativar usuários atendentes e administradores | Administrador | Essencial |
| RF05 | Cadastrar, editar e desativar categorias de ticket (ex.: Financeiro, Erro no sistema, Dúvida) | Administrador | Essencial |
| RF06 | Abrir ticket informando título, descrição e categoria | Cliente | Essencial |
| RF07 | Listar os próprios tickets com a situação de cada um | Cliente | Essencial |
| RF08 | Ver a fila de tickets com filtros por situação, categoria, prioridade e atendente | Atendente, Administrador | Essencial |
| RF09 | Ver os detalhes de um ticket com todo o histórico de mensagens e mudanças | Todos | Essencial |
| RF10 | Assumir um ticket ou atribuí-lo a outro atendente | Atendente, Administrador | Essencial |
| RF11 | Alterar a situação do ticket | Atendente, Administrador | Essencial |
| RF12 | Adicionar mensagens ao ticket | Todos | Essencial |
| RF13 | Adicionar nota interna, visível só para a equipe | Atendente, Administrador | Importante |
| RF14 | Anexar arquivos (imagem ou PDF) ao ticket | Todos | Desejável |
| RF15 | Reabrir um ticket resolvido | Cliente | Importante |
| RF16 | Avaliar o atendimento com nota de 1 a 5 e comentário opcional | Cliente | Importante |
| RF17 | Definir a prioridade do ticket e calcular o prazo de resolução | Atendente, Administrador | Importante |
| RF18 | Ver painel de indicadores: tickets por situação e categoria, tempo médio de resolução e nota média | Administrador | Importante |
| RF19 | Enviar e-mail ao cliente quando o ticket mudar de situação | Sistema | Desejável |
| RF20 | Buscar ticket por número ou palavra do título | Todos | Importante |
| RF21 | Exportar a lista de tickets filtrada em CSV | Administrador | Desejável |

Observação: dos 21, os 11 essenciais formam a base do MVP (seção 7).

## 5. Requisitos não funcionais

Os requisitos não funcionais definem como o sistema deve se comportar. Cada um tem um critério que pode ser verificado nos testes (Entrega 8).

| Código | Categoria | Requisito | Como verificar |
| --- | --- | --- | --- |
| RNF01 | Tecnologia | Desenvolvido em Python com o framework Django | Código-fonte no repositório |
| RNF02 | Banco de dados | Dados guardados em banco relacional MariaDB 10.5+ ou MySQL 8.0.16+ | Configuração do projeto |
| RNF03 | Segurança | Senhas guardadas com criptografia (hash), nunca em texto puro | Consulta direta ao banco |
| RNF04 | Segurança | Cada perfil acessa apenas as telas e os dados permitidos para ele | Teste de acesso com cada perfil |
| RNF05 | Usabilidade | Interface em português, com no máximo 3 cliques para abrir um ticket a partir da tela inicial | Teste de navegação |
| RNF06 | Responsividade | Telas utilizáveis em celular (largura de 360 px) e em computador | Teste em navegador nos dois tamanhos |
| RNF07 | Desempenho | Listas de tickets carregam em até 2 segundos com 1.000 tickets cadastrados | Teste com dados de exemplo |
| RNF08 | Compatibilidade | Funciona nas versões atuais de Chrome, Edge e Firefox | Teste nos três navegadores |
| RNF09 | Manutenibilidade | Código versionado no Git, com padrão de commits e README de instalação | Repositório (Entrega 5) |
| RNF10 | Disponibilidade | Sistema publicado na internet para a apresentação final | Acesso pelo link público |

## 6. Regras de negócio

As regras de negócio são as políticas que o sistema precisa respeitar, independentemente da tela.

| Código | Regra |
| --- | --- |
| RN01 | Todo ticket recebe um número sequencial único e a data e hora de abertura, gerados pelo sistema. |
| RN02 | Um ticket tem sempre uma destas situações: Aberto, Em atendimento, Aguardando cliente, Resolvido, Fechado. |
| RN03 | Todo ticket nasce com a situação Aberto e sem atendente. |
| RN04 | Ao ser assumido por um atendente, o ticket passa para Em atendimento. Cada ticket tem no máximo um atendente responsável. |
| RN05 | Só o atendente responsável ou um administrador pode alterar a situação de um ticket. |
| RN06 | Quando o cliente responde um ticket em Aguardando cliente, ele volta automaticamente para Em atendimento. |
| RN07 | O cliente pode reabrir um ticket Resolvido em até 7 dias. Depois disso, o ticket passa para Fechado e não pode mais ser alterado. |
| RN08 | O cliente só vê os próprios tickets. Notas internas nunca aparecem para o cliente. |
| RN09 | A prioridade define o prazo de resolução: Urgente = 4 horas, Alta = 1 dia, Média = 3 dias, Baixa = 5 dias. O padrão é Média. |
| RN10 | Um ticket com prazo vencido e ainda não resolvido é marcado como Atrasado nas listas e no painel. |
| RN11 | A avaliação (nota de 1 a 5) só pode ser feita uma vez, depois que o ticket for Resolvido. |
| RN12 | Usuários e categorias não são excluídos, apenas desativados, para preservar o histórico. Uma categoria desativada não aparece para novos tickets. |
| RN13 | Toda mudança de situação, atendente ou prioridade fica registrada no histórico do ticket, com autor e data. |
| RN14 | Anexos aceitam apenas JPG, PNG ou PDF, com até 5 MB cada. |

Ciclo de vida do ticket (RN02 a RN07):

1. **Aberto** → um atendente assume → **Em atendimento**
2. **Em atendimento** → o atendente pede informação → **Aguardando cliente** → o cliente responde → volta para **Em atendimento**
3. **Em atendimento** → o atendente conclui → **Resolvido**
4. **Resolvido** → o cliente reabre em até 7 dias → **Em atendimento**; senão → **Fechado**

## 7. Escopo

O atende+ cobre o ciclo completo de um ticket, da abertura à avaliação, mais um painel de indicadores. Integrações externas e recursos de atendimento em tempo real ficam fora.

**Dentro do escopo**

- Cadastro e login dos três perfis
- Abertura, acompanhamento, atendimento e encerramento de tickets
- Mensagens, notas internas e histórico de cada ticket
- Prioridade com prazo de resolução e marcação de atrasados
- Avaliação do atendimento pelo cliente
- Painel de indicadores e exportação em CSV

**Fora do escopo**

- Chat em tempo real e atendimento por telefone
- Abertura de tickets por e-mail ou WhatsApp
- Aplicativo nativo para celular (o sistema web será responsivo)
- Base de conhecimento e respostas automáticas com IA
- Cobrança, planos e contratos de clientes
- Vários idiomas

**Entregas por fase**

| Fase | Requisitos | Marco |
| --- | --- | --- |
| MVP | RF01, RF02, RF04 a RF12 | Checkpoint 2 — MVP funcional |
| Evolução 1 | RF13, RF15, RF17, RF20 | Checkpoint 3 |
| Evolução 2 | RF16, RF18 | Checkpoint 4 |
| Release | RF03, RF14, RF19, RF21 (se houver tempo) e correções | Checkpoint 5 — Release candidate |

## 8. Glossário e premissas

| Termo | Significado |
| --- | --- |
| Ticket | Registro de um pedido de suporte feito por um cliente |
| Situação | Etapa em que o ticket está no ciclo de atendimento (RN02) |
| Fila | Lista de tickets que a equipe precisa atender |
| Nota interna | Mensagem no ticket visível só para atendentes e administradores |
| Prazo (SLA) | Tempo máximo para resolver o ticket, conforme a prioridade (RN09) |
| Atrasado | Ticket não resolvido cujo prazo já venceu |
| MVP | Produto mínimo viável: a primeira versão que já resolve o problema principal |

**Premissas**

- A empresa usuária é fictícia; os dados de demonstração serão gerados para testes.
- Os prazos de resolução contam horas corridas, sem considerar horário comercial ou feriados.
- O projeto é desenvolvido por uma pessoa, então o escopo foi dimensionado para caber no semestre.
