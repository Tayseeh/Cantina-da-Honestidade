/* Scripts compartilhados da interface: navegação, formulários, máscaras e interações gerais. */

/* ===== base-01.js ===== */
(() => {
// Anuncia a confirmação a partir de uma região live que já existe no DOM.
      // Não move o foco: isso evita interromper a leitura e reduz anúncios duplicados.
      document.addEventListener('DOMContentLoaded', () => {
        const visibleMessage = document.querySelector('[data-product-added-message] span');
        const liveRegion = document.getElementById('product-added-live-region');
        if (!visibleMessage || !liveRegion) return;
        const message = visibleMessage.textContent.trim();
        window.setTimeout(() => {
          liveRegion.textContent = '';
          window.setTimeout(() => { liveRegion.textContent = message; }, 120);
        }, 180);
      });
})();


/* ===== base-02.js ===== */
(() => {
// Sincroniza formulários e fetch com o token CSRF da sessão atual.
(() => {
  const tokenFromPage = () => document.querySelector('meta[name="csrf-token"]')?.content || '';
  document.querySelectorAll('form').forEach(form => {
    const method = (form.getAttribute('method') || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !form.querySelector('input[name="csrf_token"]')) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'csrf_token';
      input.value = tokenFromPage();
      form.appendChild(input);
    }
  });

  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const options = { ...init };
    const requestMethod = typeof Request !== 'undefined' && input instanceof Request ? input.method : 'GET';
    const method = String(options.method || requestMethod).toUpperCase();
    const inputUrl = typeof input === 'string' ? input : (input && input.url) || window.location.href;
    let sameOrigin = true;
    try { sameOrigin = new URL(inputUrl, window.location.href).origin === window.location.origin; } catch (_) { sameOrigin = false; }
    if (sameOrigin && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const token = tokenFromPage();
      const sourceHeaders = options.headers || (typeof Request !== 'undefined' && input instanceof Request ? input.headers : undefined);
      const headers = new Headers(sourceHeaders || {});
      if (token && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', token);
      options.headers = headers;
    }
    return originalFetch(input, options);
  };
})();
})();


/* ===== catalog-01.js ===== */
(() => {
document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('product-search');
  const clear = document.getElementById('clear-product-search');
  const searchStatus = document.getElementById('product-search-status');
  const empty = document.getElementById('product-search-empty');
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
  function filterSearch() {
    if (!search) return;
    const term = normalize(search.value);
    let count = 0;
    document.querySelectorAll('.product-search-item').forEach(card => { const show = normalize(card.dataset.productSearch).includes(term); card.classList.toggle('d-none', !show); if (show) count++; });
    document.querySelectorAll('[data-category-section]').forEach(section => section.classList.toggle('d-none', !section.querySelector('.product-search-item:not(.d-none)')));
    if (empty) empty.classList.toggle('d-none', count !== 0);
    if (searchStatus) searchStatus.textContent = `${count} produtos encontrados.`;
    if (clear) clear.disabled = !search.value;
  }
  search?.addEventListener('input', filterSearch);
  clear?.addEventListener('click', () => { search.value = ''; filterSearch(); search.focus(); });
  filterSearch();
  const filters = document.querySelectorAll('[data-category-filter]');
  const sections = { snacks: document.querySelector('[data-category-section="snacks"]'), bebidas: document.querySelector('[data-category-section="bebidas"]') };
  filters.forEach(button => button.addEventListener('click', () => {
    filters.forEach(item => item.classList.toggle('active', item === button));
    const selected = button.dataset.categoryFilter;
    Object.entries(sections).forEach(([key, section]) => { if (section) section.classList.toggle('d-none', selected !== 'all' && selected !== key); });
  }));
});
})();


