# Primeiro acesso — bloqueio total

## Regra implementada

Enquanto `usuarios.precisa_definir_acesso = 1`, qualquer usuário autenticado permanece restrito à rota de primeiro acesso. O bloqueio é aplicado no backend por um `before_request`; portanto, não depende de menus, tamanho de tela ou dispositivo.

São permitidos apenas:
- a rota de primeiro acesso, para concluir a configuração;
- a rota de saída, para encerrar a sessão;
- arquivos estáticos necessários para renderizar a tela.

## Credenciais exigidas por perfil

- **Operador e administrador:** nova senha e confirmação.
- **Cliente:** nova senha e confirmação, além de PIN de pagamento e confirmação.

A senha deve atender às regras de validação do formulário. O PIN do cliente deve possuir quatro dígitos. Os valores são armazenados como hashes.

## Interface

Durante a configuração, a navegação principal, a barra lateral desktop e a navegação mobile ficam ocultas. A tela é responsiva e não apresenta ação de voltar para as áreas internas.

## Persistência

O acesso é liberado somente quando a rota valida as confirmações e atualiza `precisa_definir_acesso` para `0`. Se o usuário sair antes de concluir, o indicador permanece ativo e o bloqueio volta a ser aplicado no próximo login.

## Arquivos relacionados

- `core.py`: bloqueio global de requisições durante o primeiro acesso.
- `routes/auth.py`: validação e gravação das novas credenciais.
- `templates/first_access.html`: formulário de configuração inicial.
- `templates/base.html`: ocultação da navegação durante o fluxo.

## Validação

A implementação deve ser testada com MySQL em execução, para operador, administrador e cliente, em desktop e mobile. Os testes unitários e a compilação sintática não substituem esse teste integrado.
