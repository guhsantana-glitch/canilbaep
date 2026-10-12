# Sistema de Gestão do Canil - 10° BAEP

Sistema web para cadastro e acompanhamento dos cães do canil, condutores,
veterinários responsáveis, histórico de saúde (vacinas, medicamentos, pesagens),
treinamentos com gráfico de evolução, documentos e geração de fichas/relatórios em PDF.
Login local (usuário/senha), com painel próprio para o administrador cadastrar
outros usuários sem depender do /admin/ do Django.

Desenvolvido pelo SD PM 161844-0 Gava.

## Novidades desta versão

- Corrigido bug em que as datas (nascimento/ingresso) apareciam em branco ao editar um cão
- Cadastro de **Veterinários responsáveis** (criar, editar, excluir)
- Catálogo de **Tipos de vacina** (criar, editar, excluir) — usado como lista suspensa ao lançar uma vacina no cão
- Botões de **editar e excluir** para vacinas, medicamentos, pesagens, treinamentos e documentos na ficha do cão
- **Gráfico de evolução do treinamento** (nota de 0 a 10 por avaliação, lançada em cada treinamento)
- Espaço reservado para os **logotipos do canil e do 10° BAEP** nos PDFs (`static/logos/`, veja o arquivo `LEIA-ME.txt` lá dentro)
- Rodapé do sistema com o crédito de desenvolvimento
- **Login gov.br removido** — autenticação apenas local
- **Painel de usuários** (menu "Usuários", visível só para superusuário): cria/edita/exclui usuários do sistema. Todo usuário criado tem acesso completo às funções do sistema, mas só entra no `/admin/` do Django se a caixinha "Acesso ao painel Admin" for marcada

## 1. Rodando localmente (Windows, Mac ou Linux)

Pré-requisito: Python 3.11+ instalado.

```bash
cd canil_baep
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse:
- **http://127.0.0.1:8000/** — tela de login e o sistema
- **http://127.0.0.1:8000/admin/** — painel administrativo do Django (opcional, uso avançado)

> ⚠️ Se você já tinha rodado uma versão anterior deste projeto, o banco de dados
> mudou (novos campos e tabelas). Apague o arquivo `db.sqlite3` antigo antes do
> `python manage.py migrate` para começar limpo, ou me avise que te ajudo a
> migrar os dados existentes sem perder nada.

## 2. Cadastrando outros usuários (sem usar o /admin/)

1. Entre com o usuário superusuário (criado com `createsuperuser`)
2. No menu superior, clique em **Usuários**
3. Clique em **+ Novo usuário**, defina nome de usuário e senha
4. Deixe a caixinha **"Acesso ao painel Admin"** desmarcada para usuários comuns
   (eles terão acesso completo a cães, condutores, veterinários, vacinas,
   relatórios etc., mas não conseguirão entrar em `/admin/`)
5. Marque essa caixinha apenas para quem você quiser que também acesse o
   painel administrativo do Django

## Estrutura

- `core/models.py` — Cão, Condutor, Veterinário, TipoVacina, Vacina, Medicamento, Pesagem, Treinamento, Documento
- `core/views.py` — cadastro, edição, exclusão, ficha do cão, relatório mensal, gestão de usuários
- `core/pdf_utils.py` — geração da ficha para porta do box e do relatório mensal em PDF (com espaço para logotipos)
- `core/templates/` — telas do sistema
- `canis/` — multi-canil (modelo Canil, vínculo usuário-canil, middleware de escopo)
- `gestaocanis/` — painel do gestor geral (canis, usuários, uso)
- `static/logos/` — coloque aqui `logo_canil.png` e `logo_baep.png`

## Multi-canil (modo SaaS)

O sistema atende vários canis setoriais com dados totalmente isolados:

1. Entre como superusuário e abra **Gestão** no menu — o painel mostra
   quantos canis estão cadastrados/ativos, total de cães e usuários, e o
   uso por canil.
2. Cadastre cada canil (**+ Novo canil**) e seus usuários
   (**Gerenciar usuários → + Novo usuário**, definindo canil e papel).
3. Clique em **Acessar** no canil para operar dentro dele (o nome do canil
   aparece ao lado do usuário logado). Cada operador comum entra direto
   no seu canil, sem ver dados dos outros.
4. Desativar um canil bloqueia o acesso de seus usuários na hora.

## 3. Deploy (Render + Neon — gratuito e sem expirar)

Banco: use o **Neon** (Postgres gratuito que não expira, igual ao AdestraPro).
Não use o Postgres do Render (o plano free expira e apaga os dados).

1. Crie conta em https://neon.tech → **New Project** (região `US East`/mais próxima)
   → copie a **Connection string** com pooler (`...-pooler...`, `sslmode=require`).
2. No https://dashboard.render.com, abra o Web Service `canilbaep`
   (ou crie um **New → Web Service** apontando este repositório):
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn canil_baep.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
3. Em **Environment**, defina:
   - `DATABASE_URL` = connection string do Neon (cole a URL com pooler)
   - `DJANGO_DEBUG=False`
   - `DJANGO_SECRET_KEY` = Generate (ou uma chave longa)
   - `DJANGO_ALLOWED_HOSTS=canilbaep.onrender.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://canilbaep.onrender.com`
