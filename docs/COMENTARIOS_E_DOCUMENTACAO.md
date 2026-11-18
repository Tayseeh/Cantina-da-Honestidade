# Comentários e documentação do código

## Padrão adotado

Os comentários foram escritos em português e priorizam:
- responsabilidade de módulos, arquivos e telas;
- regras de negócio e condições que não são óbvias;
- relação entre eventos de interface e dados enviados ao backend;
- comportamentos que precisam ser preservados em futuras alterações.

Não foi adicionado comentário em cada linha. Isso geraria ruído e duplicaria o que a própria instrução já informa.

## Onde encontrar explicações

| Área | Arquivos | O que está documentado |
|---|---|---|
| Inicialização e backend | `apli.py`, `core.py`, `database.py` | Inicialização, sessão, autenticação, acesso ao banco e funções compartilhadas. |
| Regras de negócio | `services/wallet_service.py`, `services/` | Carteira, compras, produtos, recargas, relatórios e tentativas de login. |
| Rotas | `routes/` | Fluxos HTTP e permissões por perfil. |
| Interface | `templates/` | Responsabilidade de cada tela e estrutura Jinja2. |
| JavaScript | `static/js/` | Busca de clientes, ordenação, sugestão de preço, confirmação e interações compartilhadas. |
| Estilos | `static/css/app.css` | Estilos consolidados e seções responsivas. |
| Testes | `tests/` | Cenários automatizados que verificam os serviços e funções. |

## Documentos relacionados

- `../README.md`: instalação, configuração, execução e manutenção.
- `../MANUAL_DO_USUARIO.md`: instruções de uso por perfil.
- `ARQUITETURA.md`: organização dos módulos, tabelas e fluxos.
- `PRIMEIRO_ACESSO_BLOQUEIO_TOTAL.md`: regra de primeiro acesso.
- `REVISAO_CORRECOES_TRANSACIONAIS_E_LOGIN.md`: compra, saldo negativo e autenticação.
- `AUDITORIA_FINAL.md`: validações e limitações desta revisão.

## Cuidados ao atualizar

1. Não altere uma regra de negócio apenas para adequar o texto de um comentário.
2. Ao mudar uma regra, atualize a documentação funcional e técnica correspondente.
3. Não inclua `.env`, senhas, tokens ou credenciais reais em pacotes compartilhados.
4. Execute os testes automatizados e valide os fluxos no navegador e no MySQL antes de publicar.
