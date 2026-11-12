# Confia+ — Cantina da Honestidade

Versão reorganizada para facilitar o estudo, a manutenção e a apresentação acadêmica. O ponto de entrada `apli.py` inicia a aplicação; `core.py` configura o Flask e disponibiliza funções compartilhadas; as rotas ficam separadas por assunto no pacote `routes/`; e os serviços especializados ficam distribuídos entre a raiz do projeto e o pacote `services/`. A visão estrutural está em `docs/ARQUITETURA.md`, e a descrição detalhada dos módulos, fluxos, transações e regras de negócio está em `docs/DOCUMENTACAO_TECNICA.md`.

> A integração com o MySQL deve ser testada no ambiente local com o banco configurado.

Sistema web acadêmico para administrar uma cantina baseada na honestidade. O Confia+ reúne cadastro de usuários, produtos, carteiras, compras e movimentações em uma aplicação Flask com banco de dados MySQL 8.

Este documento é um guia técnico de instalação, configuração, execução, backup e manutenção. Para conhecer as telas, os perfis e os procedimentos de uso, consulte também o [Manual do Usuário](MANUAL_DO_USUARIO.md). Siga as etapas na ordem: primeiro prepare o MySQL, depois configure o Python e o `.env`, inicie a aplicação e, se desejar, carregue os dados fictícios com o `scripts/seed.py`.

> **Atenção:** o código do projeto e o banco de dados são coisas diferentes. Baixar ou atualizar o ZIP não traz automaticamente os usuários, produtos, compras e saldos que já existem em outro computador. Para transferir dados, utilize backup e restauração.

## Sumário

