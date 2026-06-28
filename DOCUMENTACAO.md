# Documentação — sic-backend_v2

> **Propósito deste documento:** Registrar de forma completa e objetiva a estrutura, módulos, integrações, fluxos e estado atual desta segunda versão do backend do SIC (Sistema Interno Conticonsultoria), para permitir comparação com a versão anterior e embasar decisões de continuidade ou migração.

---

## 1. Visão Geral

O **sic-backend_v2** é uma API REST construída com **Flask** (Python 3.11), que serve como backend para o sistema interno da Conticonsultoria. Sua função principal é integrar e centralizar dados de múltiplos sistemas externos utilizados pela empresa, expondo-os a um frontend web.

**URL de produção do frontend:** `https://sic.conticonsultoria.cloud`  
**Porta padrão do backend:** `5000`  
**WSGI server em produção:** Gunicorn

### Sistemas externos integrados

| Sistema | Tipo | Finalidade |
|---|---|---|
| **Microsoft 365 / Azure AD** | OAuth2 + Graph API | Autenticação de usuários, grupos e canais do Teams |
| **PSOffice** | ERP (REST API + SQL Server) | Projetos, recursos, apontamentos de horas |
| **RD Station CRM** | CRM (REST API) | Negociações, pipeline comercial |
| **DeskManager** | Helpdesk (REST API) | Clientes, contratos, chamados de suporte |
| **MongoDB** | Banco NoSQL | Persistência de negociações, warmup, chamados internos |
| **Redis** | Cache | Armazenamento de tokens de sessão |
| **Power Automate** | Automação | Integração com fluxos da Microsoft (configurado, não implementado) |

---

## 2. Tecnologias e Dependências

```
Flask==3.0.3                  # Framework web principal
Flask-Cors==5.0.0             # Habilita CORS para o frontend
Flask-JWT-Extended==4.7.1     # Geração e validação de JWT
Flask-PyMongo==2.3.0          # Integração Flask + MongoDB
msal==1.31.0                  # Microsoft Authentication Library (OAuth2)
PyJWT==2.3.0                  # Manipulação de tokens JWT
pymongo==4.10.1               # Driver MongoDB
python-dotenv==1.0.1          # Carregamento de variáveis de ambiente
pytz==2024.2                  # Fusos horários
requests==2.32.3              # Chamadas HTTP para APIs externas
pydantic==1.10.2              # Validação de dados (versão 1.x)
pandas                        # Processamento de dados (notebooks e relatórios)
redis                         # Cache de sessão
pymssql                       # Conexão com SQL Server (PSOffice)
gunicorn                      # WSGI server para produção
beautifulsoup4                # Parsing HTML (templates de e-mail)
six                           # Compatibilidade Python 2/3
```

---

## 3. Estrutura de Diretórios