/* ===== catalog-02.js ===== */
(() => {
(() => {
  const modal = document.getElementById('qrScannerModal');
  const status = document.getElementById('qr-reader-status');
  const startButton = document.getElementById('start-qr-reader');
  let scanner = null;
  let processing = false;
  async function stopScanner() {
    if (scanner && scanner.isScanning) {
      try { await scanner.stop(); } catch (_) {}
    }
  }
  function productIdFromQr(value) {
    const raw = String(value || '').trim();
    if (/^\d+$/.test(raw)) return raw;
    try {
      const parsed = new URL(raw, window.location.origin);
      if (parsed.origin !== window.location.origin) return null;
      const match = parsed.pathname.match(/^\/qr\/(\d+)\/?$/);
      return match ? match[1] : null;
    } catch (_) { return null; }
  }
  async function startScanner() {
    if (!window.Html5Qrcode) {
      status.textContent = 'Não foi possível carregar o leitor de QR Code. Verifique sua conexão e tente novamente.';
      return;
    }
    startButton.disabled = true;
    status.textContent = 'Solicitando acesso à câmera…';
    try {
      if (!scanner) scanner = new Html5Qrcode('qr-reader');
      await scanner.start({ facingMode: 'environment' }, { fps: 10, qrbox: { width: 230, height: 230 } }, async decodedText => {
        if (processing) return;
        const productId = productIdFromQr(decodedText);
        if (!productId) {
          status.textContent = 'Este QR Code não parece ser de um produto do Confia+. Tente outro.';
          return;
        }
        processing = true;
        status.textContent = 'QR Code lido! Adicionando produto ao carrinho…';
        await stopScanner();
        try {
          const response = await fetch(`/carrinho/adicionar/${productId}`, {method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content}});
          const data = await response.json();
          if (!response.ok) { status.textContent = data.error || 'Não foi possível adicionar o produto.'; processing = false; return; }
          upsertCartItem(null, data);
          updateCartSummary(data);
          const announcement = document.getElementById('cart-announcement');
          if (announcement) { announcement.textContent = ''; window.setTimeout(() => { announcement.textContent = `${data.nome} adicionado ao carrinho. Quantidade deste produto: ${data.quantidade_produto}. Total de unidades no carrinho: ${data.itens}.`; }, 120); }
          status.textContent = `${data.nome} adicionado ao carrinho. Quantidade deste produto: ${data.quantidade_produto}.`;
          processing = false;
        } catch (_) {
          status.textContent = 'Não foi possível adicionar o produto. Verifique sua conexão e tente novamente.';
          processing = false;
        }
      }, () => {});
      status.textContent = 'Câmera ativa. Aponte para o QR Code do produto.';
    } catch (error) {
      status.textContent = 'Não foi possível abrir a câmera. Confira a permissão do navegador e use HTTPS ou localhost.';
      startButton.disabled = false;
    }
  }
  startButton.addEventListener('click', startScanner);
  modal.addEventListener('hidden.bs.modal', async () => {
    await stopScanner();
    processing = false;
    startButton.disabled = false;
    status.textContent = 'Ao iniciar, permita o acesso à câmera.';
  });
  if (new URLSearchParams(window.location.search).get('scanner') === '1') {
    bootstrap.Modal.getOrCreateInstance(modal).show();
    modal.addEventListener('shown.bs.modal', startScanner, { once: true });
  }
})();
})();


/* ===== catalog-03.js ===== */
(() => {
(() => {
  const pin = document.getElementById("pin-compra");
  const modalForm = document.querySelector("#confirmPurchase form");
  const errorBox = document.getElementById("pin-error-modal");
  const submitButton = document.getElementById("confirm-purchase-button");

  if (pin) {
    pin.addEventListener("input", () => {
      pin.value = pin.value.replace(/\D/g, "").slice(0, 4);
      if (errorBox) {
        errorBox.classList.add("d-none");
        errorBox.textContent = "";
      }
    });
  }

  if (!modalForm) return;
  modalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!modalForm.reportValidity()) return;

    if (errorBox) {
      errorBox.classList.add("d-none");
      errorBox.textContent = "";
    }
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Processando...";
    }

    try {
      const response = await fetch(modalForm.action, {
        method: "POST",
        body: new FormData(modalForm),
        headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" },
        credentials: "same-origin",
      });

      let data = {};
      try { data = await response.json(); } catch (_) {}

      if (response.redirected) {
        // Compatibility for older server responses: replace current page instead of
        // adding a redirect entry that can return to a stale checkout state.
        window.location.replace(data.redirect || response.url);
        return;
      }

      if (!response.ok) {
        if (errorBox) {
          errorBox.textContent = data.error || "PIN incorreto. Confira os 4 números e tente novamente.";
          errorBox.classList.remove("d-none");
        }
        pin?.focus();
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = "Confirmar compra";
        }
        return;
      }

      if (data.redirect) {
        window.location.replace(data.redirect);
        return;
      }

      if (errorBox) {
        errorBox.textContent = "A compra foi processada, mas não recebemos a confirmação de navegação. Acesse Meus pedidos para conferir.";
        errorBox.classList.remove("d-none");
      }
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = "Confirmar compra";
      }
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = "Não foi possível finalizar a compra. Tente novamente.";
        errorBox.classList.remove("d-none");
      }
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = "Confirmar compra";
      }
    }
  }, true);
})();
})();


