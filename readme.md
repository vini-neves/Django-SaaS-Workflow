# 🚀 StudioFlow: Plataforma SaaS Multi-Tenant de Gestão de Conteúdo

## 💡 Visão Geral e Propósito

O StudioFlow é uma prova de conceito de uma plataforma **SaaS (Software as a Service) B2B** desenvolvida com **Django** para resolver o caos no fluxo de trabalho de agências de marketing.

O projeto demonstra a capacidade de construir aplicações complexas que exigem **isolamento rigoroso de dados**, usabilidade moderna e integração de serviços críticos.

### 🎯 O Problema Resolvido: Isolamento e Fluxo

O projeto soluciona o principal desafio de um software multi-agência: garantir que a Agência A (no domínio A) não possa acessar ou ver os dados da Agência B (no domínio B), enquanto mantém um sistema de gestão de produção contínua e transparente.

---

## ✨ Principais Funcionalidades Implementadas

O projeto demonstra experiência nas seguintes áreas, que são cruciais para um portfólio profissional:

### 1. Arquitetura e Segurança
* **Multi-Tenancy (Django-Tenants):** Isolamento total de dados por schema no PostgreSQL, garantindo que cada agência (`tenant1.localhost`) acesse apenas seus próprios dados.
* **Segurança de Login:** Implementação de uma **TenantLoginView** customizada que impede o login cruzado (Usuário da Agência A tentando logar na URL da Agência B).
* **White-Labeling:** Customização dinâmica do frontend (cores principais, cores secundárias, logo) puxadas do banco de dados e injetadas via variáveis CSS.
* **Proteção de Credenciais:** Uso da biblioteca `python-decouple` para manter todas as chaves secretas (Google, Django Secret Key, DB Passwords) fora do repositório Git, via arquivo `.env`.

### 2. Gestão de Workflow (Kanban)
* **Kanban Duplo:** Separação lógica entre as tarefas:
    * **Kanban Geral:** Tarefas de rotina (`To Do`, `In Progress`, `Done`).
    * **Kanban Operacional:** Fluxo de produção e aprovação (Briefing, Copy, Design, Aprovação Cliente, Agendamento).
* **Interatividade:** Funcionalidade de **Drag & Drop** (arrastar e soltar) para mudança de status e ordem das tarefas, persistida via API.
* **Detalhes Dinâmicos:** Modal de detalhes da tarefa com informações completas e histórico de modificação.

### 3. Publicação e Aprovação (Social Media)
* **Estrutura de Agendamento:** Modelos de dados prontos para múltiplos destinos granulares (`Facebook Story`, `Instagram Reel`, `X Post`, `YouTube Short`, etc.).
* **Fluxo de Aprovação Externa (Pronto):** Estrutura de backend completa para gerar um **link público exclusivo (token)** que pode ser enviado ao cliente para revisão de conteúdo e design.
* **Integração API (Setup):** Configuração de OAuth 2.0 (Google Calendar) e preparação da estrutura para a API Meta/Graph.

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia | Função no Projeto |
| :--- | :--- | :--- |
| **Backend Core** | Python 3, Django | Framework principal. |
| **Banco de Dados** | PostgreSQL | Suporte a Schemas Isolados (`django-tenants`). |
| **Multi-Tenancy** | Django-Tenants | Isolamento rigoroso de dados por URL. |
| **UX/Interatividade** | Feather Icons, SweetAlert2, jQuery, DataTables.net | Ícones, alertas modernos e tabelas dinâmicas. |
| **Segurança** | python-decouple | Gerenciamento seguro de variáveis de ambiente. |

---

## ⚙️ Configuração do Ambiente Local

### Pré-requisitos

1.  **PostgreSQL:** Servidor deve estar rodando.
2.  **Python 3.x**
3.  **Arquivo `hosts`:** Adicione as linhas `127.0.0.1 tenant1.localhost` e `127.0.0.1 tenant2.localhost`.

### Passos de Instalação e Inicialização

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/vini-neves/Django-SaaS-Workflow.git](https://github.com/vini-neves/Django-SaaS-Workflow.git)
    cd Django-SaaS-Workflow
    ```

2.  **Instalação de Dependências:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # Instale todas as dependências (Django, django-tenants, psycopg2-binary, etc.)
    # Se você criou um requirements.txt, use 'pip install -r requirements.txt'
    ```

3.  **Configuração de Chaves (Crie o Arquivo Secreto):**
    * Crie o arquivo **`.env`** na raiz do projeto (ao lado do `manage.py`).
    * Preencha-o com suas credenciais:

    ```
    # .env
    SECRET_KEY='seu_token_aqui'
    DATABASE_NAME=meu_saas_db
    DATABASE_USER=django_user
    DATABASE_PASSWORD='sua_senha_do_postgres'
    DB_HOST=localhost
    # ... Google Credentials (Client ID, Client Secret)
    ```

4.  **Inicialize o Banco de Dados:**
    * Este comando cria a estrutura de tabelas no schema `public`.
    ```bash
    python manage.py migrate_schemas --shared
    ```

5.  **Crie Usuários e Tenants de Teste:**
    * Crie um Superusuário (para o admin principal): `python manage.py createsuperuser`
    * Acesse `http://localhost:8000/admin/` e crie a primeira **Agency** (schema: `tenant1`) e o **Domain** (`tenant1.localhost`).

6.  **Execute o Projeto:**
    ```bash
    python manage.py runserver
    ```
    Acesse a aplicação em `http://tenant1.localhost:8000/`.