```
sic-backend_v2/
├── app/                          # Aplicação Flask principal
│   ├── __init__.py               # Factory da aplicação (create_app)
│   ├── config.py                 # Configurações via variáveis de ambiente
│   ├── extensions.py             # Inicialização de extensões (Mongo, Redis, MSAL, SQL)
│   ├── blueprints/               # Módulos da aplicação (um blueprint por domínio)
│   │   ├── main/                 # Rota raiz / health check
│   │   ├── auth/                 # Autenticação Microsoft 365
│   │   ├── m365/                 # Microsoft Graph API (Teams, grupos)
│   │   ├── psoffice/             # Integração com ERP PSOffice
│   │   ├── rdstation/            # Integração com RD Station CRM
│   │   ├── comercial/            # Gestão de negociações comerciais
│   │   ├── warmup/               # Workflow de warmup de projetos
│   │   ├── users/                # Gestão de usuários (incompleto)
│   │   ├── deskmanager/          # Integração com DeskManager
│   │   ├── suporte/              # Chamados de suporte internos
│   │   ├── reports/              # Módulo de relatórios (vazio)
│   │   └── api/                  # Endpoints da API v1 (com token estático)
│   ├── utils/                    # Utilitários reutilizáveis
│   │   ├── decorators.py         # Decoradores de autenticação e roles
│   │   ├── validators.py         # Validação de tokens JWT e estático
│   │   ├── responses.py          # Padronização de respostas JSON
│   │   ├── serialization.py      # Conversão de ObjectId do MongoDB
│   │   ├── datetime_util.py      # Utilitários de datas e fusos horários
│   │   ├── file_utils.py         # Carregamento de arquivos (SQL)
│   │   ├── connection_tests.py   # Testes de conexão com bancos
│   │   ├── results.py            # Serialização de resultados
│   │   └── holidays.py           # Feriados via API externa
│   ├── queries/sql_server/       # Queries SQL para o PSOffice
│   ├── data/                     # Dados estáticos (planners, plan_tasks)
│   ├── templates/                # Templates HTML (e-mail de teste)
│   └── static/                   # Arquivos estáticos (favicon)
├── v2.x/                         # Protótipo de arquitetura DDD (ver seção 9)
├── Notebooks/                    # Jupyter notebooks para operações manuais
├── notes/                        # Notas de arquitetura e inicialização
├── Dockerfile                    # Imagem Docker (Python 3.11 + Gunicorn)
├── docker-compose.yml            # Orquestração do container
├── requirements.txt              # Dependências Python
├── run.py                        # Ponto de entrada local
├── vercel.json                   # Configuração alternativa para deploy no Vercel
└── .env                          # Variáveis de ambiente (não versionado)
```

---

## 4. Configuração e Variáveis de Ambiente

Todas as configurações sensíveis são carregadas via `.env`. O caminho hardcoded no código é `/root/sic-conti-v2/sic-backend/.env` (ambiente de produção Linux).

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Flask |
| `JWT_SECRET_KEY` | Chave para assinatura de tokens JWT |
| `FRONTEND_REDIRECT_URL` | URL do frontend após login |
| `MONGO_URI` | String de conexão do MongoDB |
| `DEFAULT_DB` | Nome do banco de dados padrão no Mongo |
| `MSAL_CLIENT_ID` | ID do app registrado no Azure AD |
| `MSAL_CLIENT_SECRET` | Segredo do app no Azure AD |
| `MSAL_AUTHORITY` | Endpoint de autorização Microsoft |
| `MSAL_SCOPE` | Escopos da API Microsoft Graph |
| `MSAL_TENANT_ID` | ID do tenant Microsoft |
| `REDIRECT_URI` | URI de callback do OAuth2 |
| `REDIS_HOST` | Host do Redis |
| `REDIS_PORT` | Porta do Redis (padrão: 6379) |
| `REDIS_PASSWORD` | Senha do Redis |
| `TOKEN_PSOFFICE` | Token de autenticação do PSOffice |
| `TOKEN_RD` | Token de autenticação do RD Station |
| `DESK_PUBLIC_KEY` | Chave pública do DeskManager |
| `DESK_OPERADOR_KEY` | Chave de operador do DeskManager |
| `DB_SERVER_PSOFFICE` | Servidor SQL Server do PSOffice |
| `DB_NAME_PSOFFICE` | Nome do banco SQL Server |
| `DB_USERNAME_PSOFFICE` | Usuário do banco SQL Server |
| `DB_PASSWORD_PSOFFICE` | Senha do banco SQL Server |
| `STATIC_TOKEN` | Token estático para endpoints da API v1 |
| `POWER_AUTOMATE_URL` | URL do webhook do Power Automate |

---

## 5. Autenticação e Autorização

### Fluxo OAuth2 (Microsoft 365)

```
1. Frontend chama GET /auth/login
2. Backend redireciona para o endpoint de autorização da Microsoft (MSAL)
3. Usuário faz login na conta Microsoft da empresa
4. Microsoft redireciona para GET /auth/callback com código de autorização
5. Backend troca o código por access_token + refresh_token
6. Tokens são armazenados no Redis:
   - {user_id}_access_token  → TTL: 1 hora
   - {user_id}_refresh_token → TTL: 30 dias
7. Backend gera um JWT próprio e envia ao frontend
8. Frontend usa esse JWT no header Authorization: Bearer <token>
```

