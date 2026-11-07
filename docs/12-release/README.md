# Checkpoint 5 — Release candidate (`v1.0.0`)

A `v1.0.0` é a versão candidata à entrega final. Ela reúne o MVP (`v0.1.0`), a evolução (`v0.2.0`) e as correções
encontradas na [Entrega 8](../11-testes/), e está publicada na internet (RNF10).

**Endereço público:** https://natcurti.pythonanywhere.com

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Administradora | juliana@empresa.com | atende123 |
| Atendente | carlos@empresa.com | atende123 |
| Cliente | maria@souzacomercio.com.br | atende123 |

## 1. O que entra na versão

| Origem | Conteúdo |
| --- | --- |
| `v0.1.0` (Checkpoint 2) | Cadastro e login, tickets do cliente, fila, atendimento e administração (RF01, RF02, RF04 a RF12) |
| `v0.2.0` (Checkpoints 3 e 4) | Notas internas, prioridade, avaliação e painel de indicadores (RF13, RF16, RF17, RF18) |
| Entrega 8 | Correções dos BUG-08, BUG-09 e BUG-12: limite de tamanho dos textos e quebra de palavras longas |
| Este checkpoint | Preparação para o servidor e publicação no PythonAnywhere |

**Situação final:**
- 15 dos 21 requisitos funcionais, todos os essenciais;
- 12 das 14 regras de negócio;
- 141 testes automatizados passando;
- nenhum defeito aberto.

## 2. Preparação para o servidor

O mesmo código roda na máquina de quem desenvolve e no servidor. O que muda fica no arquivo `.env`, que nunca vai para o GitHub:

| Configuração | Na máquina (padrão) | No servidor |
| --- | --- | --- |
| `DEBUG` | `True`: mostra os detalhes de um erro | `False`: mostra as páginas 403 e 404 do sistema, sem detalhes técnicos |
| `SECRET_KEY` | Uma chave fixa de desenvolvimento | Uma chave própria e secreta. Com `DEBUG=False`, o sistema se recusa a iniciar com a chave de desenvolvimento. |
| `ALLOWED_HOSTS` | `localhost` | O endereço do site |
| Cookies de sessão | Funcionam em HTTP | Só trafegam por HTTPS |

A verificação de segurança do Django para servidores (`python manage.py check --deploy`) passa sem avisos. Dois
avisos foram silenciados de propósito, com o motivo explicado em `config/settings.py`:
- **Redirecionamento para HTTPS:** o próprio PythonAnywhere já faz.
- **HSTS:** não faz sentido num subdomínio de outra empresa.

## 3. Como publicar no PythonAnywhere

O PythonAnywhere tem um plano gratuito que roda Django com SQLite. O site fica em `https://<usuario>.pythonanywhere.com`.
Nos comandos abaixo, troque **`natcurti`** pelo seu nome de usuário, se for outro.

### 3.1 Baixar o projeto e instalar

No painel do PythonAnywhere, abra **Consoles → Bash** e rode:

```bash
git clone https://github.com/natcurti/projeto_atende_mais.git
cd projeto_atende_mais
python3.13 -m venv ~/.virtualenvs/atende
source ~/.virtualenvs/atende/bin/activate
pip install -r requirements.txt
```

Se o `python3.13` não existir, use `python3.12` ou `python3.11`. Qualquer versão a partir da 3.10 funciona, mas
anote qual usou: a aba **Web** vai pedir a mesma.

### 3.2 Criar o `.env` do servidor

Ainda no console, gere uma chave secreta e crie o arquivo:

```bash
CHAVE=$(python -c "from django.core.management.utils import get_random_secret_key as g; print(g())")
cat > .env <<EOF
DEBUG=False
SECRET_KEY=$CHAVE
ALLOWED_HOSTS=natcurti.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://natcurti.pythonanywhere.com
SQLITE_ARQUIVO=db.sqlite3
EOF
```

### 3.3 Preparar o banco e os arquivos estáticos

```bash
python manage.py migrate
python manage.py carregar_dados_exemplo
python manage.py collectstatic --noinput
python manage.py check --deploy
```

O último comando deve terminar com `System check identified no issues (2 silenced).`

### 3.4 Criar o site

1. Na aba **Web**, clique em **Add a new web app** → **Next** → **Manual configuration** (não escolha "Django") → a mesma versão de Python do passo 3.1 → **Next**.
2. Na mesma aba, preencha:

| Campo | Valor |
| --- | --- |
| **Source code** | `/home/natcurti/projeto_atende_mais` |
| **Working directory** | `/home/natcurti/projeto_atende_mais` |
| **Virtualenv** | `/home/natcurti/.virtualenvs/atende` |

3. Em **Static files**, adicione uma linha:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/natcurti/projeto_atende_mais/staticfiles` |

4. Clique no link do **WSGI configuration file** (algo como `/var/www/natcurti_pythonanywhere_com_wsgi.py`), apague todo o conteúdo e cole:

```python
import os
import sys

caminho = "/home/natcurti/projeto_atende_mais"
if caminho not in sys.path:
    sys.path.insert(0, caminho)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Clique em **Save**.

5. De volta à aba **Web**, ligue **Force HTTPS** e clique no botão verde **Reload**.

Abra `https://natcurti.pythonanywhere.com`: deve aparecer a tela de entrada do atende+, com as cores e a fonte do sistema.

### 3.5 Se algo der errado

| Sintoma | Causa provável | Onde olhar |
| --- | --- | --- |
| "Something went wrong" | Erro ao iniciar o Django | **Error log**, na aba Web: a última linha diz o que faltou |
| `ImproperlyConfigured: ... SECRET_KEY` | O `.env` não foi criado ou está fora da pasta do projeto | Passo 3.2 |
| "Bad Request (400)" | O endereço não está em `ALLOWED_HOSTS` | `.env` |
| Página sem cores, só texto | Falta o `collectstatic` ou o mapeamento de `/static/` | Passos 3.3 e 3.4 |
| "CSRF verification failed" ao entrar | `CSRF_TRUSTED_ORIGINS` diferente do endereço com `https://` | `.env` |

Depois de mudar o `.env` ou o código, clique em **Reload** na aba Web.

### 3.6 Atualizar o site com uma versão nova

```bash
cd ~/projeto_atende_mais
git pull
source ~/.virtualenvs/atende/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Depois, clique em **Reload** na aba Web.

### 3.7 Manutenção do plano gratuito

- O site gratuito fica no ar por 3 meses. Para renovar, clique em **Run until 3 months from today** na aba Web. Faça isso antes da apresentação, por garantia.
- Para recomeçar a demonstração com os dados originais:

```bash
rm db.sqlite3
python manage.py migrate
python manage.py carregar_dados_exemplo
```

Depois, clique em **Reload**.

## 4. Verificação depois da publicação

| Verificação | Como |
| --- | --- |
| Site no ar com HTTPS | Abrir o endereço; o cadeado aparece no navegador |
| Login dos três perfis | Juliana, Carlos e Maria, cada um vê o próprio menu |
| Fluxo completo | Maria abre um ticket → Carlos assume e resolve → Maria avalia |
| Painel | Juliana abre o *Painel* nos três períodos |
| Páginas de erro | Um endereço inexistente mostra a página 404 do sistema, sem detalhes técnicos |
| Celular | Abrir o endereço no celular e fazer o fluxo da Maria |
