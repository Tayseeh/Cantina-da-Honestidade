# Manual do Usuário — Confia+

## 1. Apresentação

O Confia+ apoia a operação da Cantina da Honestidade. O sistema organiza o catálogo, o saldo das carteiras, as compras, as recargas e as atividades de gestão.

A interface apresenta recursos diferentes conforme o perfil autenticado: **Cliente**, **Operador** ou **Administrador**.

Este manual descreve os fluxos encontrados na versão atual do código. A disponibilidade de alguns itens pode variar conforme o perfil e o estado da conta.

## 2. Acesso ao sistema

1. Abra o endereço disponibilizado pela equipe responsável.
2. Informe seu nome de usuário/e-mail e senha, conforme os campos da tela.
3. No primeiro acesso, siga a etapa de definição de credenciais, quando solicitada.
4. Para sair, utilize a opção **Sair da conta**.

As contas podem ser bloqueadas temporariamente após sucessivas tentativas inválidas de autenticação. Se isso ocorrer, aguarde o período de bloqueio ou solicite orientação ao responsável pelo sistema.

## 3. Perfil Cliente

### 3.1 Consultar produtos

1. Acesse **Produtos/Cardápio**.
2. Navegue pelas categorias disponíveis: **Salgadinhos**, **Biscoitos e Bolinhos**, **Doces e Balas** e **Bebidas**.
3. Use o campo de busca para localizar um produto.
4. Confira nome, imagem, preço e disponibilidade antes de adicionar ao carrinho.

Apenas produtos ativos e disponíveis para venda devem ser apresentados para compra.

### 3.2 Adicionar produtos ao carrinho

1. Selecione o produto desejado.
2. Use o botão de adicionar.
3. Ajuste a quantidade no carrinho, se necessário.
4. Confira os itens e o total antes de finalizar.

O QR Code é um atalho para localizar o produto e iniciar sua inclusão no carrinho. A leitura do código não confirma nem paga a compra.

### 3.3 Finalizar uma compra

1. Abra **Carrinho**.
2. Revise os produtos, quantidades e total.
3. Informe o PIN de pagamento solicitado.
4. Se a compra fizer o saldo passar de zero/positivo para negativo, leia e confirme a ciência sobre o saldo negativo.
5. Conclua a operação e aguarde a confirmação do sistema.

O backend valida novamente o estoque, a situação do produto e o PIN no momento da confirmação. Se o estoque não for suficiente ou o produto não estiver disponível, a compra não deve ser concluída.

### 3.4 Entender o saldo negativo

A carteira pode ficar negativa conforme a regra de negócio configurada. A confirmação de ciência é solicitada quando uma compra faz o saldo passar de não negativo para negativo. Enquanto a carteira continuar negativa, compras adicionais não repetem essa confirmação. Se uma recarga elevar o saldo para zero ou acima e uma compra posterior voltar a deixá-lo negativo, será solicitada nova confirmação.

### 3.5 Consultar histórico e notificações

- Acesse **Meus pedidos/Histórico** para consultar compras registradas.
- Acesse **Notificações** para visualizar mensagens recebidas.
- Acesse **Meu perfil** para consultar ou atualizar os dados pessoais permitidos na tela.

## 4. Perfil Operador

O Operador atua na rotina da cantina. As funções abaixo dependem das permissões implementadas para esse perfil.

### 4.1 Gerenciar clientes

1. Abra **Clientes**.
2. Use a busca por nome, matrícula ou e-mail.
3. Utilize o filtro para visualizar todos, clientes com saldo negativo e demais situações disponíveis.
4. Para cadastrar, selecione **Cadastrar** e preencha os campos obrigatórios.
5. Para gerenciar um cliente, abra o menu de três pontinhos da respectiva linha.
6. Escolha a ação desejada, como editar dados, ativar/desativar ou redefinir acesso, conforme as opções apresentadas.

A matrícula é exibida com formatação visual em grupos. A formatação não altera o valor armazenado no banco.

### 4.2 Gerenciar produtos

