# Sistema de Gestão do Canil - 10° BAEP

Sistema web para cadastro e acompanhamento dos cães do canil, condutores,
histórico de saúde (vacinas, medicamentos, pesagens), treinamentos, documentos
e geração de fichas/relatórios em PDF. Login local (usuário/senha) com suporte
pronto para autenticação via **Login Único (gov.br)**.

## 1. Rodando localmente (Windows, Mac ou Linux)

Pré-requisito: Python 3.11+ instalado.

```bash
# 1. Entre na pasta do projeto
cd canil_baep

# 2. Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente (copie o exemplo)
cp .env.example .env            # Windows: copy .env.example .env

# 5. Crie o banco de dados local
python manage.py migrate

# 6. Crie seu usuário administrador
python manage.py createsuperuser

# 7. Rode o servidor
python manage.py runserver
```

Acesse:
- **http://127.0.0.1:8000/** — tela de login e o sistema
- **http://127.0.0.1:8000/admin/** — painel administrativo (CRUD rápido, útil para cadastro em massa)

Sem preencher as variáveis `GOVBR_*` no `.env`, o sistema funciona normalmente com
login usuário/senha — o botão "Entrar com gov.br" só aparece quando configurado.

## 2. Ativando o login com gov.br

O login com gov.br usa o protocolo oficial **Login Único** (OAuth2 + PKCE),
já implementado em `core/govbr.py`. Documentação oficial:
https://acesso.gov.br/roteiro-tecnico/iniciarintegracao.html

**Passo a passo:**

1. Solicite a credencial de teste (ambiente de homologação/staging) em:
   https://acesso.gov.br/roteiro-tecnico/solicitacaocredencialprocesso.html
   — isso é feito pelo órgão (10° BAEP) junto ao gov.br e normalmente exige
   um responsável técnico e institucional cadastrado.
2. Ao solicitar, informe a URL de retorno (redirect_uri). Para testes locais,
   siga a orientação oficial de criar um domínio local de desenvolvimento
   (ex: `local.canil10baep.gov.br` apontando para `127.0.0.1` no seu arquivo
   `hosts`), pois o gov.br staging normalmente não aceita `localhost` puro.
   Já em produção, será a URL real do sistema hospedado, ex:
   `https://canil.10baep.gov.br/accounts/govbr/callback/`.
3. Depois de aprovado, você recebe `client_id` e `client_secret`. Preencha no `.env`:
   ```
   GOVBR_ENV=staging
   GOVBR_CLIENT_ID=<recebido do gov.br>
   GOVBR_CLIENT_SECRET=<recebido do gov.br>
   GOVBR_REDIRECT_URI=<a mesma URL cadastrada no passo 2>
   ```
4. Reinicie o servidor. O botão "Entrar com gov.br" aparece automaticamente
   na tela de login.
5. Quando for para produção, troque `GOVBR_ENV=production` e solicite a
   credencial de produção (mesmo link acima).

**Como funciona no código:**
- `core/govbr.py` — monta a URL de autorização (com PKCE), troca o código
  por token e consulta os dados do cidadão (nome, e-mail, CPF).
- `core/views.py` — `govbr_login`, `govbr_callback`, `govbr_logout`: o usuário
  é criado/logado automaticamente no primeiro acesso, usando o **CPF como
  username**. Um administrador pode depois vincular esse usuário a um
  registro de `Condutor` pelo `/admin/`.
- O login local continua disponível como alternativa (ex: para contas de
  serviço/administração que não usam CPF via gov.br).

## Estrutura

- `core/models.py` — Cão, Condutor, Vacina, Medicamento, Pesagem, Treinamento, Documento
- `core/views.py` — cadastro, edição, exclusão, ficha do cão, relatório mensal, login gov.br
- `core/govbr.py` — integração OAuth2/PKCE com o Login Único
- `core/pdf_utils.py` — geração da ficha para porta do box e do relatório mensal em PDF
- `core/templates/` — telas do sistema

## 3. Deploy (Railway ou Render)

1. Suba este projeto para um repositório no GitHub (o `.gitignore` já exclui
   `.env`, `db.sqlite3` e mídia local — nunca comite o `.env` real).
2. Crie um novo projeto na plataforma escolhida e conecte o repositório.
3. Adicione um banco PostgreSQL — a variável `DATABASE_URL` é detectada automaticamente.
4. Defina as variáveis de ambiente (as mesmas do `.env.example`, com valores reais):
   - `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
   - `GOVBR_ENV`, `GOVBR_CLIENT_ID`, `GOVBR_CLIENT_SECRET`, `GOVBR_REDIRECT_URI` (com a URL de produção)
5. O `Procfile` já roda as migrações e sobe o servidor com Gunicorn.
6. Após o primeiro deploy, crie o superusuário pelo terminal da plataforma:
   ```bash
   python manage.py createsuperuser
   ```

## Próximos incrementos sugeridos

- Alertas automáticos de vacinas/próximas doses vencendo
- Gráfico de evolução de peso na ficha do cão
- Exportação de relatórios em Excel
- Vincular automaticamente usuário gov.br → Condutor por CPF/matrícula
- Permissões por papel (veterinário, condutor, administrador)
