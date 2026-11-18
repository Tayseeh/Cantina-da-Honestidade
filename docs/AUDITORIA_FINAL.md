# Auditoria e documentação — Confia+ / Cantina da Honestidade

## Escopo desta revisão

Revisão do pacote recebido em 11/11/2026, com foco em:
- comentários e docstrings no código;
- alinhamento dos arquivos Markdown com o comportamento implementado;
- sintaxe Python, templates Jinja2 e scripts JavaScript;
- execução dos testes automatizados disponíveis;
- segurança do pacote de distribuição.

A revisão foi documental e estática. Não foram alteradas regras de negócio, consultas SQL, rotas, estilos funcionais ou fluxos da aplicação; foram adicionados comentários explicativos e atualizada a documentação.

## Documentação aplicada

- Módulos Python: preservadas e revisadas as docstrings existentes que descrevem módulos, classes e funções.
- JavaScript: adicionados cabeçalhos e comentários nos fluxos de sugestão de preço, ordenação de tabelas, busca/seleção de clientes para recarga e confirmação visual de compra.
- CSS: identificado o propósito da folha consolidada e preservados os comentários de seções já existentes.
- Templates Jinja2: adicionados comentários de identificação para explicar a responsabilidade de cada tela.
- Markdown: atualizados `README.md`, `MANUAL_DO_USUARIO.md` e os documentos de arquitetura, primeiro acesso e revisão transacional/login. Este relatório registra o escopo e as limitações da validação.

## Regras de negócio refletidas na documentação

### Compra e saldo negativo
- A primeira compra que projeta saldo negativo exige confirmação do cliente.
- Enquanto o saldo atual continuar negativo, cada compra seguinte também exige confirmação.
- O registro de ciência `CIENCIA_SALDO_NEGATIVO` é mantido uma única vez por cliente em `logs_auditoria`; novas confirmações não duplicam esse registro.
- Quando recargas levam o saldo a zero ou a um valor positivo, a confirmação recorrente deixa de ser exigida.

### Notificações
- O resumo de notificações é compartilhado pelas interfaces desktop e mobile.
- Ao selecionar uma notificação, o backend marca como lida a notificação pertencente ao usuário autenticado.
- O contador considera apenas notificações não lidas e a leitura permanece após atualizar a página.

### Primeiro acesso
- O bloqueio ocorre no backend enquanto `precisa_definir_acesso` estiver ativo.
- Operadores e administradores definem senha; clientes definem senha e PIN.
- A navegação principal permanece indisponível até a conclusão.

### Banco de dados
O esquema atual contém nove tabelas, incluindo `login_attempts`, utilizada para persistir tentativas de autenticação.

## Validações executadas

- **19 testes automatizados:** aprovados.
- **28 arquivos Python:** compilação sintática aprovada.
- **20 templates Jinja2:** análise sintática aprovada.
- **5 arquivos JavaScript:** `node --check` aprovado.
- Integridade do ZIP final: verificada.
- Arquivo `.env` local: excluído do pacote de distribuição; `.env.example` preservado.

## Limitações

Não foi executada uma sessão real do Flask conectada ao MySQL, nem testes de navegação automatizados em navegador. Portanto, esta revisão não atesta o funcionamento integrado de login, compras, recargas, notificações ou layouts em dispositivos reais. Esses fluxos devem ser conferidos no ambiente local após instalar as dependências e configurar o `.env`.

## Orientação para manutenção

Comentários devem explicar intenção, regra de negócio, motivo de uma validação ou relação entre componentes. Evite comentários que apenas repitam a instrução seguinte. Quando uma regra mudar, atualize simultaneamente o código, o manual do usuário e a documentação técnica correspondente.