4. **Deploy** (o `build.sh` já roda `collectstatic` + `migrate`).
5. No **Shell** do serviço, crie o gestor geral:
   ```bash
   python manage.py createsuperuser
   ```
6. Acesse `https://canilbaep.onrender.com/login/` → Gestão → cadastre
   unidades, canis e usuários.

> Notas do plano free: o site "dorme" após ~15 min sem uso (a primeira
> abertura demora ~1 min); fotos/documentos somem a cada novo deploy
> (disco efêmero) — quando quiser, evoluímos para armazenamento externo.

## 4. Fotos e documentos permanentes (storage gratuito, sem cartão)

Sem isso, fotos/documentos enviados no site somem a cada deploy do Render.
Com um bucket S3 (Cloudflare R2 ou Supabase), viram uma "pasta na nuvem"
permanente. O R2 pede cartão (só cobra se passar de 10 GB); o
**Supabase não pede cartão** — recomendado:

1. Crie conta em https://supabase.com → **New Project** (`canilbaep`,
   região **South America (São Paulo)**, crie uma senha do banco).
2. No projeto → **Storage** → **New bucket** (`canilbaep-media**, **Public** ligado).
3. Gere as chaves S3: **Project Settings → API → S3 Access Keys**
   (ou **Storage → S3 access keys**, conforme a versão do painel) →
   anote endpoint (`https://xxx.supabase.co/storage/v1/s3`), access key e
   secret key. A URL pública base é
   `https://xxx.supabase.co/storage/v1/object/public`.
4. No Render → serviço `canilbaep` → **Environment**, adicione:
   - `STORAGE_BUCKET=canilbaep-media`
   - `STORAGE_ENDPOINT_URL=https://xxx.supabase.co/storage/v1/s3`
   - `STORAGE_ACCESS_KEY=...`
   - `STORAGE_SECRET_KEY=...`
   - `STORAGE_PUBLIC_URL=xxx.supabase.co/storage/v1/object/public`
5. Redeploy. Novos uploads passam a ir para o bucket e sobrevivem aos deploys.
   (Arquivos antigos precisam ser re-anexados uma vez.)

Alternativa com cartão: Cloudflare R2 (10 GB free) — mesmo esquema,
preenchendo as mesmas variáveis `STORAGE_*` com os dados do R2.

## Próximos incrementos sugeridos

- Alertas automáticos de vacinas/próximas doses vencendo
- Gráfico de evolução de peso na ficha do cão (mesmo estilo do gráfico de treinamento)
- Exportação de relatórios em Excel
- Login com gov.br (fica pendente para quando a credencial oficial for solicitada)
