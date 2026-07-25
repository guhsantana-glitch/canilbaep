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
- `static/logos/` — coloque aqui `logo_canil.png` e `logo_baep.png`

## 3. Deploy (Railway ou Render)

1. Suba este projeto para um repositório no GitHub (o `.gitignore` já exclui
   `.env`, `db.sqlite3` e mídia local).
2. Crie um novo projeto na plataforma escolhida e conecte o repositório.
3. Adicione um banco PostgreSQL — a variável `DATABASE_URL` é detectada automaticamente.
4. Defina as variáveis de ambiente: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`,
   `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
5. O `Procfile` já roda as migrações e sobe o servidor com Gunicorn.
6. Após o primeiro deploy, crie o superusuário pelo terminal da plataforma:
   ```bash
   python manage.py createsuperuser
   ```

## Próximos incrementos sugeridos

- Alertas automáticos de vacinas/próximas doses vencendo
- Gráfico de evolução de peso na ficha do cão (mesmo estilo do gráfico de treinamento)
- Exportação de relatórios em Excel
- Login com gov.br (fica pendente para quando a credencial oficial for solicitada)
