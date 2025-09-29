# ETL Processor - Transformador de CSV para SQL

Uma aplicação completa para transformar arquivos CSV em scripts SQL, com interface web intuitiva e API backend robusta.

## 🚀 Arquitetura

O projeto foi reestruturado para uma arquitetura moderna de microserviços:

- **Frontend**: Next.js 14 com TypeScript e Tailwind CSS
- **Backend**: Flask API em Python para processamento de dados
- **Containerização**: Docker e Docker Compose para fácil deployment

## ✨ Funcionalidades

- 📁 Upload de arquivos CSV via drag & drop
- ⚙️ Configuração flexível de delimitadores (vírgula, ponto e vírgula, tab, pipe)
- 🎯 Seleção e reordenação de campos
- 🎨 Formatação de dados (texto, número, moeda, data)
- 👀 Pré-visualização dos dados processados
- 🗄️ Geração de SQL para múltiplos SGBDs (MySQL, PostgreSQL, SQLite, SQL Server, ANSI)
- 📥 Download de arquivos processados (CSV, TSV, TXT, SQL)

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

3. **Executar o servidor Flask**
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
  "databaseType": "mysql",
  "includeCreateTable": true
}
```

## 🗂️ Estrutura do Projeto

```
etl-processor/
├── app/                    # Páginas Next.js
├── components/             # Componentes React
│   ├── csv/               # Componentes específicos para CSV
│   └── ui/                # Componentes de UI reutilizáveis
├── lib/                   # Utilitários e serviços
├── backend/               # API Flask
│   ├── app.py            # Aplicação principal
│   ├── requirements.txt  # Dependências Python
│   └── Dockerfile        # Container do backend
├── docker-compose.yml     # Orquestração dos serviços
├── Dockerfile.frontend    # Container do frontend
└── README.md             # Este arquivo
```

## 🎯 Como Usar

1. **Upload do CSV**: Arraste e solte ou selecione um arquivo CSV
2. **Configurar Delimitador**: Escolha o delimitador usado no arquivo
3. **Selecionar Campos**: Escolha quais campos incluir e defina a ordem
4. **Formatar Dados**: Configure o formato de cada campo (texto, número, moeda, data)
5. **Pré-visualizar**: Veja como ficará o resultado final
6. **Exportar**: Baixe o arquivo processado (CSV ou SQL)

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

### Bancos de Dados Suportados
- ANSI SQL
- MySQL
- PostgreSQL
- SQLite
- SQL Server

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

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🚀 Próximas Funcionalidades

- [ ] Suporte a mais formatos de arquivo (Excel, JSON)
- [ ] Validação avançada de dados
- [ ] Templates de transformação salvos
- [ ] API de batch processing
- [ ] Interface de administração
- [ ] Logs de auditoria
