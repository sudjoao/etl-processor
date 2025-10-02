# ETL Processor - Transformador de CSV para SQL

Uma aplicação completa para transformar arquivos CSV em scripts SQL, com interface web intuitiva e API backend robusta.

## 🚀 Arquitetura

O projeto foi reestruturado para uma arquitetura moderna de microserviços:

- **Frontend**: Next.js 14 com TypeScript e Tailwind CSS
- **Backend**: Flask API em Python para processamento de dados
- **Containerização**: Docker e Docker Compose para fácil deployment

## ✨ Funcionalidades

### Processamento de Dados
- 📁 Upload de arquivos CSV via drag & drop
- ⚙️ Configuração flexível de delimitadores (vírgula, ponto e vírgula, tab, pipe)
- 🎯 Seleção e reordenação de campos
- 🎨 Formatação de dados (texto, número, moeda, data)
- 👀 Pré-visualização dos dados processados
- 🗄️ Geração de SQL para múltiplos SGBDs (MySQL, PostgreSQL, SQLite, SQL Server, ANSI)
- 📥 Download de arquivos processados (CSV, TSV, TXT, SQL)

### Modelagem de Data Warehouse ⭐ NOVO
- 🏗️ Análise automática de esquemas SQL
- ⭐ Geração de modelos dimensionais (Star Schema)
- 📊 Identificação automática de tabelas fato e dimensão
- 🔄 Suporte a Slowly Changing Dimensions (SCD)
- 🎯 Recomendações de otimização
- 📋 Geração de DDL para múltiplos SGBDs
- 🔍 Visualização interativa do modelo dimensional
- 🛠️ **Suporte aprimorado para dados de CSV**: Funciona com tabelas únicas geradas a partir de CSV
- 🤖 **Classificação IA**: Integração com OpenRouter para classificação inteligente de dimensões

## 🛠️ Tecnologias Utilizadas

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- Radix UI Components
- React Hook Form
- Lucide Icons

### Backend
- Flask 3.0
- Flask-CORS
- Python 3.11
- Gunicorn
- SQLParse (análise de SQL)
- Pandas & NumPy (processamento de dados)
- Engine de Modelagem Dimensional personalizado

### DevOps
- Docker
- Docker Compose
- Multi-stage builds

## 🚀 Execução com Docker Compose (Recomendado)

### Pré-requisitos
- Docker
- Docker Compose

### Passos

1. **Clone o repositório**
```bash
git clone <repository-url>
cd etl-processor
```

2. **Execute com Docker Compose**
```bash
docker-compose up --build
```

3. **Acesse a aplicação**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

### Comandos úteis

```bash
# Executar em background
docker-compose up -d --build

# Parar os serviços
docker-compose down

# Ver logs
docker-compose logs -f

# Rebuild apenas um serviço
docker-compose up --build frontend
docker-compose up --build backend
```

## 🔧 Execução em Desenvolvimento

### Frontend

1. **Instalar dependências**
```bash
pnpm install
```

2. **Configurar variáveis de ambiente**
```bash
cp .env.example .env
# Editar .env conforme necessário
```

3. **Executar em modo desenvolvimento**
```bash
pnpm dev
```

### Backend

1. **Navegar para o diretório backend**
```bash
cd backend
```

2. **Instalar dependências Python**
```bash
pip install -r requirements.txt
```

3. **Configurar classificação IA (opcional)**
```bash
# Editar .env e adicionar sua chave do OpenRouter
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
AI_MODEL=anthropic/claude-3.5-sonnet
AI_CLASSIFICATION_ENABLED=true
```

4. **Executar o servidor Flask**
```bash
python app.py
```

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```

### Transformar CSV para SQL
```http
POST /api/transform
Content-Type: application/json

{
  "csvContent": "nome,idade,salario\nJoão,30,5000.50",
  "fields": [
    {"name": "nome", "selected": true, "order": 0, "format": "text"},
    {"name": "idade", "selected": true, "order": 1, "format": "number"},
    {"name": "salario", "selected": true, "order": 2, "format": "currency"}
  ],
  "tableName": "funcionarios",
  "delimiter": ",",
  "databaseType": "postgresql",
  "includeCreateTable": true
}
```

## 🗂️ Estrutura do Projeto

```
etl-processor/
├── app/                    # Páginas Next.js
├── components/             # Componentes React
│   ├── csv/               # Componentes específicos para CSV
│   ├── dw/                # Componentes de Data Warehouse ⭐
│   └── ui/                # Componentes de UI reutilizáveis
├── lib/                   # Utilitários e serviços
├── backend/               # API Flask
│   ├── app.py            # Aplicação principal
│   ├── sql_analyzer.py   # Analisador de SQL ⭐
│   ├── dimensional_modeling.py  # Engine de modelagem ⭐
│   ├── star_schema_generator.py # Gerador de Star Schema ⭐
│   ├── requirements.txt  # Dependências Python
│   └── Dockerfile        # Container do backend
├── docker-compose.yml     # Orquestração dos serviços
├── Dockerfile.frontend    # Container do frontend
└── README.md             # Este arquivo
```

## 🏗️ Modelagem de Data Warehouse

### Funcionalidades Avançadas

O ETL Processor agora inclui um engine completo de modelagem dimensional que automaticamente:

- **Analisa esquemas SQL** e identifica padrões dimensionais
- **Gera modelos Star Schema** com tabelas fato e dimensão
- **Cria chaves substitutas** (surrogate keys) automaticamente
- **Implementa SCD** (Slowly Changing Dimensions) Tipo 1 e 2
- **Otimiza para diferentes SGBDs** (MySQL, PostgreSQL, SQL Server, etc.)

### Como Usar a Modelagem DW

1. **Gere o SQL** normalmente através do processamento CSV
2. **Clique em "Modelagem DW"** após a geração do SQL
3. **Visualize o modelo** dimensional proposto
4. **Baixe os scripts DDL** otimizados para seu SGBD
5. **Implemente no seu Data Warehouse**

### Endpoints da API DW

```bash
# Analisar SQL
POST /api/analyze-sql
{
  "sql": "CREATE TABLE vendas (...)"
}

