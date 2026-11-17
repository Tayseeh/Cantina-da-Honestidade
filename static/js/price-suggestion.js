/* Sugestão de preço de venda: calcula custo + 50% e aplica o valor no formulário do produto. */
(() => {
  'use strict';

  // Aceita valores digitados no padrão brasileiro e também números com ponto decimal.
  function parsePrice(value) {
    let text = String(value ?? '').trim().replace(/[^\d,.-]/g, '');
    if (!text) return 0;

    const comma = text.lastIndexOf(',');
    const dot = text.lastIndexOf('.');
    if (comma >= 0 && dot >= 0) {
      text = comma > dot
        ? text.replace(/\./g, '').replace(',', '.')
        : text.replace(/,/g, '');
    } else if (comma >= 0) {
      text = text.replace(/\./g, '').replace(',', '.');
    }

    const amount = Number(text);
    return Number.isFinite(amount) && amount > 0 ? amount : 0;
  }

  function brl(value) {
    return value.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // Mantém a busca dos campos restrita ao formulário do botão clicado (novo ou edição).
  function getFields(button) {
    const form = button.closest('form');
    if (!form) return null;
    const cost = form.querySelector('[name="preco_compra"]');
    const sale = form.querySelector('[name="preco_venda"]');
    const message = form.querySelector('[data-price-suggestion]');
    return cost && sale && message ? { form, cost, sale, message, button } : null;
  }

  // Atualiza a mensagem e o estado do botão sempre que o custo é alterado.
  function refresh(fields) {
    const amount = parsePrice(fields.cost.value);
    if (amount <= 0) {
      fields.message.textContent = 'Informe um preço de compra válido para calcular a sugestão (acréscimo padrão de 50%).';
      fields.button.disabled = true;
      fields.button.removeAttribute('data-suggested');
      return null;
    }

    const suggested = Math.round((amount * 1.5 + Number.EPSILON) * 100) / 100;
    fields.message.textContent = `Sugestão: R$ ${brl(suggested)} (custo + 50%). Clique no botão para aplicar ao preço de venda.`;
    fields.button.disabled = false;
    fields.button.dataset.suggested = suggested.toFixed(2);
    return suggested;
  }

  // Delegação: também funciona com formulários que sejam abertos/renderizados depois.
  document.addEventListener('input', event => {
    if (event.target.matches('[name="preco_compra"]')) {
      const form = event.target.closest('form');
      const button = form?.querySelector('[data-apply-suggestion]');
      if (button) {
        const fields = getFields(button);
        if (fields) refresh(fields);
      }
    }
  });

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-apply-suggestion]');
    if (!button) return;

    const fields = getFields(button);
    if (!fields) {
      console.error('[Preço sugerido] Não foi possível localizar os campos de compra/venda no mesmo formulário.');
      return;
    }

    const suggested = refresh(fields);
    if (suggested === null) {
      fields.cost.focus();
      return;
    }

    fields.sale.value = brl(suggested);
    fields.sale.dispatchEvent(new Event('input', { bubbles: true }));
    fields.sale.dispatchEvent(new Event('change', { bubbles: true }));
  });

  document.querySelectorAll('[data-apply-suggestion]').forEach(button => {
    const fields = getFields(button);
    if (fields) refresh(fields);
  });
})();