### Validação nas rotas

| Mecanismo | Decorator/Utilitário | Uso |
|---|---|---|
| JWT interno | `validate_tokens()` | Maioria dos endpoints de negócio |
| Token Azure AD | `require_auth()` | Verificação direta de token Microsoft |
| Role-based | `require_role()` | Controle de acesso por papel |
| Token estático | `validate_static_token()` | Endpoints da API v1 (integrações externas) |

### Sessão
- `GET /auth/session` — retorna dados do usuário logado a partir do token JWT

---

## 6. Módulos (Blueprints) — Endpoints

### 6.1 `main` — `/`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/` | Health check da API | Nenhuma |

---

### 6.2 `auth` — `/auth`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/login` | Inicia fluxo OAuth2 com Microsoft | Nenhuma |
| GET | `/callback` | Recebe código e gera JWT | Nenhuma |
| GET | `/logout` | Invalida sessão no Redis | JWT |
| GET | `/session` | Retorna dados da sessão atual | JWT |

---

### 6.3 `m365` — `/m365`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/profile` | Perfil do usuário + foto | JWT |
| GET | `/groups` | Lista grupos do Teams | JWT |
| GET | `/group_channels` | Lista canais de um grupo | JWT |
| GET | `/channel_members` | Lista membros de um canal | JWT |

**Serviço:** `M365Services` — acessa Microsoft Graph API v1.0  
**Classe auxiliar:** `M365AppToken` — obtém token de aplicação (não de usuário)

---

### 6.4 `psoffice` — `/psoffice`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/centrosresultado` | Lista centros de resultado | JWT |
| GET | `/pessoasjuridicas` | Lista pessoas jurídicas | JWT |
| GET | `/projetos` | Lista projetos com filtros | JWT |

**Serviço:** `PsofficeServices`  
**Fontes de dados:**
- API REST do PSOffice (`https://psofficeapp.com.br/conti`)
- SQL Server direto (queries em `app/queries/sql_server/`)

---

### 6.5 `rdstation` — `/rdstation`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/deals` | Exporta todas as negociações | JWT |
| GET | `/deals-proposta-comercial` | Negociações em etapa de proposta | JWT |

**Serviço:** `RdServices`  
**Métodos internos:**
- `obter_empresas()` — organizações do CRM
- `obter_pipelines()` — funis de vendas
- `obter_negociacoes(win, closed_at_period, start_date, end_date)` — com filtros

---

### 6.6 `comercial` — `/comercial`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/ganhos` | Negociações ganhas não presentes no warmup | JWT |
| GET | `/atualizar-negociacoes` | Sincroniza negociações do RD Station no MongoDB | JWT |
| DELETE | `/deletar-negociacao/<id>` | Remove negociação do MongoDB | JWT |
| POST | `/arquivar-negociacao` | Arquiva negociação no warmup_projetos | JWT |
| POST | `/iniciar-warmup` | Cria registro inicial de warmup | JWT |

**Coleção MongoDB:** `negociacoes`

---

### 6.7 `warmup` — `/warmup`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/listar` | Lista todos os projetos em warmup | JWT |
| GET | `/listar/<negocio_id>` | Busca warmup específico por ID | JWT |
| POST | `/processar_dados` | Inicia warmup de um projeto | JWT |
| PUT | `/atualizar/<negocio_id>` | Atualiza dados de um warmup | JWT |

