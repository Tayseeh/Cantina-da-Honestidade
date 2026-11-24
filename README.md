# Confia+ — Cantina da Honestidade

Sistema web para apoiar a operação da Cantina da Honestidade, com catálogo de produtos, carteira virtual, compras com PIN, recargas em dinheiro, gestão de clientes e produtos e relatórios.

> **Estado do projeto:** aplicação acadêmica em desenvolvimento/homologação local. O código desta versão usa MySQL 8 e servidor de desenvolvimento Flask quando iniciado diretamente por `python apli.py`. Não considerar esse servidor pronto para produção institucional.

## Conteúdo

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Instalação no Windows](#instalação-no-windows)
- [Configuração do banco](#configuração-do-banco)
- [Inicialização e acesso](#inicialização-e-acesso)
- [Dados de demonstração](#dados-de-demonstração)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Testes](#testes)
- [Backup e restauração](#backup-e-restauração)
- [Solução de problemas](#solução-de-problemas)
- [Cuidados antes de publicar](#cuidados-antes-de-publicar)

## Funcionalidades

### Cliente
- Consultar produtos ativos por categoria e pesquisar no catálogo.
- Adicionar produtos ao carrinho, inclusive pelo fluxo de QR Code.
- Confirmar compras com PIN de pagamento.
- Consultar saldo da carteira, histórico de compras e notificações.
- Atualizar dados de perfil e foto, conforme os campos disponíveis na tela.

### Operador
- Consultar, cadastrar e gerenciar clientes.
- Pesquisar clientes e filtrar por situação e saldo negativo.
- Consultar produtos, cadastrar e editar produtos, preços, categorias, fotos e estoque.
- Registrar recargas em dinheiro recebidas fisicamente.
- Consultar informações operacionais disponíveis na interface.

### Administrador
- Gerenciar contas de administradores e operadores.
- Consultar relatório e logs de auditoria.
- Visualizar indicadores e informações gerenciais disponibilizados no painel.

### Regras importantes
- A compra é confirmada somente após validação do PIN.
- O backend verifica novamente estoque e disponibilidade no momento da compra.
- O saldo da carteira pode ficar negativo.
- Quando uma compra faz o saldo passar de zero ou positivo para negativo, o cliente precisa confirmar ciência. Se o saldo continuar negativo, compras seguintes não repetem essa confirmação. Se uma recarga levar o saldo de volta a zero ou positivo e uma compra posterior voltar a deixá-lo negativo, uma nova confirmação será solicitada.
- As recargas registradas pelo sistema são em dinheiro, feitas por um operador após receber o valor fisicamente.
- O QR Code do produto é um atalho para localizar/adicionar o item ao carrinho; não conclui uma compra por si só.
- O seed contém dados fictícios para demonstração. Os valores de custo e venda do catálogo de demonstração não devem ser tratados como tabela comercial oficial.

## Tecnologias

- Python 3.10 ou superior (recomendado: versão compatível com as dependências instaladas).
- Flask 3.x e Jinja2.
- MySQL Server 8.
- `mysql-connector-python`.
- HTML, CSS, JavaScript e Bootstrap utilizado pelos templates.
- Pillow para processamento de imagens.
- `python-dotenv` para carregar variáveis do arquivo `.env`.
- `tzdata` para suporte a fuso horário.

As dependências Python estão listadas em `requirements.txt`.

## Requisitos

1. Python instalado e disponível no PATH.
2. MySQL Server 8 em execução.
3. Um banco MySQL criado para a aplicação.
4. Um usuário MySQL com permissões para criar/alterar tabelas e executar as operações da aplicação.
5. Terminal PowerShell ou Prompt de Comando no Windows.

## Instalação no Windows

Abra o PowerShell na pasta do projeto:

```powershell
cd C:\caminho\para\Cantina-da-Honestidade
```

Crie e ative o ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, use temporariamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuração do banco

Crie o banco no MySQL:

```sql
CREATE DATABASE cantina_honestidade
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Na raiz do projeto, copie `.env.example` para `.env`:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` com os dados do seu MySQL:

```dotenv
APP_ENV=development
CANTINA_DB_HOST=localhost
CANTINA_DB_PORT=3306
CANTINA_DB_NAME=cantina_honestidade
CANTINA_DB_USER=root
CANTINA_DB_PASSWORD=sua_senha_mysql
```

Ajuste usuário e senha para o ambiente local. O `.env` contém credenciais e não deve ser enviado ao Git nem compartilhado.

Para desenvolvimento, `CANTINA_SECRET_KEY` pode ficar ausente: o código usa uma chave fixa de desenvolvimento e exibe um aviso. **Não use essa chave em produção.** Para um ambiente de produção, configure `APP_ENV=production` e uma `CANTINA_SECRET_KEY` privada, aleatória e com pelo menos 32 caracteres.

O esquema é inicializado pela aplicação na primeira requisição (e também no fluxo de inicialização de `apli.py`). A função `initialize_database()` cria tabelas ausentes e executa verificações pontuais de compatibilidade; ela não substitui uma estratégia completa de migrações versionadas.

## Inicialização e acesso

Com o ambiente virtual ativo e o MySQL iniciado:

```powershell
python apli.py
```

Acesse no navegador:

- Na própria máquina: `http://127.0.0.1:5000`
- Em outro dispositivo da mesma rede: use o endereço IP local do computador que está executando a aplicação, por exemplo `http://192.168.x.x:5000`, se o firewall e a rede permitirem.

O comando acima inicia o servidor de desenvolvimento Flask com `debug=True`, porta `5000` e escuta em `0.0.0.0`. É adequado apenas para desenvolvimento/homologação controlada. Não exponha esse servidor diretamente à internet.

Para encerrar, volte ao terminal e pressione `Ctrl+C`.

## Dados de demonstração

O seed opcional está em `scripts/seed.py`. Execute a partir da raiz:

```powershell
python .\scripts\seed.py
```

Ele cria/atualiza dados fictícios de demonstração de forma conservadora. Para contas já existentes, o script não substitui senhas e saldos; para clientes de demonstração, completa apenas campos cadastrais vazios. Produtos são identificados pelo nome e o catálogo definido no script é ativado/atualizado conforme a implementação.

### Contas de demonstração

| Perfil | Usuário | Senha inicial |
|---|---|---|
| Administrador | `admin` | `Admin@12345` |
| Operador | `operador1` | `Operador@12345` |
| Operador | `operador2` | `Operador@12345` |
| Cliente | `cliente1` | `Cliente@12345` |
| Cliente | `cliente2` | `Cliente@12345` |
| Cliente | `cliente3` | `Cliente@12345` |
| Cliente | `cliente4` | `Cliente@12345` |
| Cliente | `cliente5` | `Cliente@12345` |

PINs de demonstração dos clientes, na mesma ordem: `1234`, `2345`, `3456`, `4567`, `5678`.

**Atenção:** essas credenciais são públicas e exclusivamente didáticas. Não as utilize em ambiente real. No primeiro acesso, siga a tela de configuração de credenciais quando ela for apresentada.

O seed não é necessário para iniciar a aplicação se o banco já tiver usuários e produtos cadastrados.

## Estrutura do projeto

```text
Cantina-da-Honestidade/
├── apli.py                 # Ponto de entrada Flask
├── core.py                 # Configuração da aplicação e funções compartilhadas
├── database.py             # Conexão e acesso ao MySQL
├── schema_service.py       # Criação/compatibilidade inicial do esquema
├── domain_utils.py         # Formatações e utilitários de domínio
├── routes/                 # Rotas por área funcional
├── services/               # Regras e serviços especializados
├── templates/              # Páginas Jinja/HTML
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/            # Imagens enviadas
├── scripts/
│   ├── seed.py             # Dados fictícios
│   ├── backup.py           # Backup MySQL + uploads
│   └── restaurar_backup.py # Restauração com confirmação
├── tests/                  # Testes automatizados
├── docs/
│   └── ARQUITETURA.md
├── requirements.txt
└── .env.example
```

## Testes

Com o ambiente virtual ativo, na raiz do projeto:

```powershell
python -m unittest discover -s tests -v
```

Os testes existentes cobrem serviços e regras selecionadas, como checkout, utilitários de domínio, tentativas de login, produtos, relatórios e recargas. A execução dos testes não substitui testes integrados com um banco MySQL de homologação nem testes de interface em navegadores/dispositivos reais.

## Backup e restauração

O backup está em `scripts/backup.py` e requer `mysqldump` disponível no PATH. Ele gera uma pasta com:
- dump SQL do banco;
- arquivo ZIP de `static/uploads`;
- manifesto com hashes SHA-256.

Execute:

```powershell
python .\scripts\backup.py
```

Por padrão, os arquivos são gravados em `backups/`. É possível definir `CANTINA_BACKUP_DIR` no `.env`.

A restauração requer o cliente `mysql` no PATH e solicita o caminho da pasta de backup e a confirmação literal `RESTAURAR`:

```powershell
python .\scripts\restaurar_backup.py
```

**Atenção:** restaurar substitui os dados do banco selecionado no `.env` e extrai os uploads do backup. Faça uma cópia de segurança atual antes de restaurar e confira cuidadosamente host e nome do banco.

O usuário MySQL configurado deve ter permissões adequadas para `mysqldump`/`mysql`. Configure as mesmas credenciais de banco no `.env usado pela aplicação e pelos scripts.

## Solução de problemas

### `ModuleNotFoundError`
Confirme que o ambiente virtual está ativo e reinstale as dependências:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### `Access denied for user`
Confira `CANTINA_DB_HOST`, `CANTINA_DB_PORT`, `CANTINA_DB_USER`, `CANTINA_DB_PASSWORD` e se o usuário MySQL tem acesso ao banco indicado.

### `Unknown database`
Crie `cantina_honestidade` no MySQL ou corrija `CANTINA_DB_NAME` no `.env`.

### Erro ao executar o seed
Execute o script a partir da raiz do projeto com:

```powershell
python .\scripts\seed.py
```

Não use `python seed.py` na raiz: o arquivo fica dentro de `scripts/`.

### Fotos não aparecem
Confira se o diretório `static/uploads` existe e se o processo tem permissão de leitura/escrita. As imagens de produtos e de perfil são armazenadas nessa área.

### Porta 5000 ocupada
Encerre o processo que está usando a porta ou ajuste a porta no bloco `app.run` de `apli.py` para desenvolvimento.

## Cuidados antes de publicar

A implantação institucional ainda exige preparação e homologação. Antes de disponibilizar o sistema:
1. usar servidor WSGI de produção (por exemplo, Gunicorn em Linux) e proxy reverso;
2. habilitar HTTPS com certificado válido;
3. configurar `APP_ENV=production`, `CANTINA_SECRET_KEY` forte e cookies seguros;
4. criar usuário MySQL exclusivo para a aplicação, com privilégios mínimos (evitar `root`);
5. manter MySQL inacessível diretamente pela internet;
6. configurar backup automatizado e testar restauração;
7. configurar permissões, monitoramento, logs e política de retenção;
8. executar testes integrados, de segurança, carga e acessibilidade;
9. validar o ambiente com a equipe responsável pela infraestrutura e proteção de dados.

Esses itens são recomendações de implantação; não significam que a aplicação já esteja publicada ou homologada em produção.
