# Revisão técnica — transações de compra, saldo negativo e limite de login

## Estado descrito nesta versão

### 1. Compra transacional

A rota `routes/shopping.py` valida o PIN, recebe a chave de idempotência e coordena as mensagens do fluxo. O processamento financeiro e de estoque está concentrado em `services/checkout_service.py`.

O serviço:
- valida carrinho, quantidades, disponibilidade e estoque;
- bloqueia as linhas de produtos e carteira durante o processamento;
- calcula o saldo projetado;
- registra compra, itens, baixa de estoque e movimentação financeira;
- confirma todas as alterações em uma transação ou desfaz a operação em caso de erro.

A chave de idempotência impede que uma mesma solicitação seja registrada mais de uma vez conforme a validação implementada no fluxo.

### 2. Regra de confirmação de saldo negativo

A carteira pode ficar negativa. A confirmação funciona de acordo com o saldo atual:
- na primeira compra que projetar saldo negativo, o cliente precisa confirmar ciência;
- enquanto o saldo atual continuar negativo, cada compra seguinte também exige nova confirmação;
- quando uma recarga quitar o saldo negativo e o saldo voltar a zero ou ficar positivo, essa confirmação deixa de ser exigida, salvo se uma compra futura voltar a projetar saldo negativo e ainda não houver registro inicial de ciência.

O registro `CIENCIA_SALDO_NEGATIVO` em `logs_auditoria` é criado uma única vez por cliente. A confirmação visual pode ser solicitada novamente em compras posteriores sem duplicar esse registro de auditoria.

### 3. Tentativas de login

O controle de tentativas é persistido na tabela `login_attempts`, provisionada por `schema_service.py`. O contador é associado à conta identificada; username e e-mail da mesma conta compartilham o contador. Para identificadores inexistentes, é utilizada uma chave derivada por SHA-256, evitando persistir o identificador em texto puro.

O limite configurado no serviço é de 8 falhas por janela de 5 minutos e é limpo após login bem-sucedido.

### 4. Notificações do cliente

O resumo de notificações é utilizado pelas interfaces desktop e mobile. A seleção de uma notificação chama a rota autenticada que marca como lida a notificação pertencente ao cliente da sessão. O contador representa notificações não lidas; a leitura é persistida no banco e não deve reaparecer após recarregar a página.

### 5. Primeiro acesso

Enquanto `usuarios.precisa_definir_acesso = 1`, o bloqueio é aplicado no backend. Operadores e administradores definem senha e confirmação; clientes também definem PIN e confirmação. A navegação principal fica oculta até a conclusão do fluxo.

## Validação e limites

Os testes automatizados cobrem serviços e funções isoladas, mas não substituem teste integrado. A validação funcional completa deve ser realizada com Flask, dependências e MySQL ativos, incluindo:
- compra com saldo positivo;
- primeira compra que deixa a carteira negativa;
- compra seguinte com saldo ainda negativo;
- recarga que quita o saldo negativo;
- leitura de notificação em desktop e mobile;
- bloqueio de primeiro acesso por perfil;
- limite de tentativas de login.