**Coleção MongoDB:** `warmup_projetos`  
**Estrutura do documento warmup:**
```json
{
  "negocio_id": "",
  "etapa": "Warmup Comercial",
  "status": "Aguardando",
  "inicio_warmup": "<datetime>",
  "cliente": { "nome": "", "cliente_id": "" },
  "capa_projeto": { "codigo": "", "nome_vendedor": "", "email_vendedor": "" },
  "formacao_preco": { "valor": "" },
  "cronograma_execucao": {},
  "adicionais_projeto": {},
  "faturamento": {},
  "observacoes_gerais": [],
  "responsaveis": {
    "responsavel_comercial": { "nome": "", "email": "" }
  }
}
```

---

### 6.8 `users` — `/users`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/` | Lista usuários | Nenhuma |

> **Estado:** Incompleto. O arquivo `models.py` está vazio e não há lógica de negócio implementada.

---

### 6.9 `deskmanager` — `/deskmanager`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/clientes` | Lista clientes do DeskManager | JWT |
| GET | `/contratos` | Lista contratos + dados PSOffice | JWT |
| GET | `/chamados-suporte` | Lista chamados de suporte | JWT |

**Serviço:** `DeskManagerServices`  
**Funcionalidade adicional:** O endpoint `/contratos` cruza dados do DeskManager com projetos AMS do PSOffice, enriquecendo os contratos com `projId` e `crId`.

---

### 6.10 `suporte` — `/suporte`
| Método | Rota | Descrição | Auth |
|---|---|---|---|
| POST | `/criar` | Cria chamado interno | Nenhuma |
| GET | `/listar` | Lista todos os chamados | Nenhuma |
| GET | `/listar/<id>` | Busca chamado por ID | Nenhuma |
| PUT | `/editar/<id>` | Atualiza chamado | Nenhuma |
| DELETE | `/deletar/<id>` | Remove chamado | Nenhuma |

**Coleção MongoDB:** `chamados`

> **Atenção:** Este blueprint não possui validação de token em nenhum endpoint.

---

### 6.11 `reports` — `/reports`
> **Estado:** Módulo criado mas completamente vazio. Nenhum endpoint implementado.

---

### 6.12 `api` — `/api/v1`
Endpoints com autenticação via **token estático** (para consumo por sistemas externos sem login interativo).

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/` | Status da API |
| GET | `/api/v1/psoffice/...` | Endpoints PSOffice via token estático |
| GET | `/api/v1/rdstation/...` | Endpoints RD Station via token estático |

---

## 7. Queries SQL Server (PSOffice)

Armazenadas em `app/queries/sql_server/` e carregadas dinamicamente pelo `file_utils.py`:

| Arquivo | Descrição |
|---|---|
| `get_projetos_psoffice.sql` | Lista de projetos com detalhes |
| `get_usuarios_psoffice.sql` | Lista de usuários |
| `get_apontamentos_psoffice.sql` | Apontamentos com projeto e usuário |
| `apontamentos_aprovados.sql` | Apontamentos com STATUS = '2' |
| `apontamentos_pendentes.sql` | Apontamentos com STATUS IN ('0','1','4') |
| `ausencias_aprovadas.sql` | Ausências aprovadas com intervalo de datas |
| `buscar_id_usuario.sql` | Busca ID de usuário por CPF |
| `projetos.sql` | Lista de projetos com detalhes completos |
| `reembolsos_aprovados.sql` | Reembolsos aprovados |
| `reembolsos_pendentes.sql` | Reembolsos pendentes |

---

## 8. Bancos de Dados

### MongoDB
**Coleções identificadas:**

| Coleção | Módulo responsável | Descrição |
|---|---|---|
| `negociacoes` | comercial | Negociações sincronizadas do RD Station |
| `warmup_projetos` | warmup / comercial | Projetos em processo de warmup |
| `chamados` | suporte | Chamados de suporte internos |

### Redis
Usado exclusivamente para armazenar tokens de sessão OAuth2:
- Chave `{user_id}_access_token` — TTL: 3600s
- Chave `{user_id}_refresh_token` — TTL: 2592000s (30 dias)

### SQL Server (PSOffice)
Acesso **somente leitura** ao banco de dados do ERP PSOffice. Gerenciado pela classe `DatabaseManager` em `extensions.py`. Usa `pymssql` com connection pooling.

---

## 9. Dados Estáticos

### `app/data/planners.json`
Lista com **80+ grupos do Microsoft Teams** da Conticonsultoria, cada um com:
- `displayName`, `id`, `email`, `visibility`

### `app/data/plan_tasks.json`
Lista de tarefas do Microsoft Planner com o backlog de desenvolvimento do sistema, incluindo:
- Implementar `MicrosoftServices`
- Implementar `FinteraServices`
- Implementar `DeskManagerServices`
- Migrar funcionalidades básicas da v1 para v2
- Desenvolver formação de preço, propostas comerciais, orçamentos
- Configurar documentação no Notion *(concluído)*

---

## 10. Deploy e Infraestrutura

### Docker (produção)
```yaml
# docker-compose.yml
services:
  flask_app_sic:
    container_name: backend-5000
    build: .           # Dockerfile na raiz
    image: sic-backend
    ports:
      - "5000:5000"
    volumes:
      - .:/app         # Volume para desenvolvimento (não ideal em produção)
    env_file:
      - .env
    restart: always
