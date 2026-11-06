-- ==========================================================
-- atende+ — modelo físico do banco de dados (Entrega 4)
-- SGBD oficial: SQLite 3.35 ou mais recente (já vem com o Python)
--
-- Como usar (o banco inteiro fica no arquivo atende_mais.db):
--   sqlite3 atende_mais.db ".read schema.sql" ".read dados-exemplo.sql"
--
-- No sistema final, quem cria as tabelas é o Django (python manage.py migrate)
-- a partir dos models, seguindo este mesmo modelo.
--
-- As restrições CHECK garantem no próprio banco as regras de
-- negócio que dependem só dos dados de uma linha (ex.: RN02,
-- RN03, RN11). Regras que dependem de tempo ou de quem está
-- logado (ex.: RN05, RN07, RN09) ficam na aplicação Django.
--
-- Particularidades do SQLite:
--   * O tamanho de VARCHAR(n) não é imposto pelo SQLite; o Django valida antes de gravar.
--   * Chaves estrangeiras só valem com PRAGMA foreign_keys = ON (o Django liga sozinho).
--   * Datas são gravadas como texto no formato AAAA-MM-DD HH:MM:SS, em UTC.
-- ==========================================================

PRAGMA foreign_keys = ON;

-- ---------- usuario ----------
-- Clientes, atendentes e administradores (RF01, RF04).
CREATE TABLE usuario (
    id             INTEGER      PRIMARY KEY AUTOINCREMENT,
    nome           VARCHAR(150) NOT NULL,
    email          VARCHAR(254) NOT NULL,
    senha_hash     VARCHAR(128) NOT NULL,                 -- RNF03: nunca a senha em texto puro
    perfil         VARCHAR(13)  NOT NULL,
    empresa        VARCHAR(150) NULL,                     -- obrigatório só para clientes
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,    -- RN12: desativar em vez de excluir
    criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso  DATETIME     NULL,

    CONSTRAINT uq_usuario_email   UNIQUE (email),
    CONSTRAINT ck_usuario_perfil  CHECK (perfil IN ('cliente', 'atendente', 'administrador')),
    CONSTRAINT ck_usuario_empresa CHECK (perfil <> 'cliente' OR empresa IS NOT NULL)
);

-- ---------- categoria ----------
-- Assuntos dos tickets, mantidos pelo administrador (RF05).
CREATE TABLE categoria (
    id         INTEGER     PRIMARY KEY AUTOINCREMENT,
    nome       VARCHAR(60) NOT NULL,
    ativa      BOOLEAN     NOT NULL DEFAULT TRUE,         -- RN12
    criada_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_categoria_nome UNIQUE (nome)
);

