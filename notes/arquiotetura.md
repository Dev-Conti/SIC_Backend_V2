/backend
├── app/                             # Aplicação Flask principal
│   ├── __init__.py                  # Inicialização da aplicação Flask
│   ├── config.py                    # Configurações gerais da aplicação
│   ├── extensions.py                # Inicialização de extensões (pymongo, authlib, etc.)
│   ├── blueprints/                  # Módulos separados por funcionalidades
│   │   ├── auth/                    # Módulo de autenticação com Microsoft 365
│   │   │   ├── __init__.py          # Registro do blueprint de autenticação
│   │   │   ├── routes.py            # Endpoints relacionados à autenticação
│   │   │   ├── services.py          # Lógica de autenticação e integração com OAuth 2.0
│   │   │   └── helpers.py           # Funções auxiliares para autenticação
│   │   ├── users/                   # Módulo de gestão de usuários
│   │   │   ├── __init__.py          # Registro do blueprint de usuários
│   │   │   ├── routes.py            # Endpoints relacionados a usuários
│   │   │   ├── models.py            # Modelos de usuário (MongoDB)
│   │   │   ├── services.py          # Lógica de negócios relacionada a usuários
│   │   │   └── validators.py        # Validações específicas para usuários
│   │   └── reports/                 # Módulo de relatórios
│   │       ├── __init__.py          # Registro do blueprint de relatórios
│   │       ├── routes.py            # Endpoints relacionados a relatórios
│   │       ├── services.py          # Lógica de geração de relatórios
│   │       └── helpers.py           # Funções auxiliares para relatórios
│   └── utils/                       # Funções utilitárias reutilizáveis
│       ├── decorators.py            # Decoradores reutilizáveis (ex: autenticação)
│       ├── validators.py            # Funções de validação genéricas
│       └── helpers.py               # Funções auxiliares gerais
├── tests/                           # Testes unitários e de integração
│   ├── conftest.py                  # Configuração de fixtures do Pytest
│   ├── test_auth.py                 # Testes relacionados à autenticação
│   ├── test_users.py                # Testes relacionados a usuários
│   └── test_reports.py              # Testes relacionados a relatórios
├── requirements.txt                 # Dependências do projeto
├── docker-compose.yml               # Arquivo para orquestração dos contêineres
├── run.py                           # Arquivo para rodar a aplicação localmente
├── vercel.json                      # Configuração específica para o Vercel
└── api/                             # Diretório para serverless functions no Vercel
    └── index.py                     # Ponto de entrada para o Vercel


/backend/app/blueprints/colaboradores/
├── __init__.py          # Registro do blueprint de colaboradores
├── routes.py            # Endpoints relacionados a colaboradores
├── models.py            # Modelos de colaborador (MongoDB)
├── services.py          # Lógica de negócios relacionada a colaboradores
└── validators.py        # Validações específicas para colaboradores