1. [O que o sistema faz](#1-o-que-o-sistema-faz)
2. [Tecnologias](#2-tecnologias)
3. [Requisitos](#3-requisitos)
4. [Baixar e preparar o projeto](#4-baixar-e-preparar-o-projeto)
5. [Instalar e preparar o MySQL](#5-instalar-e-preparar-o-mysql)
6. [Configurar o `.env`](#6-configurar-o-env)
7. [Preparar o Python](#7-preparar-o-python)
8. [Iniciar e acessar o sistema](#8-iniciar-e-acessar-o-sistema)
9. [Carga opcional de demonstração: `scripts/seed.py`](#9-carga-opcional-de-demonstração-seedpy)
10. [Consultar dados no Workbench](#10-consultar-dados-no-workbench)
11. [Backup e restauração](#11-backup-e-restauração)
12. [Publicar o projeto em um servidor](#12-publicar-o-projeto-em-um-servidor)
13. [Estrutura dos arquivos](#13-estrutura-dos-arquivos)
14. [Solução de problemas](#14-solução-de-problemas)
15. [Segurança e cuidados](#15-segurança-e-cuidados)
16. [Comentários e documentação do código](#16-comentários-e-documentação-do-código)

## 1. O que o sistema faz

O Confia+ foi desenvolvido para apoiar a rotina de uma cantina baseada na honestidade. Entre os recursos implementados estão:

- gerenciamento de usuários com perfis e permissões diferentes;
- cadastro e gerenciamento de produtos e estoque;
- carteiras e consulta de saldo;
- registro e consulta de compras;
- recargas e movimentações;
- histórico, notificações com estado de leitura persistente e recursos administrativos;
- confirmação recorrente de ciência em compras enquanto a carteira estiver negativa;
- interfaces responsivas para desktop e dispositivos móveis.

As ações disponíveis variam conforme o perfil de acesso e as regras implementadas no sistema.

## 2. Tecnologias

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| Flask | Aplicação web |
| MySQL Server 8 | Banco de dados |
| MySQL Connector/Python | Comunicação entre Python e MySQL |
| HTML, CSS e JavaScript | Interface |
| Pillow | Manipulação de imagens |
| python-dotenv | Leitura das configurações do `.env` |

**MySQL Server e MySQL Workbench não são a mesma coisa.** O Server armazena os dados e precisa estar em execução. O Workbench é uma ferramenta gráfica opcional para administrar o servidor e executar consultas.

## 3. Requisitos

Para instalar localmente no Windows, tenha:

- Windows 10 ou 11;
- Python 3.12 ou 3.13;
- MySQL Server 8.0;
- PowerShell;
- MySQL Workbench (opcional, recomendado para visualizar o banco);
- Git (opcional, caso prefira clonar o repositório).

Para hospedar em servidor, consulte também a seção [12 — Publicar o projeto em um servidor](#12-publicar-o-projeto-em-um-servidor).

## 4. Baixar e preparar o projeto

1. Baixe o ZIP do projeto ou clone o repositório Git.
2. Extraia o ZIP em uma pasta local.
3. Abra o PowerShell dentro da pasta extraída.

A pasta correta é aquela que contém `apli.py`, `database.py`, `requirements.txt` e `.env.example`.

Confira:

```powershell
Get-ChildItem -Force
```

Se estiver usando Git, o comando de clonagem segue este formato:

```powershell
git clone URL_DO_REPOSITORIO
cd Cantina-da-Honestidade
```

Substitua `URL_DO_REPOSITORIO` pelo endereço real do repositório.

## 5. Instalar e preparar o MySQL

### 5.1 Instalar e iniciar o servidor

Instale o **MySQL Server 8.0**. Durante a instalação, defina a senha da conta `root` e guarde-a em local seguro.

No Windows, abra `services.msc` e confirme que o serviço do MySQL está em execução. O nome pode aparecer como `MySQL80`.

O MySQL local normalmente utiliza:

- Host: `localhost`
- Porta: `3306`
- Banco: `cantina_honestidade`

Se sua instalação utilizar outro host ou porta, use os valores reais no `.env`.

### 5.2 Criar o banco

Abra o MySQL Workbench e conecte-se à instância local usando o usuário `root` e a senha definida na instalação. Abra uma nova aba SQL e execute:

```sql
CREATE DATABASE cantina_honestidade
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Se o banco já existir, não é necessário criá-lo novamente. Não apague um banco existente para instalar uma versão nova do código.

> Nesta instalação, o projeto pode ser configurado para utilizar `root`, como no ambiente local já utilizado. Para um ambiente público, prefira uma conta exclusiva para a aplicação, com privilégios limitados ao banco `cantina_honestidade`.

## 6. Configurar o `.env`

O arquivo `.env` guarda as configurações locais, inclusive as credenciais do MySQL. O projeto inclui `.env.example` como modelo, mas a aplicação lê o arquivo `.env`.

Na pasta principal do projeto, execute:

```powershell
Copy-Item .env.example .env
notepad .env
```

Configure os valores. Exemplo para a instalação local que utiliza `root`:

```dotenv
APP_ENV=development
CANTINA_DB_HOST=localhost
CANTINA_DB_PORT=3306
CANTINA_DB_NAME=cantina_honestidade
CANTINA_DB_USER=root
CANTINA_DB_PASSWORD=COLOQUE_A_SENHA_DO_ROOT
```

Troque `COLOQUE_A_SENHA_DO_ROOT` pela senha definida no MySQL. Não inclua aspas desnecessárias e não deixe espaços antes ou depois dos valores.

O projeto também aceita `CANTINA_SECRET_KEY`. Em desenvolvimento local, se ela não estiver definida, o código utiliza uma chave fixa de desenvolvimento e exibe um aviso no terminal. **Em produção, essa variável é obrigatória e deve ser uma chave privada aleatória com pelo menos 32 caracteres.** Nunca reutilize a chave de exemplo.

Para gerar uma chave forte com Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado para o `.env`:

```dotenv
CANTINA_SECRET_KEY=COLE_AQUI_A_CHAVE_GERADA
```

Confira se o arquivo existe e não foi salvo como `.env.txt`:

```powershell
Get-ChildItem -Force .env*
```

Para verificar se a senha está carregada sem exibi-la:

```powershell
python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv('.env', override=True); print('Arquivo .env existe:', Path('.env').exists()); print('Usuário:', os.getenv('CANTINA_DB_USER')); print('Senha configurada:', bool(os.getenv('CANTINA_DB_PASSWORD'))); print('Banco:', os.getenv('CANTINA_DB_NAME'))"
```

O resultado esperado inclui `Arquivo .env existe: True` e `Senha configurada: True`. **Não envie o conteúdo do `.env` para outras pessoas nem o publique no GitHub.**

## 7. Preparar o Python

Os comandos abaixo devem ser executados na pasta principal do projeto.

### 7.1 Criar o ambiente virtual

```powershell
python -m venv .venv
```

### 7.2 Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute somente nesta janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Quando estiver ativo, o terminal mostrará `(.venv)` no início da linha.

### 7.3 Instalar as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` contém as bibliotecas Python utilizadas pela aplicação em execução local. Para desenvolvimento no Windows, o Flask inicia pelo comando `python apli.py`; não é necessário instalar Gunicorn. Se abrir um novo terminal, ative novamente o ambiente virtual antes de executar os comandos do sistema.

## 8. Iniciar e acessar o sistema

Antes de iniciar, confirme que:

- o serviço MySQL está em execução;
- o banco `cantina_honestidade` existe;
- o `.env` está configurado;
- o ambiente `(.venv)` está ativo;
- as dependências foram instaladas.

Inicie:

```powershell
python apli.py
```

Abra no navegador:

<http://127.0.0.1:5000>

Para encerrar, volte ao PowerShell e pressione `Ctrl + C`.

Na primeira inicialização, o projeto executa a inicialização/atualização estrutural do banco. Isso **não** insere automaticamente os usuários e produtos fictícios. A carga de demonstração é opcional e deve ser executada manualmente com `scripts/seed.py`.

O servidor iniciado com `python apli.py` é o servidor de desenvolvimento do Flask. Ele serve para testes locais, não para disponibilizar o sistema publicamente na internet.

## 9. Carga opcional de demonstração: `scripts/seed.py`

O `scripts/seed.py` insere registros fictícios para facilitar testes e demonstrações. Ele é opcional: não precisa ser executado se você quiser começar com uma base sem os dados de exemplo.

### 9.1 O que é criado

- 1 administrador;
- 2 operadores;
- 5 clientes;
- carteiras para as contas;
- 10 produtos fictícios.

Os clientes de demonstração incluem dados cadastrais ilustrativos previstos no código, como matrícula, CPF, telefone, data de nascimento e PIN. Esses dados não representam pessoas reais.

### 9.2 Como executar

Com o MySQL ligado, `.env` configurado e ambiente virtual ativo, execute na pasta do projeto:

```powershell
python scripts/seed.py
```

Aguarde a mensagem de conclusão no terminal. Se houver erro de conexão, confira primeiro o `.env` e o serviço MySQL.

### 9.3 Usuários, senhas e PINs de demonstração

A tabela abaixo foi conferida diretamente com a lista `USUARIOS` do arquivo `scripts/seed.py`. As credenciais são válidas para contas **criadas pelo seed em uma base nova**.

| Perfil | Nome | Usuário para login | Senha inicial | PIN de compra |
|---|---|---|---|---|
| Administrador | Administrador Demonstração | `admin` | `Admin@12345` | Não se aplica |
| Operador | Mariana Costa | `operador1` | `Operador@12345` | Não se aplica |
| Operador | Rafael Souza | `operador2` | `Operador@12345` | Não se aplica |
| Cliente | Ana Lima | `cliente1` | `Cliente@12345` | `1234` |
| Cliente | Marcos Alves | `cliente2` | `Cliente@12345` | `2345` |
| Cliente | Beatriz Oliveira | `cliente3` | `Cliente@12345` | `3456` |
| Cliente | Lucas Pereira | `cliente4` | `Cliente@12345` | `4567` |
| Cliente | Camila Martins | `cliente5` | `Cliente@12345` | `5678` |

**Como entrar:** abra `http://127.0.0.1:5000`, informe o valor da coluna **Usuário para login** e a respectiva **Senha inicial**. O PIN é solicitado somente ao cliente no momento de confirmar uma compra; ele não substitui a senha de acesso ao sistema.

Os PINs são compostos por quatro números. Administrador e operadores não recebem PIN de compra pelo seed.

**Importante sobre contas que já existem:** o `scripts/seed.py` não redefine senhas nem PINs de usuários existentes. Se você já executou o seed anteriormente, as credenciais acima só continuarão válidas se ninguém tiver alterado esses acessos depois. O script preserva senhas, PINs, dados preenchidos e saldos existentes. Para testar com as credenciais desta tabela em uma instalação já utilizada, confira/recupere o acesso pelo fluxo de administração do sistema; executar o seed novamente não restaura as senhas originais.

Os cinco clientes recebem saldo inicial de R$ 20,00 cada quando suas contas e carteiras são criadas. Administrador e operadores começam com saldo zero. Senhas e PINs são armazenados no banco como hashes, não em texto puro.

> Estas são credenciais públicas de demonstração. Use-as somente em ambiente local de testes. Nunca as mantenha em uma instalação real ou pública.

### 9.4 Produtos incluídos

| Produto | Preço de venda inicial | Estoque |
|---|---:|---:|
| Água mineral 500 ml | R$ 2,00 | 30 |
| Refrigerante lata | R$ 5,00 | 20 |
| Suco de caixinha | R$ 4,00 | 20 |
| Café | R$ 2,50 | 30 |
| Pão de queijo | R$ 3,00 | 25 |
| Salgado assado | R$ 5,00 | 20 |
| Sanduíche natural | R$ 8,00 | 12 |
| Biscoito | R$ 3,50 | 20 |
| Chocolate | R$ 4,50 | 15 |
| Barra de cereal | R$ 3,50 | 15 |

### 9.5 Posso executar o seed mais de uma vez?

O script foi preparado para evitar duplicações:

- usuários são procurados por nome de usuário **ou** e-mail;
- produtos são procurados pelo nome, sem diferenciar maiúsculas de minúsculas;
- contas já encontradas não são recriadas;
- para uma conta de demonstração já existente com perfil `cliente`, o script pode completar alguns campos cadastrais vazios: matrícula, CPF, telefone, data de nascimento e PIN; também completa o nome quando ele ainda contém somente o primeiro nome previsto no seed;
- o PIN só é preenchido quando `pin_hash` está vazio;
- senhas, PINs já cadastrados, dados já preenchidos e saldos de carteiras existentes não são substituídos;
- se uma conta encontrada ainda não tiver carteira, o script cria uma: R$ 20,00 para clientes e R$ 0,00 para administrador/operadores;
- compras, movimentações e outros registros não são apagados;
- produtos que já existem são ignorados, sem atualização de preço, estoque ou descrição.

O seed **não é uma rotina de atualização geral** e não sincroniza registros existentes com os exemplos. Ao final, o terminal informa quantas contas e produtos foram criados, ignorados ou conferidos/completados.

> **Não execute o seed em produção.** As contas e credenciais são públicas e servem apenas para demonstração/testes. Em uma instalação real, crie usuários próprios e defina credenciais individuais.

## 10. Consultar dados no MySQL Workbench

1. Abra o MySQL Workbench.
2. Conecte-se à instância local.
3. Atualize o painel **Schemas**.
4. Expanda `cantina_honestidade`.
5. Expanda **Tables** para visualizar as tabelas.

Consultas úteis:

```sql
USE cantina_honestidade;

-- Usuários
SELECT id, nome, sobrenome, username, email, perfil, ativo
FROM usuarios;

-- Produtos
SELECT id, nome, descricao, preco_compra, preco, estoque, ativo
FROM produtos;

-- Carteiras e respectivos usuários
SELECT u.username, u.nome, c.saldo
FROM usuarios u
JOIN carteiras c ON c.usuario_id = u.id;
```

A coluna de senha contém o hash, não a senha original.

## 11. Backup e restauração

O projeto possui `scripts/backup.py` e `scripts/restaurar_backup.py`. Os scripts salvam/restauram o banco MySQL e os arquivos de `static/uploads` incluídos na rotina. O backup gera uma pasta com o arquivo SQL, o ZIP dos uploads e um manifesto com checksums.

**Faça backups regulares e guarde uma cópia fora do computador/servidor.** A restauração substitui os dados do banco selecionado; confira o destino antes de confirmar.

### 11.1 Pré-requisito: localizar `mysqldump.exe` e `mysql.exe` no Windows

O backup utiliza `mysqldump.exe`. A restauração utiliza o cliente `mysql.exe`. Esses programas são instalados junto com o MySQL Server, mas o Windows pode não encontrá-los se a pasta `bin` não estiver no `PATH`.

Na instalação MySQL Server 8.0 usada como referência neste projeto, os executáveis ficam em:

```text
C:\Program Files\MySQL\MySQL Server 8.0\bin
```

Verifique se o Windows encontra o programa:

```powershell
where.exe mysqldump
where.exe mysql
```

Se o comando não localizar os executáveis, teste o caminho completo:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" --version
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```

Se aparecer a versão, os utilitários estão instalados. Falta apenas configurar o `PATH`.

### 11.2 Solução temporária (somente no PowerShell atual)

Para permitir que o `scripts/backup.py` encontre o `mysqldump` nesta janela do PowerShell, execute:

```powershell
$env:PATH += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"
```

Depois rode:

```powershell
python scripts/backup.py
```

Essa alteração vale apenas para a janela atual. Se fechar o PowerShell e abrir outro, será necessário executar o comando novamente. Para a restauração, a mesma pasta precisa estar no PATH, pois o script chama `mysql.exe`:

```powershell
python scripts/restaurar_backup.py
```

Se o MySQL estiver instalado em outra pasta ou versão, ajuste o caminho do comando para a pasta `bin` real.

### 11.3 Configurar o PATH permanentemente no Windows

Para não repetir o comando temporário:

1. Abra o menu Iniciar e pesquise **Editar as variáveis de ambiente do sistema**.
2. Abra **Variáveis de Ambiente**.
3. Em **Variáveis do sistema** (ou nas variáveis do usuário), selecione `Path` e clique em **Editar**.
4. Clique em **Novo**.
5. Adicione a pasta, sem colocar o nome do executável:

   ```text
   C:\Program Files\MySQL\MySQL Server 8.0\bin
   ```

6. Confirme todas as janelas com **OK**.
7. Feche e abra novamente o PowerShell.
8. Teste:

   ```powershell
   where.exe mysqldump
   where.exe mysql
   ```

O Windows deve mostrar o caminho dos executáveis. Não é necessário reinstalar o MySQL quando os arquivos já existem.

### 11.4 Executar o backup

Com MySQL em execução, `.env` configurado, ambiente virtual ativo e `mysqldump` no PATH:

```powershell
python scripts/backup.py
```

O script cria uma pasta dentro de `backups`, com nome baseado na data e hora, contendo:

- `cantina_honestidade.sql`: exportação do banco;
- `uploads.zip`: arquivos da pasta `static/uploads`;
- `manifest.json`: data de criação e checksums para verificar a integridade dos arquivos.

Se aparecer `Access denied`, confira se `CANTINA_DB_USER` e `CANTINA_DB_PASSWORD` no `.env` correspondem à conta MySQL. Os scripts de backup e restauração também leem `CANTINA_DB_HOST`, `CANTINA_DB_PORT`, `CANTINA_DB_NAME`, `CANTINA_DB_USER` e `CANTINA_DB_PASSWORD` do mesmo `.env`. Portanto, na instalação local, se a aplicação estiver configurada com `root`, os scripts usarão `root` também. Em produção, configure `cantina_app` (ou outro usuário exclusivo com privilégios adequados) e a mesma credencial no `.env`; não deixe `CANTINA_DB_USER` ou `CANTINA_DB_PASSWORD` ausentes, pois os scripts têm valores padrão de contingência que não devem ser usados como configuração de produção. Se aparecer `WinError 2` ou mensagem de que o arquivo não foi encontrado, confira o PATH e o caminho de `mysqldump.exe` ou `mysql.exe`.

### 11.5 Restaurar um backup

Antes de restaurar, confirme que o `.env` aponta para o banco correto e que `mysql.exe` está no PATH. Se possível, faça primeiro um backup do banco atual para poder voltar ao estado anterior. Execute:

```powershell
python scripts/restaurar_backup.py
```

O script solicitará o caminho completo da pasta de backup. Informe a pasta que contém `manifest.json`, `cantina_honestidade.sql` e `uploads.zip` (não informe apenas o arquivo ZIP externo do projeto). Depois exibirá o host e o banco de destino e pedirá a confirmação digitando exatamente `RESTAURAR`.

**Atenção:** a restauração importa o SQL no banco MySQL selecionado e extrai os uploads para a pasta do projeto, podendo sobrescrever arquivos de mesmo caminho. Faça um backup do estado atual antes de continuar. Nunca teste a restauração diretamente em uma base com dados importantes sem uma cópia de segurança.

### 11.6 Conferir e guardar o backup

Após a execução, abra a pasta `backups` e confira se a pasta da execução contém os três arquivos esperados: `cantina_honestidade.sql`, `uploads.zip` e `manifest.json`. Copie a pasta inteira para outro local seguro, preferencialmente outro dispositivo ou armazenamento remoto com acesso restrito. O diretório `backups/` está no `.gitignore`: os backups não devem ser enviados ao GitHub.

O script não agenda backups automaticamente nem apaga cópias antigas. Defina uma rotina de cópias compatível com a frequência de uso do sistema e acompanhe se as execuções terminaram sem erro. Periodicamente, teste a restauração em uma base separada. O manifesto valida a integridade dos arquivos, mas não substitui um teste real de recuperação.

## 12. Publicar o projeto em um servidor

Esta seção descreve uma implantação de referência para um servidor Linux (por exemplo, Ubuntu) com MySQL, Gunicorn e Nginx. Ela exige acesso administrativo ao servidor, domínio ou endereço público, firewall e configuração de HTTPS.

> **Importante:** executar `python apli.py` no computador local não coloca o sistema na internet. O servidor de desenvolvimento do Flask não deve ser usado como servidor público. A implantação pública também exige manutenção, atualizações, monitoramento e backups. Faça testes em ambiente separado antes de utilizar dados reais.

### 12.1 Preparar o servidor

1. Contrate ou disponibilize um servidor Linux com acesso SSH.
2. Aponte um domínio para o endereço IP do servidor, se houver domínio.
3. Atualize o sistema operacional.
4. Instale Python, ambiente virtual, pip, MySQL Server, Nginx e ferramentas necessárias.
5. Configure o firewall para permitir SSH e tráfego HTTP/HTTPS; não exponha a porta do MySQL publicamente.

Em Ubuntu, a instalação inicial pode seguir este exemplo:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip mysql-server nginx
```

### 12.2 Copiar o projeto

Copie o código para uma pasta de aplicação no servidor, por exemplo `/opt/confia-plus`. Não copie `.venv`, caches, `.env` de desenvolvimento nem backups antigos.

Entre na pasta e crie o ambiente:

```bash
cd /opt/confia-plus
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install gunicorn
```

O Gunicorn é o servidor WSGI utilizado neste exemplo de implantação Linux. Ele é uma dependência exclusiva do cenário de produção descrito aqui e é instalado separadamente porque não faz parte do `requirements.txt` da execução local. Não use `python apli.py` como servidor público.

### 12.3 Preparar o MySQL do servidor

Configure o MySQL para aceitar conexões locais do próprio servidor e crie o banco e um usuário exclusivo da aplicação. Exemplo de SQL, executado por uma conta administrativa:

```sql
CREATE DATABASE cantina_honestidade
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'cantina_app'@'localhost'
  IDENTIFIED BY 'DEFINA_UMA_SENHA_FORTE_E_UNICA';

GRANT ALL PRIVILEGES ON cantina_honestidade.*
  TO 'cantina_app'@'localhost';

FLUSH PRIVILEGES;
```

Use uma senha longa e exclusiva. Não use a senha de `root` na aplicação pública. Mantenha o MySQL acessível apenas localmente, salvo se houver uma arquitetura de rede privada devidamente protegida.

### 12.4 Configurar variáveis de produção

Crie um `.env` no diretório da aplicação, com permissões restritas. Exemplo:

```dotenv
APP_ENV=production
CANTINA_DB_HOST=localhost
CANTINA_DB_PORT=3306
CANTINA_DB_NAME=cantina_honestidade
CANTINA_DB_USER=cantina_app
CANTINA_DB_PASSWORD=DEFINA_UMA_SENHA_FORTE_E_UNICA
CANTINA_SECRET_KEY=COLOQUE_UMA_CHAVE_ALEATORIA_PRIVADA_COM_32_CARACTERES_OU_MAIS
```

Gere uma chave aleatória com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use o resultado em `CANTINA_SECRET_KEY`. Não reutilize a chave de desenvolvimento, não publique o `.env` e não o envie em mensagens ou repositórios. Restrinja as permissões do arquivo:

```bash
chmod 600 .env
```

### 12.5 Inicializar o banco e testar o servidor WSGI

Com o ambiente virtual ativo, teste a inicialização do esquema e a importação da aplicação:

```bash
python -c "from apli import app, initialize_database; app.app_context().push(); initialize_database(); print('Banco inicializado')"
gunicorn --bind 127.0.0.1:8000 --workers 2 apli:app
```

O Gunicorn fica escutando apenas em `127.0.0.1`, para que o Nginx seja a entrada pública. Teste localmente no servidor e encerre o processo de teste antes de configurar o serviço permanente.

**Não execute `scripts/seed.py` em produção.** Crie contas reais com credenciais próprias e verifique o primeiro acesso e as permissões antes de liberar o sistema.

### 12.6 Configurar Nginx e HTTPS

Configure o Nginx como proxy reverso para `127.0.0.1:8000`. O bloco de servidor deve encaminhar as requisições para o Gunicorn e preservar os cabeçalhos do cliente, host e protocolo. Exemplo básico de configuração dentro do bloco `server`:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Configure `server_name` com o domínio real, valide a configuração (`sudo nginx -t`) e recarregue o Nginx. Em seguida, configure certificado TLS/HTTPS válido para o domínio. Não considere o sistema pronto para uso público enquanto o HTTPS não estiver ativo.

### 12.7 Executar como serviço

Em vez de manter o Gunicorn aberto em um terminal, configure um serviço `systemd` para iniciar automaticamente após reinicializações, usando o diretório do projeto, o executável Gunicorn dentro de `.venv` e `apli:app`. O serviço deve executar com um usuário de sistema sem privilégios administrativos, ter acesso somente aos diretórios necessários e iniciar após o MySQL.

Depois de configurar o serviço, habilite-o, inicie-o e verifique os logs com `systemctl status` e `journalctl`. Os caminhos, usuário do serviço e nome do domínio precisam corresponder ao servidor real; não copie uma configuração genérica sem ajustá-la.

### 12.8 Checklist antes de liberar o acesso

- [ ] `APP_ENV=production`.
- [ ] `CANTINA_SECRET_KEY` privada e forte configurada.
- [ ] Usuário MySQL exclusivo da aplicação; não usar `root`.
- [ ] MySQL não exposto diretamente à internet.
- [ ] HTTPS válido e redirecionamento HTTP para HTTPS configurado.
- [ ] Nginx e Gunicorn executando como serviços.
- [ ] Contas de demonstração e seed não utilizados.
- [ ] Senhas iniciais substituídas e acessos conferidos.
- [ ] Backups automáticos e teste de restauração planejados.
- [ ] Logs, atualizações e monitoramento definidos.
- [ ] Testes de permissões feitos com cada perfil.

A implantação acima é um roteiro técnico de referência, não uma certificação de segurança. Antes de utilizar dados pessoais ou financeiros reais, revise a aplicação, suas dependências, controles de acesso, política de privacidade, proteção de dados, rotina de backup e plano de resposta a incidentes com pessoas responsáveis pela infraestrutura e segurança.

## 13. Estrutura dos arquivos

| Arquivo/pasta | Função |
|---|---|
| `apli.py` | Ponto de entrada: importa as rotas, inicializa o banco e inicia o servidor Flask de desenvolvimento |
| `core.py` | Configuração da aplicação Flask, autenticação, funções compartilhadas e integração entre módulos |
| `routes/` | Rotas organizadas por área: autenticação, perfil (incluindo notificações e ajuda), compras, operações e administração |
| `services/` | Serviços especializados de checkout, produtos, relatórios e recargas |
| `database.py` | Conexão, consultas e operações com MySQL |
| `schema_service.py` | Criação das oito tabelas do banco com `CREATE TABLE IF NOT EXISTS` |
| `services/wallet_service.py` | Consultas de saldo e registro de movimentações da carteira |
| `media_service.py` | Validação, processamento e armazenamento de imagens de perfil e produtos |
| `domain_utils.py` | Funções auxiliares de domínio, formatação e normalização |
| `scripts/seed.py` | Carga opcional de 8 contas e 10 produtos fictícios |
| `scripts/backup.py` | Backup do banco e dos uploads |
| `scripts/restaurar_backup.py` | Restauração de backup |
| `requirements.txt` | Dependências Python necessárias à execução local da aplicação |
| `.env.example` | Modelo de configuração; deve ser copiado para `.env` |
| `.gitignore` | Arquivos locais que não devem ser versionados |
| `templates/` | Páginas HTML/Jinja |
| `static/` | CSS concentrado em `css/app.css`, JavaScript concentrado em `js/app.js`, imagens e uploads |
| `tests/` | Testes automatizados dos serviços e funções do sistema |
| `docs/ARQUITETURA.md` | Descrição da arquitetura, módulos, dados e fluxos principais |

## 14. Solução de problemas

### Erro 1045 — `Access denied`

Exemplo:

```text
mysql.connector.errors.ProgrammingError: 1045 (28000):
Access denied for user 'root'@'localhost' (using password: YES)
```

`using password: YES` significa que uma senha foi enviada, mas o MySQL não a aceitou. Confira no `.env` se `CANTINA_DB_USER` e `CANTINA_DB_PASSWORD` correspondem ao usuário e senha do MySQL. Se estiver usando `root`, teste a mesma senha no Workbench. Verifique também host e porta. Não envie a senha para obter ajuda.

Se aparecer `using password: NO`, confira se o `.env` existe, está na pasta correta, tem o nome exato `.env` e contém `CANTINA_DB_PASSWORD` preenchida.

### Erro `WinError 2` ao executar `scripts/backup.py`

O Windows não encontrou `mysqldump.exe`. Siga a seção [11.1 e 11.2](#11-backup-e-restauração): confira a pasta `C:\Program Files\MySQL\MySQL Server 8.0\bin` e adicione-a temporariamente ao PATH ou configure o PATH permanentemente.

### Erro de conexão recusada

Verifique se o serviço MySQL está iniciado e se `CANTINA_DB_HOST` e `CANTINA_DB_PORT` estão corretos.

### `ModuleNotFoundError`

Ative o ambiente virtual e execute:

```powershell
python -m pip install -r requirements.txt
```

### `python` não é reconhecido no Windows

Tente `py` no lugar de `python`. Use o mesmo comando para criar o ambiente virtual e executar o projeto.

### Erro de token CSRF

Atualize a página de login e tente novamente. Mantenha o mesmo endereço durante a sessão (por exemplo, use sempre `http://127.0.0.1:5000`, sem alternar entre `localhost` e `127.0.0.1`). Não desative a proteção CSRF para contornar o erro.

### Usuários ou produtos de demonstração não aparecem

A aplicação não insere os exemplos automaticamente. Ative o ambiente virtual e execute `python scripts/seed.py`. Confira as mensagens do terminal e se o `.env` aponta para o banco esperado.

### Erro de sintaxe SQL

Confirme que está utilizando MySQL Server 8.0 e que a aplicação aponta para o banco correto. Não misture uma base SQLite antiga com esta versão MySQL do projeto.

## 15. Segurança e cuidados

- Nunca publique `.env`, senhas, chaves secretas ou backups com dados reais.
- Não use as credenciais públicas do seed em produção.
- Não exponha a porta 3306 do MySQL diretamente à internet.
- Utilize HTTPS em toda implantação pública.
- Use uma conta MySQL exclusiva e com privilégios mínimos em produção.
- Restrinja o acesso aos diretórios de backup e uploads.
- Faça backup antes de atualizações e restaurações.
- Revise `git status` antes de enviar alterações ao GitHub:

```bash
git status --short
```

O `.gitignore` já prevê ignorar `.env`, ambientes virtuais, caches e backups, mas confira se nenhum segredo já foi adicionado ao histórico do Git. Se uma credencial tiver sido publicada, altere-a; apagar o arquivo em um commit posterior não invalida a credencial exposta.

---

**Confia+ — Cantina da Honestidade**  
Projeto acadêmico desenvolvido com Python, Flask e MySQL.


## 16. Comentários e documentação do código

Os módulos Python documentam suas responsabilidades com docstrings. Os scripts JavaScript, a folha CSS e os templates Jinja2 possuem comentários de identificação e explicações nos fluxos relevantes. Os comentários priorizam regras de negócio, decisões e interações que não são evidentes pela leitura isolada de uma instrução.

A documentação funcional e técnica fica distribuída entre:
- `MANUAL_DO_USUARIO.md`: procedimentos por perfil e regras visíveis ao usuário;
- `docs/ARQUITETURA.md`: módulos, banco de dados, fluxos e integrações;
- `docs/PRIMEIRO_ACESSO_BLOQUEIO_TOTAL.md`: bloqueio e configuração inicial;
- `docs/REVISAO_CORRECOES_TRANSACIONAIS_E_LOGIN.md`: transações, saldo negativo, login e notificações;
- `docs/AUDITORIA_FINAL.md`: escopo, validações realizadas e limitações conhecidas.

Ao alterar o código, atualize os documentos correspondentes. Não coloque credenciais reais no ZIP: configure o `.env` localmente a partir de `.env.example`.


## Organização dos diretórios

- `services/`: serviços de negócio compartilhados, incluindo a carteira.
- `scripts/`: backup, restauração e carga opcional de dados fictícios.
- `routes/`: rotas HTTP organizadas por área funcional.
- `templates/`: páginas e componentes Jinja2.
- `static/`: CSS, JavaScript e arquivos enviados.
- `tests/`: testes automatizados.
- `docs/`: documentação técnica e relatórios de revisão.

Os comandos administrativos devem ser executados a partir da raiz do projeto, usando o caminho `scripts/`, por exemplo: `python scripts/seed.py`.