# Gerar modelo dimensional
POST /api/generate-dw-model
{
  "sql": "CREATE TABLE vendas (...)",
  "dialect": "postgresql"
}

# Obter recomendações
GET /api/dw-recommendations

# Metadados do sistema
GET /api/dw-metadata
```

## 🎯 Como Usar

1. **Upload do CSV**: Arraste e solte ou selecione um arquivo CSV
2. **Configurar Delimitador**: Escolha o delimitador usado no arquivo
3. **Selecionar Campos**: Escolha quais campos incluir e defina a ordem
4. **Formatar Dados**: Configure o formato de cada campo (texto, número, moeda, data)
5. **Pré-visualizar**: Veja como ficará o resultado final
6. **Exportar**: Baixe o arquivo processado (CSV ou SQL)
7. **Modelagem DW** ⭐: Gere automaticamente um modelo dimensional

## 🔧 Configurações Suportadas

### Delimitadores
- Vírgula (`,`)
- Ponto e vírgula (`;`)
- Tabulação (`\t`)
- Pipe (`|`)

### Formatos de Campo
- **Texto**: Mantém como string
- **Número**: Formata como número decimal
- **Moeda**: Formata como valor monetário (R$)
- **Data**: Converte YYYY-MM-DD para DD/MM/YYYY

### Banco de Dados Suportado
- **PostgreSQL** (único banco suportado para garantir compatibilidade total)

### Modelos de IA Suportados (OpenRouter)
- `anthropic/claude-3.5-sonnet` (recomendado)
- `anthropic/claude-3-haiku`
- `openai/gpt-4o`
- `openai/gpt-3.5-turbo`
- `meta-llama/llama-3.1-8b-instruct`

## 🤖 Classificação IA de Dimensões

O sistema inclui classificação inteligente de dimensões usando IA via OpenRouter:

### Configuração
1. Obtenha uma chave API em [OpenRouter](https://openrouter.ai/)
2. Configure no arquivo `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
AI_MODEL=anthropic/claude-3.5-sonnet
AI_CLASSIFICATION_ENABLED=true
```

### Funcionalidades
- **Classificação Automática**: IA analisa colunas e identifica padrões dimensionais
- **Fallback Inteligente**: Se a IA falhar, usa classificação baseada em regras
- **Múltiplos Modelos**: Suporte a diferentes modelos de IA
- **Confiança**: Cada classificação inclui nível de confiança
- **Raciocínio**: IA explica suas decisões de classificação

### Endpoint de Teste
```http
POST /api/test-ai-classification
Content-Type: application/json

{
  "sql": "CREATE TABLE dados (nome VARCHAR(255), cpf VARCHAR(255));"
}
```

## 🐛 Troubleshooting

### Problemas Comuns

1. **Porta 5001 em uso**
   - No macOS, desabilite o AirPlay Receiver em Configurações do Sistema
   - Ou altere a porta no arquivo `backend/app.py` e `docker-compose.yml`

2. **Erro de CORS**
   - Verifique se o backend está rodando na porta correta
   - Confirme a variável `NEXT_PUBLIC_API_URL` no `.env`

3. **Erro de parsing CSV**
   - Verifique se o delimitador está correto
   - Certifique-se de que o arquivo está em UTF-8

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 🔧 Troubleshooting

### Problema: "Could not generate a valid star schema from the provided SQL"

**Solução**: Este erro foi corrigido na versão atual. O sistema agora:
- ✅ Suporta tabelas únicas geradas a partir de CSV
- ✅ Identifica automaticamente padrões dimensionais em dados planos
- ✅ Cria modelos Star Schema mesmo com dados de controle de acesso
- ✅ Ignora comentários SQL durante o parsing

### Outros Problemas Comuns

- **Porta 5001 em uso**: Execute `lsof -ti:5001 | xargs kill -9` para liberar a porta
- **Docker não inicia**: Verifique se o Docker Desktop está rodando
- **Erro de CORS**: Verifique se o backend está rodando na porta correta

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🚀 Próximas Funcionalidades

- [ ] Suporte a mais formatos de arquivo (Excel, JSON)
- [ ] Validação avançada de dados
- [ ] Templates de transformação salvos
- [ ] API de batch processing
- [ ] Interface de administração
- [ ] Logs de auditoria
