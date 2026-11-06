-- ==========================================================
-- atende+ — modelo físico do banco de dados (Entrega 4)
-- SGBD: MariaDB 10.5+ ou MySQL 8.0.16+ (os dois aceitam este script)
--
-- Como usar:
--   CREATE DATABASE atende_mais CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   USE atende_mais;
--   SOURCE schema.sql;
--
-- As restrições CHECK garantem no próprio banco as regras de
-- negócio que dependem só dos dados de uma linha (ex.: RN02,
-- RN03, RN11). Regras que dependem de tempo ou de quem está
-- logado (ex.: RN05, RN07, RN09) ficam na aplicação Django.
-- Datas e horas são gravadas em UTC (padrão do Django).
-- ==========================================================

-- ---------- usuario ----------
-- Clientes, atendentes e administradores (RF01, RF04).
CREATE TABLE usuario (
    id             INT          NOT NULL AUTO_INCREMENT,
    nome           VARCHAR(150) NOT NULL,
    email          VARCHAR(254) NOT NULL,
    senha_hash     VARCHAR(128) NOT NULL,                 -- RNF03: nunca a senha em texto puro
    perfil         VARCHAR(13)  NOT NULL,
    empresa        VARCHAR(150) NULL,                     -- obrigatório só para clientes
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,    -- RN12: desativar em vez de excluir
    criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso  DATETIME     NULL,

    CONSTRAINT pk_usuario         PRIMARY KEY (id),
    CONSTRAINT uq_usuario_email   UNIQUE (email),
    CONSTRAINT ck_usuario_perfil  CHECK (perfil IN ('cliente', 'atendente', 'administrador')),
    CONSTRAINT ck_usuario_empresa CHECK (perfil <> 'cliente' OR empresa IS NOT NULL)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ---------- categoria ----------
-- Assuntos dos tickets, mantidos pelo administrador (RF05).
CREATE TABLE categoria (
    id         INT         NOT NULL AUTO_INCREMENT,
    nome       VARCHAR(60) NOT NULL,
    ativa      BOOLEAN     NOT NULL DEFAULT TRUE,         -- RN12
    criada_em  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_categoria      PRIMARY KEY (id),
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ---------- ticket ----------
-- O pedido de suporte (RF06). O id é o número exibido (#1042), começando em 1000 (RN01).
CREATE TABLE ticket (
    id             INT          NOT NULL AUTO_INCREMENT,
    titulo         VARCHAR(120) NOT NULL,
    descricao      TEXT         NOT NULL,
    situacao       VARCHAR(18)  NOT NULL DEFAULT 'aberto',   -- RN02, RN03
    prioridade     VARCHAR(7)   NOT NULL DEFAULT 'media',    -- RN09
    cliente_id     INT          NOT NULL,
    atendente_id   INT          NULL,                        -- vazio enquanto o ticket está Aberto
    categoria_id   INT          NOT NULL,
    aberto_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prazo          DATETIME     NOT NULL,                    -- aberto_em + tempo da prioridade (RN09)
    atualizado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido_em   DATETIME     NULL,
    fechado_em     DATETIME     NULL,

    CONSTRAINT pk_ticket            PRIMARY KEY (id),
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
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci AUTO_INCREMENT = 1000;

CREATE INDEX ix_ticket_situacao_prazo ON ticket (situacao, prazo);   -- ordenação da fila (RF08, RN10)
-- cliente_id, atendente_id e categoria_id já ganham índice automático por serem chaves estrangeiras.

-- ---------- mensagem ----------
-- Conversa do ticket: mensagens ao cliente e notas internas (RF12, RF13).
CREATE TABLE mensagem (
    id         INT      NOT NULL AUTO_INCREMENT,
    ticket_id  INT      NOT NULL,
    autor_id   INT      NOT NULL,
    texto      TEXT     NOT NULL,
    interna    BOOLEAN  NOT NULL DEFAULT FALSE,           -- RN08: notas internas não aparecem para o cliente
    criada_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_mensagem        PRIMARY KEY (id),
    CONSTRAINT fk_mensagem_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT fk_mensagem_autor  FOREIGN KEY (autor_id)  REFERENCES usuario (id),
    CONSTRAINT ck_mensagem_texto  CHECK (CHAR_LENGTH(TRIM(texto)) > 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE INDEX ix_mensagem_ticket ON mensagem (ticket_id, criada_em);

-- ---------- anexo ----------
-- Arquivos enviados na abertura (mensagem_id vazio) ou junto de uma mensagem (RF14, RN14).
CREATE TABLE anexo (
    id             INT          NOT NULL AUTO_INCREMENT,
    ticket_id      INT          NOT NULL,
    mensagem_id    INT          NULL,
    enviado_por_id INT          NOT NULL,
    arquivo        VARCHAR(255) NOT NULL,                  -- caminho do arquivo no servidor
    nome_original  VARCHAR(255) NOT NULL,
    tipo           VARCHAR(4)   NOT NULL,
    tamanho_bytes  INT          NOT NULL,
    enviado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_anexo             PRIMARY KEY (id),
    CONSTRAINT fk_anexo_ticket      FOREIGN KEY (ticket_id)      REFERENCES ticket (id),
    CONSTRAINT fk_anexo_mensagem    FOREIGN KEY (mensagem_id)    REFERENCES mensagem (id),
    CONSTRAINT fk_anexo_enviado_por FOREIGN KEY (enviado_por_id) REFERENCES usuario (id),
    CONSTRAINT ck_anexo_tipo        CHECK (tipo IN ('jpg', 'png', 'pdf')),
    CONSTRAINT ck_anexo_tamanho     CHECK (tamanho_bytes BETWEEN 1 AND 5242880)   -- até 5 MB
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ---------- historico ----------
-- Registro automático de cada mudança no ticket (RN13).
CREATE TABLE historico (
    id              INT          NOT NULL AUTO_INCREMENT,
    ticket_id       INT          NOT NULL,
    autor_id        INT          NOT NULL,
    campo           VARCHAR(10)  NOT NULL,
    valor_anterior  VARCHAR(150) NULL,                     -- vazio quando não havia valor (ex.: sem atendente)
    valor_novo      VARCHAR(150) NULL,
    alterado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_historico        PRIMARY KEY (id),
    CONSTRAINT fk_historico_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT fk_historico_autor  FOREIGN KEY (autor_id)  REFERENCES usuario (id),
    CONSTRAINT ck_historico_campo  CHECK (campo IN ('situacao', 'atendente', 'prioridade')),
    CONSTRAINT ck_historico_mudou  CHECK (NOT (valor_anterior <=> valor_novo))   -- só grava se algo mudou
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE INDEX ix_historico_ticket ON historico (ticket_id, alterado_em);

-- ---------- avaliacao ----------
-- Nota do cliente depois da resolução: uma por ticket (RF16, RN11).
CREATE TABLE avaliacao (
    id          INT          NOT NULL AUTO_INCREMENT,
    ticket_id   INT          NOT NULL,
    nota        TINYINT      NOT NULL,
    comentario  VARCHAR(500) NULL,
    avaliado_em DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_avaliacao        PRIMARY KEY (id),
    CONSTRAINT fk_avaliacao_ticket FOREIGN KEY (ticket_id) REFERENCES ticket (id),
    CONSTRAINT uq_avaliacao_ticket UNIQUE (ticket_id),      -- RN11: só uma avaliação por ticket
    CONSTRAINT ck_avaliacao_nota   CHECK (nota BETWEEN 1 AND 5)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
