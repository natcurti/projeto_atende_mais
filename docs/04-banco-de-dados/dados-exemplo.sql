-- ==========================================================
-- atende+ — dados de exemplo (Entrega 4)
-- Os mesmos personagens e tickets do protótipo da Entrega 3.
-- Executar depois de schema.sql. Funciona no SQLite e no MariaDB/MySQL.
-- Para facilitar a leitura, as datas abaixo estão no horário de Brasília.
-- ==========================================================

-- Senhas: no sistema real, o Django gera o hash. Aqui é só um texto de exemplo.
INSERT INTO usuario (nome, email, senha_hash, perfil, empresa, ativo) VALUES
  ('Juliana Prado',  'juliana@empresa.com',          'hash-de-exemplo', 'administrador', NULL,                 TRUE),   -- id 1
  ('Carlos Lima',    'carlos@empresa.com',           'hash-de-exemplo', 'atendente',     NULL,                 TRUE),   -- id 2
  ('Ana Reis',       'ana@empresa.com',              'hash-de-exemplo', 'atendente',     NULL,                 TRUE),   -- id 3
  ('Pedro Alves',    'pedro@empresa.com',            'hash-de-exemplo', 'atendente',     NULL,                 FALSE),  -- id 4
  ('Maria Souza',    'maria@souzacomercio.com.br',   'hash-de-exemplo', 'cliente',       'Souza Comércio ME',  TRUE),   -- id 5
  ('Roberto Dias',   'roberto@padariabompao.com.br', 'hash-de-exemplo', 'cliente',       'Padaria Bom Pão',    TRUE),   -- id 6
  ('Fernanda Lopes', 'fernanda@lojacentral.com.br',  'hash-de-exemplo', 'cliente',       'Loja Central',       TRUE),   -- id 7
  ('José Silva',     'jose@autopecassilva.com.br',   'hash-de-exemplo', 'cliente',       'Auto Peças Silva',   TRUE);   -- id 8

INSERT INTO categoria (nome, ativa) VALUES
  ('Erro no sistema', TRUE),   -- id 1
  ('Dúvida',          TRUE),   -- id 2
  ('Financeiro',      TRUE),   -- id 3
  ('Treinamento',     FALSE);  -- id 4

-- Prazos seguindo a RN09: urgente 4 h, alta 1 dia, média 3 dias, baixa 5 dias.
INSERT INTO ticket (titulo, descricao, situacao, prioridade, cliente_id, atendente_id, categoria_id,
                    aberto_em, prazo, atualizado_em, resolvido_em, fechado_em) VALUES
  ('Não consigo cadastrar produto', 'O botão Salvar fica desabilitado na tela de produtos.',
   'fechado', 'alta', 5, 3, 1,
   '2026-10-24 10:00', '2026-10-25 10:00', '2026-11-01 09:00', '2026-10-25 09:00', '2026-11-01 09:00'),          -- #1000
  ('Cobrança duplicada em outubro', 'O boleto de outubro veio duas vezes no mesmo valor. Paguei só um.',
   'resolvido', 'media', 5, 3, 3,
   '2026-11-01 14:10', '2026-11-04 14:10', '2026-11-03 09:05', '2026-11-03 09:05', NULL),                        -- #1001
  ('Dúvida sobre o relatório mensal', 'O relatório mensal mostra vendas canceladas. Isso está certo?',
   'aguardando_cliente', 'baixa', 5, 2, 2,
   '2026-11-04 11:00', '2026-11-09 11:00', '2026-11-05 16:40', NULL, NULL),                                      -- #1002
  ('Erro ao emitir nota fiscal', 'Ao clicar em "Emitir nota", aparece a mensagem "Falha na comunicação com a SEFAZ".',
   'em_atendimento', 'media', 5, 2, 1,
   '2026-11-05 09:30', '2026-11-08 09:30', '2026-11-06 10:12', NULL, NULL),                                      -- #1003
  ('Boleto não chegou por e-mail', 'O boleto de novembro não chegou no e-mail do financeiro.',
   'aguardando_cliente', 'baixa', 8, 3, 3,
   '2026-11-05 11:00', '2026-11-10 11:00', '2026-11-05 15:20', NULL, NULL),                                      -- #1004
  ('Como cadastrar um novo usuário?', 'Contratamos uma pessoa nova e não achamos onde criar o acesso dela.',
   'aberto', 'media', 7, NULL, 2,
   '2026-11-06 15:00', '2026-11-09 15:00', '2026-11-06 15:00', NULL, NULL),                                      -- #1005
  ('Sistema lento ao gerar relatório', 'Desde ontem o relatório de vendas leva mais de 5 minutos para abrir.',
   'aberto', 'urgente', 6, NULL, 1,
   '2026-11-06 08:00', '2026-11-06 12:00', '2026-11-06 08:00', NULL, NULL);                                      -- #1006

-- Conversa do ticket #1003 (a mesma do protótipo).
INSERT INTO mensagem (ticket_id, autor_id, texto, interna, criada_em) VALUES
  (1003, 2, 'Parece o mesmo caso do certificado digital vencido. Confirmar com o print antes de responder.', TRUE, '2026-11-05 10:04'),
  (1003, 2, 'Olá, Maria! Pode nos enviar um print da tela com o erro? Assim confirmamos a causa.', FALSE, '2026-11-05 10:05'),
  (1003, 5, 'Segue o print.', FALSE, '2026-11-06 10:12'),
  (1001, 3, 'Maria, confirmamos a duplicidade e cancelamos o segundo boleto. Não há nada pendente na sua conta.', FALSE, '2026-11-03 09:05'),
  (1002, 2, 'Olá! Pode nos dizer de qual mês é o relatório?', FALSE, '2026-11-05 16:40');

INSERT INTO anexo (ticket_id, mensagem_id, enviado_por_id, arquivo, nome_original, tipo, tamanho_bytes, enviado_em) VALUES
  (1003, 3, 5, 'anexos/2026/11/1003-print-erro.png', 'print-erro.png', 'png', 245760, '2026-11-06 10:12');

INSERT INTO historico (ticket_id, autor_id, campo, valor_anterior, valor_novo, alterado_em) VALUES
  (1003, 2, 'atendente', NULL,             'Carlos Lima',        '2026-11-05 10:02'),
  (1003, 2, 'situacao',  'aberto',         'em_atendimento',     '2026-11-05 10:02'),
  (1001, 3, 'atendente', NULL,             'Ana Reis',           '2026-11-01 15:00'),
  (1001, 3, 'situacao',  'aberto',         'em_atendimento',     '2026-11-01 15:00'),
  (1001, 3, 'situacao',  'em_atendimento', 'resolvido',          '2026-11-03 09:05'),
  (1002, 2, 'situacao',  'em_atendimento', 'aguardando_cliente', '2026-11-05 16:40');

INSERT INTO avaliacao (ticket_id, nota, comentario, avaliado_em) VALUES
  (1000, 4, 'Resolveram rápido.', '2026-10-25 11:00'),
  (1001, 5, NULL,                 '2026-11-03 10:00');