/* ===== first_access-01.js ===== */
(() => {
(() => {
  ["pin", "confirmar-pin"].forEach((id) => {
    const field = document.getElementById(id);
    if (field) field.addEventListener("input", () => {
      field.value = field.value.replace(/\D/g, "").slice(0, 4);
    });
  });
})();
})();


/* ===== history-01.js ===== */
(() => {
document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.getElementById('orders-date');
  const clearButton = document.getElementById('clear-orders-date');
  const feedback = document.getElementById('orders-filter-feedback');
  const cards = [...document.querySelectorAll('#orders-list .order-mobile-card')];
  const noResults = document.getElementById('orders-no-date-results');
  if (!dateInput || !clearButton || !feedback || !noResults) return;

  function filterOrders() {
    const selectedDate = dateInput.value;
    let visible = 0;
    cards.forEach(card => {
      const matches = !selectedDate || card.dataset.orderDate === selectedDate;
      card.classList.toggle('d-none', !matches);
      if (matches) visible += 1;
    });
    noResults.classList.toggle('d-none', !selectedDate || visible > 0);
    clearButton.disabled = !selectedDate;
    feedback.textContent = selectedDate
      ? `${visible} compra(s) encontrada(s).`
      : cards.length ? `${cards.length} compra(s) no histórico.` : '';
  }

  dateInput.addEventListener('change', filterOrders);
  clearButton.addEventListener('click', () => {
    dateInput.value = '';
    filterOrders();
  });
  filterOrders();
});
})();


/* ===== home-01.js ===== */
(() => {
(() => {
  const modal = document.getElementById('homeQrScannerModal');
  if (!modal) return;
  const status = document.getElementById('home-qr-status');
  const openButton = document.querySelector('[data-bs-target="#homeQrScannerModal"]');
  const startButton = document.getElementById('home-start-qr');
  let scanner = null, processing = false;
  async function stopScanner() { if (scanner && scanner.isScanning) { try { await scanner.stop(); } catch (_) {} } }
  function productIdFromQr(value) {
    const raw = String(value || '').trim();
    if (/^\d+$/.test(raw)) return raw;
    try { const parsed = new URL(raw, window.location.origin); if (parsed.origin !== window.location.origin) return null; const match = parsed.pathname.match(/^\/qr\/(\d+)\/?$/); return match ? match[1] : null; } catch (_) { return null; }
  }
  async function startScanner() {
    if (!window.Html5Qrcode) { status.textContent = 'Não foi possível carregar o leitor. Verifique sua conexão e tente novamente.'; startButton.disabled = false; return; }
    startButton.disabled = true; status.textContent = 'Solicitando acesso à câmera…';
    try {
      if (!scanner) scanner = new Html5Qrcode('home-qr-reader');
      await scanner.start({ facingMode: 'environment' }, { fps: 10, qrbox: { width: 230, height: 230 } }, async decodedText => {
        if (processing) return;
        const productId = productIdFromQr(decodedText);
        if (!productId) { status.textContent = 'Este QR Code não identifica um produto do Confia+. Tente outro.'; return; }
        processing = true; status.textContent = 'QR Code lido! Adicionando ao carrinho…'; await stopScanner();
        window.location.href = `/qr/${productId}?next=${encodeURIComponent('/cardapio')}`;
      }, () => {});
      status.textContent = 'Câmera ativa. Aponte para o QR Code do produto.';
    } catch (_) { status.textContent = 'Não foi possível abrir a câmera. Confira a permissão e use HTTPS ou localhost.'; startButton.disabled = false; }
  }
  startButton.addEventListener('click', startScanner);
  modal.addEventListener('shown.bs.modal', startScanner);
  modal.addEventListener('shown.bs.modal', () => { startButton.focus(); });
  modal.addEventListener('hidden.bs.modal', async () => { await stopScanner(); processing = false; startButton.disabled = false; status.textContent = 'Preparando leitor de QR Code…'; if (openButton) openButton.focus(); });
})();
})();


