# Confia+ — Manual do Usuário

Este manual descreve as funções encontradas na versão atual do código do Confia+. O acesso e as opções disponíveis variam conforme o perfil da conta. Os nomes de menus podem mudar em versões futuras.

## Sumário

1. [Perfis de acesso](#1-perfis-de-acesso)
2. [Primeiro acesso e login](#2-primeiro-acesso-e-login)
3. [Rotina do cliente](#3-rotina-do-cliente)
4. [Rotina do operador](#4-rotina-do-operador)
5. [Rotina do administrador](#5-rotina-do-administrador)
6. [Notificações](#6-notificações)
7. [Regras importantes do sistema](#7-regras-importantes-do-sistema)
8. [Limitações e cuidados](#8-limitações-e-cuidados)

Para instalar, configurar o banco, executar a carga de demonstração ou fazer backup e restauração, consulte o [README técnico](README.md).

## 1. Perfis de acesso

O sistema possui três perfis:

| Perfil | O que pode fazer |
|---|---|
| Cliente | Consultar saldo e movimentações, navegar pelo cardápio, adicionar produtos ao carrinho, confirmar compras com PIN, consultar histórico e editar o próprio perfil e credenciais. |
| Operador | Consultar clientes e produtos, cadastrar clientes, cadastrar/editar/ativar/desativar produtos, registrar recargas, redefinir senha de clientes e consultar informações operacionais. |
| Administrador | Consultar painel administrativo, gerenciar contas de administradores e operadores, redefinir senhas dessas contas, consultar relatórios e logs de auditoria. |

O administrador não substitui o operador nas rotinas de cadastro de clientes, produtos e recargas. O operador não gerencia contas de administradores ou outros operadores. Essas restrições são aplicadas também nas rotas do servidor, não apenas na apresentação dos menus.

## 2. Primeiro acesso e login

Para testar a aplicação com as contas fictícias, execute primeiro `python scripts/seed.py` conforme as instruções do README. A lista completa de usuários, senhas e PINs está na seção **9.3 — Contas de demonstração** do README. Essas credenciais são públicas e não devem ser utilizadas em produção.

Acesse o endereço da aplicação e informe o nome de usuário ou e-mail e a senha. Matrícula e CPF são dados cadastrais e não são identificadores aceitos no login.

Contas criadas pela equipe recebem uma senha temporária. No primeiro acesso, o sistema exige a definição de uma senha pessoal. Para clientes, também exige a criação de um PIN de pagamento com exatamente quatro números. Para administradores e operadores, o primeiro acesso solicita a troca da senha temporária.

A senha deve ter entre 8 e 20 caracteres, com pelo menos uma letra e um número. Não compartilhe senha ou PIN. Para sair, use a opção de encerramento de sessão.

## 3. Rotina do cliente

### 3.1 Consultar a carteira

Na página inicial, o cliente visualiza o saldo disponível e as movimentações recentes. O saldo é atualizado após compras e recargas registradas pela equipe.

### 3.2 Escolher produtos

Abra o cardápio para visualizar produtos ativos com estoque disponível. É possível adicionar itens ao carrinho pela listagem ou utilizar o fluxo de leitura do QR Code exibido para o produto, quando disponível.

### 3.3 Revisar e confirmar a compra

No carrinho, confira os produtos, quantidades e total. Ao finalizar, informe o PIN de pagamento. O sistema valida o PIN, confere novamente o estoque e registra a compra, os itens, a baixa de estoque e a movimentação financeira.

A compra é debitada da carteira. O sistema permite que o saldo fique negativo: nesse caso, a compra é registrada e o valor pendente será compensado por recargas futuras. Enquanto a carteira permanecer com saldo negativo, a mensagem de aviso sobre o saldo negativo será exibida nas compras realizadas.

Se o estoque tiver sido alterado e não for mais suficiente, a compra não é concluída; revise o carrinho. Se houver dúvida sobre uma tentativa de compra, consulte o histórico antes de tentar novamente.

### 3.4 Consultar histórico

A opção de histórico apresenta as compras do próprio cliente, os itens registrados e o total gasto. O cliente também pode consultar as movimentações recentes na página inicial.

### 3.5 Perfil e segurança

Na página de perfil, o usuário pode atualizar seus dados pessoais e foto, alterar a senha e, no caso de clientes, alterar o PIN de pagamento. A senha e o PIN são armazenados como hashes, não como texto simples.

## 4. Rotina do operador

### 4.1 Cadastrar cliente

Acesse a área de clientes e utilize a opção de novo cadastro. O formulário solicita dados cadastrais e cria uma carteira para o cliente. O sistema gera uma senha temporária para ser entregue diretamente ao titular, em particular. No primeiro acesso, o cliente deverá definir a própria senha e o PIN.

O cadastro pode ser recusado se matrícula, e-mail, CPF ou nome de usuário já estiverem em uso. A matrícula, CPF e e-mail devem ser conferidos antes de salvar.

### 4.2 Consultar e administrar clientes

Na listagem de clientes, o operador pode consultar os registros e utilizar as ações disponíveis para editar dados, ativar/desativar contas e redefinir a senha de clientes. A redefinição gera uma senha temporária; o cliente deverá trocá-la no próximo acesso. A desativação preserva o histórico.

### 4.3 Cadastrar e manter produtos

Na área de gerenciamento de produtos, informe nome, descrição, preço de compra, preço de venda, quantidade em estoque e, opcionalmente, foto. Produtos podem ser editados e ativados/desativados. A desativação não apaga o registro nem o histórico de compras associado.

O cardápio do cliente exibe apenas produtos ativos e com estoque maior que zero. A visão do operador também permite consultar produtos inativos ou sem estoque.

### 4.4 Registrar recarga

Acesse Recargas, selecione o cliente pela matrícula e informe o valor. **Registre a recarga somente depois de confirmar o recebimento físico do dinheiro.** Após a confirmação, o valor é somado à carteira e uma movimentação e notificação são registradas.


### 5.1 Painel administrativo

O painel apresenta indicadores de contas ativas, compras, vendas e recargas no período exibido, clientes com saldo negativo, valor total negativo e movimentações recentes. Confira o período indicado na tela antes de interpretar os números.

### 5.2 Gerenciar contas da equipe

Na área de usuários, o administrador pode criar e gerenciar contas administrativas e de operadores, editar os dados permitidos, ativar/desativar contas e redefinir senhas. O sistema impede desativar a própria conta pela tela e impede que todas as contas de administrador fiquem inativas.

### 5.3 Relatórios e auditoria

A área de relatórios apresenta o histórico de movimentações e informações financeiras consolidadas. A área de logs de auditoria registra ações relevantes, responsável, alvo, detalhes e data. O acesso aos logs e relatórios administrativos é restrito ao perfil administrador.

## 6. Notificações

O sistema registra notificações para o cliente em eventos como recargas. O cliente pode consultar o aviso no balão de notificações ou abrir a página com a lista completa.

O balão apresenta o resumo mais recente e está disponível nas versões desktop e mobile. Ao clicar em uma notificação, ela é marcada como lida no sistema. O contador considera somente notificações não lidas; depois de marcada como lida, a notificação não volta a aumentar o contador ao atualizar a página ou entrar novamente. Outras notificações ainda não lidas continuam sendo contabilizadas.

## 7. Regras importantes do sistema

- Compras exigem PIN válido e estoque suficiente.
- O preço aplicado na compra é o preço de venda cadastrado no produto.
- A compra reduz o estoque e o saldo da carteira na mesma operação transacional.
- O saldo negativo é permitido. A primeira compra que deixar a carteira negativa exige confirmação; enquanto o saldo atual permanecer negativo, cada nova compra também exige confirmação. O registro de ciência é mantido uma única vez na auditoria. Recargas aumentam o saldo e reduzem o valor pendente; quando o saldo chega a zero ou fica positivo, o aviso deixa de ser exigido.
- Recargas representam dinheiro recebido fisicamente; não registre crédito antes do recebimento.
- Contas desativadas não podem entrar no sistema, mas seus registros históricos são preservados.
- O cadastro público não cria contas: clientes devem solicitar cadastro à equipe da cantina.

## 8. Limitações e cuidados

Este manual descreve o comportamento encontrado no código analisado. Não foi realizado teste integrado com uma instância real do MySQL durante a elaboração deste documento. A conciliação de caixa possui estrutura de dados no banco, mas não foi identificada uma tela/rota de operação correspondente nesta versão; portanto, não é descrita como funcionalidade disponível na interface.

A documentação não substitui treinamento operacional. Antes de usar o sistema com dados reais, valide os fluxos de compra, recarga e permissões e restauração de backup em ambiente de teste. As contas e os dados do `scripts/seed.py` são fictícios e destinados apenas à demonstração.


## 9. Ordenação e busca nas listagens

Nas telas que oferecem ordenação, o usuário pode selecionar o cabeçalho da coluna para ordenar os registros conforme o conteúdo exibido. A disponibilidade de cada coluna depende da listagem e do perfil de acesso. Na busca de clientes para recarga, digite parte do nome ou da matrícula, selecione o resultado desejado e confirme a operação.

## 10. Perfil em dispositivos móveis

O operador e o administrador podem acessar a área de perfil pelo menu mobile. Nela, estão disponíveis os dados da conta e as opções de edição e segurança autorizadas ao próprio perfil. A apresentação mobile utiliza cartões e navegação inferior, sem alterar as permissões aplicadas pelo servidor.
