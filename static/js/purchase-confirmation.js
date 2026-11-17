/* Comportamento da confirmação visual de compra concluída para desktop e dispositivos móveis. */
(() => {
  'use strict';
  // O modal só é aberto quando o servidor sinaliza que a compra foi concluída.
  const showPurchaseConfirmation = () => {
    const el = document.querySelector('[data-purchase-confirmation="true"]');
    if (!el || !window.bootstrap?.Modal) return;
    window.bootstrap.Modal.getOrCreateInstance(el, {
      backdrop: 'static', keyboard: true, focus: true
    }).show();
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showPurchaseConfirmation, { once: true });
  } else {
    showPurchaseConfirmation();
  }
})();