/* ===== products-01.js ===== */
(() => {
const productSearch = document.querySelector('#buscar-produto');
const productFilter = document.querySelector('#filtro-produtos');
const productCards = [...document.querySelectorAll('[data-product-card]')];
const searchCount = document.querySelector('#product-search-count');
const searchEmpty = document.querySelector('#product-search-empty');
function filterProducts() {
  const term = productSearch.value.trim().toLocaleLowerCase('pt-BR');
  const filter = productFilter.value;
  let visible = 0;
  productCards.forEach(card => {
    const matchesText = card.dataset.searchText.toLocaleLowerCase('pt-BR').includes(term);
    const stock = Number(card.dataset.stock || 0);
    const lowStockLimit = Number(card.dataset.lowStock || 5);
    const active = card.dataset.status === 'ativo';
    const matchesFilter =
      (filter === 'todos' && active) ||
      (filter === 'disponiveis' && active && stock > lowStockLimit) ||
      (filter === 'baixo' && active && stock > 0 && stock <= lowStockLimit) ||
      (filter === 'sem_estoque' && active && stock <= 0) ||
      (filter === 'inativo' && !active);
    const matches = matchesText && matchesFilter;
    card.classList.toggle('d-none', !matches);
    if (card.nextElementSibling?.classList.contains('product-edit-row')) card.nextElementSibling.classList.toggle('d-none', !matches);
    if (!matches) card.querySelector('.collapse.show')?.classList.remove('show');
    if (matches) visible++;
  });
  searchEmpty.classList.toggle('d-none', visible > 0 || productCards.length === 0);
  searchCount.textContent = `${visible} de ${productCards.length} produto(s)`;
}
productSearch.addEventListener('input', filterProducts);
productFilter.addEventListener('change', filterProducts);
document.querySelectorAll('[data-product-filter]').forEach(button => {
  button.addEventListener('click', () => {
    productFilter.value = button.dataset.productFilter;
    document.querySelectorAll('[data-product-filter]').forEach(item => {
      const selected = item === button;
      item.classList.toggle('active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    filterProducts();
  });
});
document.querySelectorAll('[data-product-name]').forEach(input => input.addEventListener('input', () => {
  input.value = input.value.replace(/[^\p{L}\p{N}\s.,'’()\/&+-]/gu, '').replace(/^[^\p{L}\p{N}]+/u, '').slice(0, 80);
}));
document.querySelectorAll('[data-product-description]').forEach(input => input.addEventListener('input', () => {
  input.value = input.value.replace(/[^\p{L}\p{N}\s.,;:!?()'’"\-_/&+%#@]/gu, '').slice(0, 250);
}));
document.querySelectorAll('[data-stock]').forEach(input => input.addEventListener('input', () => {
  input.value = input.value.replace(/\D/g, '').slice(0, 6);
}));
document.querySelectorAll('[data-money]').forEach(input => input.addEventListener('input', () => {
  let value = input.value.replace(/[^\d.,]/g, '').replace('.', ',');
  const [integer = '', ...decimalParts] = value.split(',');
  input.value = integer.slice(0, 9) + (value.includes(',') ? ',' + decimalParts.join('').slice(0, 2) : '');
}));
document.querySelectorAll('[data-remove-photo]').forEach(button => button.addEventListener('click', () => {
  button.closest('form').querySelector('[data-product-photo]').value = '';
}));
})();


/* ===== profile-01.js ===== */
(() => {
document.querySelectorAll('[data-profile-open]').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    const targetId = link.dataset.profileOpen;
    const target = document.getElementById(targetId);
    const section = document.querySelector('.profile-security-existing');
    if (!target || !section) return;
    section.classList.add('profile-security-open');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (window.bootstrap?.Collapse) window.bootstrap.Collapse.getOrCreateInstance(target).show();
  });
});
})();


/* ===== profile-02.js ===== */
(() => {
const passwordForm = document.getElementById('alterar-senha-form');
  if (passwordForm) {
    const passwordInput = document.getElementById('senha-nova');
    const passwordConfirmation = document.getElementById('confirmar-senha');
    const passwordFeedback = document.getElementById('senha-confirmacao-feedback');
    const validatePasswordPair = () => {
      let error = '';
      if (passwordInput.value && (passwordInput.value.length < 8 || passwordInput.value.length > 20 || !/\p{L}/u.test(passwordInput.value) || !/\d/.test(passwordInput.value))) {
        error = 'Use de 8 a 20 caracteres, incluindo uma letra e um número.';
      } else if (passwordConfirmation.value && passwordInput.value !== passwordConfirmation.value) {
        error = 'As senhas não coincidem.';
      }
      passwordConfirmation.setCustomValidity(passwordConfirmation.value && passwordInput.value !== passwordConfirmation.value ? 'As senhas não coincidem.' : '');
      passwordInput.setCustomValidity(passwordInput.value && (passwordInput.value.length < 8 || passwordInput.value.length > 20 || !/\p{L}/u.test(passwordInput.value) || !/\d/.test(passwordInput.value)) ? 'Use de 8 a 20 caracteres, incluindo uma letra e um número.' : '');
      passwordFeedback.textContent = error;
      return !error && Boolean(passwordInput.value) && Boolean(passwordConfirmation.value);
    };
    passwordInput.addEventListener('input', validatePasswordPair);
    passwordConfirmation.addEventListener('input', validatePasswordPair);
    passwordForm.addEventListener('submit', (event) => {
      if (!validatePasswordPair()) {
        event.preventDefault();
        passwordConfirmation.reportValidity();
        if (!passwordInput.checkValidity()) passwordInput.reportValidity();
      }
    });
  }

  const pinForm = document.getElementById('alterar-pin-form');
  if (pinForm) {
    const pinInput = document.getElementById('pin-novo');
    const pinConfirmation = document.getElementById('confirmar-pin');
    const pinFeedback = document.getElementById('pin-confirmacao-feedback');
    const validatePinPair = () => {
      pinInput.value = pinInput.value.replace(/\D/g, '').slice(0, 4);
      pinConfirmation.value = pinConfirmation.value.replace(/\D/g, '').slice(0, 4);
      const mismatch = pinConfirmation.value && pinInput.value !== pinConfirmation.value;
      pinConfirmation.setCustomValidity(mismatch ? 'Os PINs não coincidem.' : '');
      pinFeedback.textContent = mismatch ? 'Os PINs não coincidem.' : '';
      return /^[0-9]{4}$/.test(pinInput.value) && /^[0-9]{4}$/.test(pinConfirmation.value) && !mismatch;
    };
    pinInput.addEventListener('input', validatePinPair);
    pinConfirmation.addEventListener('input', validatePinPair);
    pinForm.addEventListener('submit', (event) => {
      if (!validatePinPair()) {
        event.preventDefault();
        (pinConfirmation.value && pinInput.value !== pinConfirmation.value ? pinConfirmation : pinInput).reportValidity();
      }
    });
  }
})();


/* ===== profile-03.js ===== */
(() => {
(() => {
  const pinFields = document.querySelectorAll(
    '#pin-novo-mobile, #confirmar-pin-mobile, #pin-novo, #confirmar-pin'
  );
  pinFields.forEach((field) => {
    field.setAttribute('inputmode', 'numeric');
    field.setAttribute('maxlength', '4');
    field.setAttribute('pattern', '[0-9]{4}');
    field.addEventListener('input', () => {
      field.value = field.value.replace(/\D/g, '').slice(0, 4);
      field.setCustomValidity('');
    });
    field.addEventListener('paste', (event) => {
      event.preventDefault();
      const pasted = (event.clipboardData || window.clipboardData).getData('text');
      const digits = pasted.replace(/\D/g, '').slice(0, 4);
      const start = field.selectionStart ?? field.value.length;
      const end = field.selectionEnd ?? field.value.length;
      field.setRangeText(digits, start, end, 'end');
      field.dispatchEvent(new Event('input', { bubbles: true }));
    });
  });
})();
})();



/* ===== users-01.js ===== */
(() => {
const userSearch = document.getElementById('busca-usuarios');
  const roleFilter = document.getElementById('filtro-perfil');
  const statusFilter = document.getElementById('filtro-status');
  const generalFilter = document.getElementById('filtro-geral-usuarios');
  if (generalFilter) { generalFilter.addEventListener('change', () => { roleFilter.value = ['admin', 'operador'].includes(generalFilter.value) ? generalFilter.value : 'todos'; statusFilter.value = ['ativo', 'inativo'].includes(generalFilter.value) ? generalFilter.value : 'todos'; filterUsers(); }); }
  const visibleCount = document.getElementById('usuarios-visiveis');
  const emptyResults = document.getElementById('usuarios-vazio');
  function filterUsers() {
    const term = userSearch.value.trim().toLocaleLowerCase('pt-BR');
    const selectedRole = roleFilter.value;
    const selectedStatus = statusFilter.value;
    let totalVisible = 0;
    document.querySelectorAll('.usuario-linha').forEach((row) => {
      const match = row.dataset.busca.toLocaleLowerCase('pt-BR').includes(term) && (selectedRole === 'todos' || row.dataset.perfil === selectedRole) && (selectedStatus === 'todos' || row.dataset.status === selectedStatus);
      row.classList.toggle('d-none', !match);
      document.querySelectorAll(`[data-parent-user="${row.dataset.id}"]`).forEach((detail) => { if (!match) detail.classList.remove('show'); detail.classList.toggle('d-none', !match); });
      if (match) totalVisible++;
    });
    visibleCount.textContent = `${totalVisible} usuário(s)`;
    emptyResults.classList.toggle('d-none', totalVisible > 0);
  }
  userSearch.addEventListener('input', filterUsers);
  if (!generalFilter) { roleFilter.addEventListener('change', filterUsers); statusFilter.addEventListener('change', filterUsers); }
  const userDdds = new Set('11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99'.split(' '));
  function filterToDigits(input, max, mask) {
    input.addEventListener('beforeinput', event => {
      if (event.inputType.startsWith('insert') && event.data && /\D/.test(event.data)) event.preventDefault();
    });
    input.addEventListener('input', () => { input.value = mask(input.value.replace(/\D/g, '').slice(0, max)); });
    input.value = mask(input.value.replace(/\D/g, '').slice(0, max));
  }
  function formatUserEnrollment(digits) {
    return digits;
  }
  function formatUserCpf(digits) {
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
    if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
  }
  function formatUserPhone(digits) {
    if (digits.length <= 2) return digits ? `(${digits}` : '';
    const subscriber = digits.slice(2);
    const prefix = digits.length > 10 ? 5 : 4;
    const number = subscriber.length > prefix ? `${subscriber.slice(0, prefix)}-${subscriber.slice(prefix)}` : subscriber;
    return `(${digits.slice(0, 2)}) ${number}`;
  }
  function formatUserBirth(digits) {
    if (digits.length <= 2) return digits;
    if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
    return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
  }
  function validateUserField(input) {
    const value = input.value.trim();
    const type = input.dataset.userValidation;
    let message = '';
    if (type === 'nome' || type === 'sobrenome') {
      if (!value || value.length > 30 || !/^\p{L}+(?:[ '-]\p{L}+)*$/u.test(value)) message = 'Use apenas letras, espaços, hífen ou apóstrofo (até 30 caracteres).';
    } else if (type === 'email') {
      if (value.length > 50 || !/^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$/i.test(value)) message = 'Digite um e-mail válido com até 50 caracteres.';
    } else if (type === 'matricula') {
      if (!/^\d{1,14}$/.test(value)) message = 'Informe de 1 a 14 números, sem espaços ou caracteres especiais.';
    } else if (type === 'cpf' && value) {
      if (value.replace(/\D/g, '').length !== 11) message = 'Digite os 11 números do CPF.';
    } else if (type === 'telefone' && value) {
      if (!/^[\d\s()+.-]+$/.test(value)) message = 'Use somente números; a formatação é aplicada automaticamente.';
      else {
        const digits = value.replace(/\D/g, '');
        const subscriber = digits.slice(2);
        const validNumber = (subscriber.length === 9 && subscriber.startsWith('9')) || (subscriber.length === 8 && '2345'.includes(subscriber[0]));
        if (![10, 11].includes(digits.length)) message = 'Informe o DDD e o número completo.';
        else if (!userDdds.has(digits.slice(0, 2))) message = 'O DDD informado não é válido no Brasil.';
        else if (!validNumber) message = 'Confira o número do telefone.';
      }
    } else if (type === 'nascimento' && value) {
      const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (!match) message = 'Digite uma data válida no formato dd/mm/aaaa.';
      else {
        const [, dayText, monthText, yearText] = match;
        const day = Number(dayText), month = Number(monthText), year = Number(yearText);
        const parsed = new Date(Date.UTC(year, month - 1, day));
        const iso = `${yearText}-${monthText}-${dayText}`;
        if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day || iso > input.dataset.max || iso < input.dataset.min) message = 'Digite uma data válida.';
      }
    }
    input.classList.toggle('is-invalid', Boolean(message));
    input.setAttribute('aria-invalid', message ? 'true' : 'false');
    input.setAttribute('aria-describedby', `feedback-${type}-${input.closest('.user-edit-form').querySelector('[name="id"]').value}`);
    const userId = input.closest('.user-edit-form').querySelector('[name="id"]').value;
    document.getElementById(`feedback-${type}-${userId}`).textContent = message;
    return !message;
  }
  document.querySelectorAll('.user-edit-form').forEach(form => {
    form.querySelectorAll('[data-user-validation]').forEach(input => {
      const type = input.dataset.userValidation;
      if (type === 'matricula') filterToDigits(input, 14, formatUserEnrollment);
      if (type === 'cpf') filterToDigits(input, 11, formatUserCpf);
      if (type === 'telefone') filterToDigits(input, 11, formatUserPhone);
      if (type === 'nascimento') {
        const initial = input.value;
        input.value = /^\d{4}-\d{2}-\d{2}$/.test(initial) ? `${initial.slice(8, 10)}/${initial.slice(5, 7)}/${initial.slice(0, 4)}` : formatUserBirth(initial.replace(/\D/g, '').slice(0, 8));
        filterToDigits(input, 8, formatUserBirth);
      }
      if (type === 'nome' || type === 'sobrenome') {
        input.addEventListener('beforeinput', event => { if (event.inputType.startsWith('insert') && event.data && /[^\p{L} '-]/u.test(event.data)) event.preventDefault(); });
        input.addEventListener('input', () => { input.value = input.value.replace(/[^\p{L} '-]/gu, '').slice(0, 30); });
      }
      if (type === 'email') {
        const allowedEmailChars = /[A-Za-z0-9.!#$%&'*+/=?^_`{|}~@-]/;
        input.addEventListener('beforeinput', event => { if (event.inputType.startsWith('insert') && event.data && [...event.data].some(character => !allowedEmailChars.test(character))) event.preventDefault(); });
        input.addEventListener('input', () => { input.value = input.value.replace(/[^A-Za-z0-9.!#$%&'*+/=?^_`{|}~@-]/g, '').slice(0, 50); });
      }
      input.addEventListener('blur', () => validateUserField(input));
      input.addEventListener('input', () => { if (input.classList.contains('is-invalid')) validateUserField(input); });
    });
    form.addEventListener('submit', event => {
      const invalid = [...form.querySelectorAll('[data-user-validation]')].find(input => !validateUserField(input));
      if (invalid) { event.preventDefault(); invalid.focus(); }
    });
  });
})();