1. Abra **Produtos**.
2. Pesquise pelo nome e use os filtros de situação e categoria.
3. Para cadastrar, selecione **Cadastrar** e informe nome, descrição, categoria, preço de compra, preço de venda, estoque, limite de estoque baixo e imagem, conforme os campos apresentados.
4. Para editar, abra os três pontinhos do produto e escolha **Editar**.
5. Faça as alterações no modal e salve.

O campo de preço sugerido calcula o preço de venda com base no custo acrescido de 50%. A sugestão é uma referência; o operador deve conferir o valor antes de salvar.

O status apresentado considera a situação do produto e seu estoque. Produtos podem ser desativados sem apagar o registro histórico.

### 4.3 Registrar recarga

1. Abra **Recargas**.
2. Localize o cliente usando os dados solicitados pela tela.
3. Informe o valor recebido.
4. Confirme o registro somente depois de receber o dinheiro fisicamente.
5. Confira a confirmação e o histórico de recargas.

**Importante:** o fluxo implementado registra recargas em dinheiro. Não considere que o sistema processa Pix, cartão ou integração bancária.

## 5. Perfil Administrador

### 5.1 Gerenciar usuários da equipe

1. Abra a área de usuários.
2. Pesquise o administrador ou operador.
3. Use o menu de três pontinhos da linha.
4. Para editar, selecione **Editar**. O formulário é aberto em um modal.
5. Atualize os campos permitidos e selecione **Salvar**.
6. Para cancelar, feche o modal ou use **Cancelar**.

O próprio administrador conectado não pode alterar seu próprio perfil administrativo por essa tela. O Administrador gerencia contas da equipe; a gestão de clientes pertence ao fluxo do Operador.

### 5.2 Relatórios

Acesse **Relatórios** para consultar os indicadores e informações disponíveis, como movimentações, vendas, recargas, clientes com saldo negativo e produtos mais vendidos, respeitando o período selecionado na interface.

Os resultados refletem os registros existentes no banco. Um painel sem vendas ou recargas no período pode apresentar tabelas vazias ou mensagens de ausência de registros.

### 5.3 Logs de auditoria

Acesse **Logs de auditoria** para consultar ações relevantes registradas pelo sistema, incluindo responsável, ação, alvo, detalhes e data. Os logs apoiam a rastreabilidade; não substituem uma política institucional de auditoria e retenção.

## 6. Regras e cuidados operacionais

- Confira o nome e o preço antes de confirmar uma compra.
- Confirme fisicamente o recebimento do dinheiro antes de registrar uma recarga.
- Não compartilhe senha ou PIN.
- Não utilize contas de demonstração em operação real.
- Não tente corrigir saldos diretamente no banco sem procedimento autorizado e registro.
- Em caso de erro, anote a tela, o horário, o usuário e a mensagem apresentada e encaminhe ao suporte responsável.

## 7. Perguntas frequentes

**Esqueci minha senha.**  
Solicite ao Operador ou Administrador responsável a redefinição de acesso, conforme seu perfil. O fluxo gera uma senha temporária que deve ser alterada no acesso solicitado pelo sistema.

**O produto aparece sem estoque.**  
O operador deve conferir o estoque cadastrado e atualizar a quantidade, se houver reposição física.

**O sistema recusou a compra.**  
Confira se o produto continua ativo, se há estoque suficiente e se o PIN foi informado corretamente. A validação final ocorre no servidor.

**Por que apareceu a confirmação de saldo negativo?**  
A compra está projetada para levar a carteira de zero/positivo para um valor negativo. Leia a mensagem antes de confirmar.

**A recarga não aparece.**  
Confirme se a operação foi concluída e consulte o histórico. Se persistir, informe ao suporte o cliente, valor aproximado e horário; não registre novamente sem verificar se a primeira operação foi processada.

**A matrícula parece diferente da digitada.**  
A tela agrupa os dígitos para facilitar a leitura. O agrupamento é apenas de apresentação.

## 8. Limites desta versão

O sistema registra operações e organiza informações, mas não comprova por si só redução de perdas, não realiza conciliação bancária e não substitui o controle físico do dinheiro recebido. A implantação em produção depende de homologação técnica e operacional.