-- ---------- ticket ----------
-- O pedido de suporte (RF06). O id é o número exibido (#1042), começando em 1000 (RN01).
CREATE TABLE ticket (
    id             INTEGER      PRIMARY KEY AUTOINCREMENT,
    titulo         VARCHAR(120) NOT NULL,
    descricao      TEXT         NOT NULL,
    situacao       VARCHAR(18)  NOT NULL DEFAULT 'aberto',   -- RN02, RN03
    prioridade     VARCHAR(7)   NOT NULL DEFAULT 'media',    -- RN09
    cliente_id     INTEGER      NOT NULL,
    atendente_id   INTEGER      NULL,                        -- vazio enquanto o ticket está Aberto
    categoria_id   INTEGER      NOT NULL,
    aberto_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prazo          DATETIME     NOT NULL,                    -- aberto_em + tempo da prioridade (RN09)
    atualizado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido_em   DATETIME     NULL,
    fechado_em     DATETIME     NULL,

    CONSTRAINT fk_ticket_cliente    FOREIGN KEY (cliente_id)   REFERENCES usuario (id),
    CONSTRAINT fk_ticket_atendente  FOREIGN KEY (atendente_id) REFERENCES usuario (id),
    CONSTRAINT fk_ticket_categoria  FOREIGN KEY (categoria_id) REFERENCES categoria (id),
    CONSTRAINT ck_ticket_situacao   CHECK (situacao IN ('aberto', 'em_atendimento', 'aguardando_cliente', 'resolvido', 'fechado')),
    CONSTRAINT ck_ticket_prioridade CHECK (prioridade IN ('urgente', 'alta', 'media', 'baixa')),
    -- RN03 e RN04: Aberto <=> sem atendente
    CONSTRAINT ck_ticket_atendente  CHECK ((situacao = 'aberto') = (atendente_id IS NULL)),
    CONSTRAINT ck_ticket_prazo      CHECK (prazo > aberto_em),
    CONSTRAINT ck_ticket_resolvido  CHECK (situacao NOT IN ('resolvido', 'fechado') OR resolvido_em IS NOT NULL),
    CONSTRAINT ck_ticket_fechado    CHECK (situacao <> 'fechado' OR fechado_em IS NOT NULL)
);

-- RN01: o próximo ticket criado recebe o número 1000.
INSERT INTO sqlite_sequence (name, seq) VALUES ('ticket', 999);

CREATE INDEX ix_ticket_situacao_prazo ON ticket (situacao, prazo);   -- ordenação da fila (RF08, RN10)
CREATE INDEX ix_ticket_cliente        ON ticket (cliente_id);        -- Meus tickets (RF07)
CREATE INDEX ix_ticket_atendente      ON ticket (atendente_id);      -- filtro por atendente (RF08)
CREATE INDEX ix_ticket_categoria      ON ticket (categoria_id);

-- ---------- mensagem ----------
-- Conversa do ticket: mensagens ao cliente e notas internas (RF12, RF13).
CREATE TABLE mensagem (
    id         INTEGER  PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER  NOT NULL,
    autor_id   INTEGER  NOT NULL,
    texto      TEXT     NOT NULL,
    interna    BOOLEAN  NOT NULL DEFAULT FALSE,           -- RN08: notas internas não aparecem para o cliente
    criada_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mensagem_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT fk_mensagem_autor  FOREIGN KEY (autor_id)  REFERENCES usuario (id),
    CONSTRAINT ck_mensagem_texto  CHECK (length(trim(texto)) > 0)
);

CREATE INDEX ix_mensagem_ticket ON mensagem (ticket_id, criada_em);
CREATE INDEX ix_mensagem_autor  ON mensagem (autor_id);

-- ---------- anexo ----------
-- Arquivos enviados na abertura (mensagem_id vazio) ou junto de uma mensagem (RF14, RN14).
CREATE TABLE anexo (
    id             INTEGER      PRIMARY KEY AUTOINCREMENT,
    ticket_id      INTEGER      NOT NULL,
    mensagem_id    INTEGER      NULL,
    enviado_por_id INTEGER      NOT NULL,
    arquivo        VARCHAR(255) NOT NULL,                  -- caminho do arquivo no servidor
    nome_original  VARCHAR(255) NOT NULL,
    tipo           VARCHAR(4)   NOT NULL,
    tamanho_bytes  INTEGER      NOT NULL,
    enviado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_anexo_ticket      FOREIGN KEY (ticket_id)      REFERENCES ticket (id),
    CONSTRAINT fk_anexo_mensagem    FOREIGN KEY (mensagem_id)    REFERENCES mensagem (id),
    CONSTRAINT fk_anexo_enviado_por FOREIGN KEY (enviado_por_id) REFERENCES usuario (id),
    CONSTRAINT ck_anexo_tipo        CHECK (tipo IN ('jpg', 'png', 'pdf')),
    CONSTRAINT ck_anexo_tamanho     CHECK (tamanho_bytes BETWEEN 1 AND 5242880)   -- até 5 MB
);

CREATE INDEX ix_anexo_ticket      ON anexo (ticket_id);
CREATE INDEX ix_anexo_mensagem    ON anexo (mensagem_id);
CREATE INDEX ix_anexo_enviado_por ON anexo (enviado_por_id);

-- ---------- historico ----------
-- Registro automático de cada mudança no ticket (RN13).
CREATE TABLE historico (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    ticket_id       INTEGER      NOT NULL,
    autor_id        INTEGER      NOT NULL,
    campo           VARCHAR(10)  NOT NULL,
    valor_anterior  VARCHAR(150) NULL,                     -- vazio quando não havia valor (ex.: sem atendente)
    valor_novo      VARCHAR(150) NULL,
    alterado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_historico_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT fk_historico_autor  FOREIGN KEY (autor_id)  REFERENCES usuario (id),
    CONSTRAINT ck_historico_campo  CHECK (campo IN ('situacao', 'atendente', 'prioridade')),
    CONSTRAINT ck_historico_mudou  CHECK (valor_anterior IS NOT valor_novo)   -- só grava se algo mudou
);

CREATE INDEX ix_historico_ticket ON historico (ticket_id, alterado_em);
CREATE INDEX ix_historico_autor  ON historico (autor_id);

-- ---------- avaliacao ----------
-- Nota do cliente depois da resolução: uma por ticket (RF16, RN11).
CREATE TABLE avaliacao (
    id          INTEGER      PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER      NOT NULL,
    nota        SMALLINT     NOT NULL,
    comentario  VARCHAR(500) NULL,
    avaliado_em DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_avaliacao_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT uq_avaliacao_ticket UNIQUE (ticket_id),      -- RN11: só uma avaliação por ticket
    CONSTRAINT ck_avaliacao_nota   CHECK (nota BETWEEN 1 AND 5)
);