```

```dockerfile
# Dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt && pip install gunicorn
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
```

### Vercel (alternativa)
O arquivo `vercel.json` configura um deploy serverless via `@vercel/python`, roteando tudo para `run.py`. Esta opção **não é compatível com conexões persistentes** como Redis e SQL Server — seria necessária refatoração para uso nesse ambiente.

### CORS configurado para
- `http://localhost:3000` (desenvolvimento)
- `https://sic.conticonsultoria.cloud` (produção)

---

## 11. Notebooks Jupyter

Localizados em `Notebooks/`, são scripts operacionais que rodam fora da API:

| Notebook | Finalidade |
|---|---|
| `atualizar_negociacoes_rd.ipynb` | Sincronização manual de negociações do RD Station |
| `Inserir_warmup_manual.ipynb` | Inserção manual de projetos no warmup |
| `pipelines.ipynb` | Processamento de dados de pipelines |
| `pipeline_folha.ipynb` | Pipeline de folha de pagamento |
| `teste.ipynb` | Testes e experimentos gerais |

> Esses notebooks indicam que parte das operações de dados ainda é feita manualmente, sem automação via API.

---

## 12. Subdiretório `v2.x/` — Protótipo DDD

Existe dentro do repositório um subdiretório `v2.x/` que representa uma **tentativa paralela de reescrita** usando arquitetura **DDD (Domain-Driven Design) / Hexagonal**.

### Estrutura proposta
```
v2.x/app/
├── aplicacao/         # Camada de Aplicação
│   ├── dto/           # Data Transfer Objects por domínio
│   ├── interfaces/    # Interfaces de serviços
│   ├── servicos/      # Orquestradores por domínio
│   └── testes/        # Testes da camada de aplicação
├── dominios/          # Camada de Domínio
│   ├── admin/
│   ├── comercial/
│   ├── financeiro/
│   ├── pessoal/
│   ├── servicos/
│   └── suprimentos/
└── infraestrutura/    # Camada de Infraestrutura (repositórios)
```

### Domínios mapeados
- **admin** — administração e usuários
- **comercial** — negociações e propostas
- **financeiro** — financeiro e faturamento
- **pessoal** — RH e colaboradores
- **servicos** — prestação de serviços
- **suprimentos** — compras e suprimentos

### Estado atual
Os arquivos de entidades e casos de uso estão **estruturados mas vazios** (arquivos com 1 linha). O `v2.x/` é um esqueleto arquitetural sem implementação real, indicando que este refactor foi **planejado mas não executado**.

---

## 13. Estado de Implementação por Módulo

