-- ==========================================================
-- atende+ — consultas de exemplo (Entrega 4)
-- Mostram que o modelo responde às perguntas das telas.
-- Executar depois de schema.sql e dados-exemplo.sql.
-- ==========================================================

-- 1. Fila de atendimento (RF08, RN10): tickets não resolvidos, atrasados primeiro, depois por prazo.
SELECT t.id                                 AS numero,
       t.titulo,
       c.empresa                            AS cliente,
       cat.nome                             AS categoria,
       t.prioridade,
       t.situacao,
       COALESCE(a.nome, 'Ninguém')          AS atendente,
       DATE_FORMAT(t.prazo, '%d/%m %H:%i')  AS prazo,
       (t.prazo < NOW())                    AS atrasado
FROM ticket t
JOIN usuario   c   ON c.id = t.cliente_id
JOIN categoria cat ON cat.id = t.categoria_id
LEFT JOIN usuario a ON a.id = t.atendente_id
WHERE t.situacao IN ('aberto', 'em_atendimento', 'aguardando_cliente')
ORDER BY (t.prazo < NOW()) DESC, t.prazo;

-- 2. Meus tickets (RF07, RN08): só os tickets da cliente Maria Souza (id 5).
SELECT t.id AS numero, t.titulo, cat.nome AS categoria, t.situacao, t.atualizado_em
FROM ticket t
JOIN categoria cat ON cat.id = t.categoria_id
WHERE t.cliente_id = 5
ORDER BY t.atualizado_em DESC;

-- 3. Conversa do ticket #1003 como o CLIENTE vê (RN08): sem notas internas.
SELECT DATE_FORMAT(m.criada_em, '%d/%m %H:%i') AS quando, u.nome AS autor, m.texto
FROM mensagem m
JOIN usuario u ON u.id = m.autor_id
WHERE m.ticket_id = 1003 AND m.interna = FALSE
ORDER BY m.criada_em;

-- 4. Indicador: quantidade de tickets por situação (RF18).
SELECT situacao, COUNT(*) AS quantidade
FROM ticket
GROUP BY situacao
ORDER BY quantidade DESC;

-- 5. Indicador: tempo médio de resolução por categoria, em horas (RF18).
SELECT cat.nome AS categoria,
       COUNT(*) AS resolvidos,
       ROUND(AVG(TIMESTAMPDIFF(MINUTE, t.aberto_em, t.resolvido_em)) / 60, 1) AS horas_em_media
FROM ticket t
JOIN categoria cat ON cat.id = t.categoria_id
WHERE t.resolvido_em IS NOT NULL
GROUP BY cat.nome
ORDER BY horas_em_media;

-- 6. Indicador: nota média das avaliações por atendente (RF18).
SELECT a.nome AS atendente, COUNT(*) AS avaliacoes, ROUND(AVG(av.nota), 1) AS nota_media
FROM avaliacao av
JOIN ticket  t ON t.id = av.ticket_id
JOIN usuario a ON a.id = t.atendente_id
GROUP BY a.nome
ORDER BY nota_media DESC;
