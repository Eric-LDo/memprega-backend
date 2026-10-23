# Me Emprega · Backend

API FastAPI para criar, atualizar, consultar e excluir currículos, com geração de PDF A4 de texto selecionável. PostgreSQL + SQLAlchemy e migrations Alembic. O formulário usa um documento validado armazenado em coluna JSON do banco SQL; não há um banco NoSQL separado.

## Executar tudo com Docker (recomendado)

Clone os dois repositórios lado a lado, mantendo os nomes:

```sh
git clone https://github.com/Eric-LDo/memprega-backend.git
git clone https://github.com/Eric-LDo/memprega-frontend.git
cd memprega-backend
docker compose --profile full up --build -d
```

- Frontend: http://localhost:3000
- API / Swagger: http://localhost:8000/docs
- Saúde: http://localhost:8000/health

O banco usa volume persistente. A API espera o PostgreSQL ficar saudável e executa `alembic upgrade head` antes de iniciar. O frontend espera a API. Para subir apenas banco e API: `docker compose up --build -d`. Para parar: `docker compose --profile full down` (preserva os dados). Credenciais padrão são apenas para desenvolvimento local; configure `POSTGRES_PASSWORD` antes de usar outro ambiente. Portas são expostas apenas em localhost.

## Desenvolvimento sem Docker

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Sem `.env`, usa SQLite local. Para PostgreSQL, copie `.env.example` para `.env` e configure `DATABASE_URL`. Migrations não são substituídas por `create_all` na inicialização.

## Contrato

`POST /api/v1/resumes` recebe nome, e-mail, telefone, cidade, cargo desejado, resumo, links, experiências, formações, habilidades e idiomas. Retorna `{id, token, data}`. Datas são `YYYY-MM`. Campos opcionais podem ser vazios; se uma experiência ou formação for adicionada, seu período e campos principais precisam ser preenchidos.

Rotas protegidas por `Authorization: Bearer <token>`:

| Método | Rota | Resultado |
| --- | --- | --- |
| GET | `/api/v1/resumes/{id}` | Dados do currículo |
| PUT | `/api/v1/resumes/{id}` | Substitui dados validados |
| GET | `/api/v1/resumes/{id}/pdf` | Download do PDF |
| DELETE | `/api/v1/resumes/{id}` | Exclusão definitiva |

O token aleatório de 256 bits é retornado somente na criação e armazenado como SHA-256 no banco. Não há listagem pública. A credencial e o rascunho ficam no navegador: quem possuir a credencial pode acessar esse currículo; perder o armazenamento local perde o acesso. Este MVP não inclui login de contas, recuperação entre dispositivos ou integração real com a Gupy. Antes de expor na internet, integrar a autenticação do Me Emprega, HTTPS, limites de requisições no proxy e política de retenção. Não inserir segredos nos repositórios.

## Migrations e testes

```sh
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
pytest -q
```

`schema.sql` documenta o DDL PostgreSQL gerado pela migration. Use Alembic para instalar o banco, não ambos. Testes verificam o ciclo CRUD, autorização, validação, acentos, escaping e paginação do PDF.

## Referências

- [FastAPI e bancos SQL](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