| Módulo | Estado | Observações |
|---|---|---|
| **auth** | Funcional | Fluxo OAuth2 completo com Microsoft 365 |
| **m365** | Funcional | Grupos, canais, membros do Teams |
| **psoffice** | Parcial | API REST + SQL Server; faltam alguns endpoints |
| **rdstation** | Funcional | Export de deals; filtros implementados |
| **comercial** | Funcional | Sincronização com Mongo, warmup comercial |
| **warmup** | Funcional | CRUD completo de projetos em warmup |
| **deskmanager** | Funcional | Integração com cruzamento de dados PSOffice |
| **suporte** | Funcional | CRUD de chamados (sem autenticação) |
| **users** | Incompleto | Apenas rota GET vazia; sem modelo ou serviço |
| **reports** | Vazio | Módulo criado mas sem implementação |
| **api/v1** | Parcial | Endpoints PSOffice e RD Station com token estático |

---

## 14. Problemas e Dívidas Técnicas Identificadas

1. **Caminho hardcoded do `.env`** — `app/__init__.py` e `config.py` carregam o `.env` de `/root/sic-conti-v2/sic-backend/.env`, quebrando em qualquer outro ambiente sem ajuste manual.

2. **Módulo `suporte` sem autenticação** — todos os 5 endpoints estão expostos sem qualquer validação de token.

3. **Módulo `reports` completamente vazio** — blueprint registrado mas sem nenhuma funcionalidade.

4. **Módulo `users` incompleto** — `models.py`, `services.py` e validadores estão vazios ou ausentes.

5. **Volume de desenvolvimento em docker-compose** — `volumes: - .:/app` sobrescreve a imagem Docker em runtime, o que pode causar inconsistências em produção se o código local diferir da imagem.

6. **Duplicação de rotas** — existem `routes.py` e `routes_main.py` dentro de `app/blueprints/api/` sem distinção clara.

7. **`iniciar_warmup` duplicado** — existe em `comercial/services.py` e em `warmup/services.py` com implementações ligeiramente diferentes.

8. **Notebooks operacionais** — operações que deveriam ser endpoints da API ainda são feitas via Jupyter Notebook manualmente.

9. **Vercel incompatível** — `vercel.json` presente no repositório, mas Redis e SQL Server não funcionam em ambiente serverless sem adaptação.

10. **Pydantic v1** — a versão 1.x do Pydantic está em fim de vida e é incompatível com as versões mais recentes do ecossistema Python.

---

## 15. Fluxo de Negócio Principal (Warmup Comercial)

O fluxo central do sistema, conectando CRM, MongoDB e Teams:

```
RD Station CRM
     │
     │  Negociação marcada como "Ganha"
     ▼
GET /comercial/ganhos
     │  Filtra wins dos últimos N dias que ainda não estão no warmup
     ▼
POST /warmup/processar_dados  ou  POST /comercial/iniciar-warmup
     │  Cria documento em warmup_projetos com etapa "Warmup Comercial"
     ▼
PUT /warmup/atualizar/<negocio_id>
     │  Atualiza etapas, responsáveis, cronograma, formação de preço
     ▼
MongoDB (coleção warmup_projetos)
     │
     └── Frontend consome via GET /warmup/listar
```

---

## 16. Pontos para Comparação com a Versão Anterior (v1)

Os seguintes aspectos devem ser verificados ao comparar com o sic-backend_v1:

- **Módulos existentes em v1 que estão ausentes ou incompletos em v2:** `users`, `reports`, `financeiro`, `pessoal`, `suprimentos`
- **Arquitetura:** v2 adota Flask Blueprints (modular); verificar se v1 era monolítico
- **Autenticação:** v2 usa Microsoft 365 OAuth2 + JWT próprio; verificar mecanismo da v1
- **Banco de dados:** v2 usa MongoDB + Redis + SQL Server; verificar se v1 usava os mesmos
- **Integrações:** DeskManager e RD Station foram adicionadas ou já existiam em v1?
- **Warmup Comercial:** verificar se este fluxo existia em v1 ou é funcionalidade nova
- **Notebooks:** verificar se operações manuais via Jupyter eram necessárias em v1
- **Deploy:** v2 usa Docker com Gunicorn; verificar infraestrutura de v1
