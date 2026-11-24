(() => {
  'use strict';

  const normalize = (value) => String(value ?? '')
    .toLocaleLowerCase('pt-BR')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim();

  const parseNumber = (value, fallback = 0) => {
    const parsed = Number.parseInt(String(value ?? '').trim(), 10);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  function initProductFilters() {
    const search = document.getElementById('buscar-produto');
    const select = document.getElementById('filtro-produtos');
    const list = document.getElementById('product-list');
    if (!list || (!search && !select)) return;

    const rows = Array.from(list.querySelectorAll('tr[data-product-card]'));
    const count = document.getElementById('product-search-count');
    const emptyRow = document.getElementById('product-filter-empty-row');
    const clearButton = document.getElementById('product-filter-clear');

    function applyFilters() {
      const term = normalize(search?.value);
      const status = select?.value || 'todos';
      let visible = 0;

      rows.forEach((row) => {
        const stock = parseNumber(row.dataset.stock, 0);
        const lowLimit = Math.max(0, parseNumber(row.dataset.lowStock, 5));
        const isActive = normalize(row.dataset.status) === 'ativo';
        const searchable = normalize(
          row.dataset.searchText || row.textContent
        );

        const matchesSearch = !term || searchable.includes(term);
        let matchesStatus = true;

        switch (status) {
          case 'disponiveis':
            matchesStatus = isActive && stock > lowLimit;
            break;
          case 'baixo':
            matchesStatus = isActive && stock > 0 && stock <= lowLimit;
            break;
          case 'sem_estoque':
            matchesStatus = isActive && stock <= 0;
            break;
          case 'inativo':
            matchesStatus = !isActive;
            break;
          case 'todos':
          default:
            matchesStatus = true;
        }

        const show = matchesSearch && matchesStatus;
        // Inline !important wins over the mobile CSS grid display rule.
        if (show) {
          row.classList.remove('d-none');
          row.style.removeProperty('display');
        } else {
          row.classList.add('d-none');
          row.style.setProperty('display', 'none', 'important');
        }

        // Also hide any legacy detail row immediately following this product.
        const detailRow = row.nextElementSibling;
        if (detailRow?.classList.contains('product-edit-row') && !show) {
          detailRow.classList.add('d-none');
          detailRow.style.setProperty('display', 'none', 'important');
        }

        if (show) visible += 1;
      });

      const total = rows.length;
      if (count) count.textContent = `${visible} de ${total} produto(s)`;

      const noResults = total > 0 && visible === 0;
      if (emptyRow) {
        emptyRow.classList.toggle('d-none', !noResults);
        if (noResults) {
          emptyRow.style.removeProperty('display');
        } else {
          emptyRow.style.setProperty('display', 'none', 'important');
        }
      }

      document.querySelectorAll('[data-product-filter]').forEach((button) => {
        const selected = button.dataset.productFilter === status;
        button.classList.toggle('active', selected);
        button.setAttribute('aria-pressed', String(selected));
      });
    }

    // Native event listeners attached directly to the controls.
    search?.addEventListener('input', applyFilters);
    select?.addEventListener('change', applyFilters);
    document.querySelectorAll('[data-product-filter]').forEach((button) => {
      button.addEventListener('click', () => {
        if (select) select.value = button.dataset.productFilter || 'todos';
        applyFilters();
      });
    });

    clearButton?.addEventListener('click', () => {
      if (search) search.value = '';
      if (select) select.value = 'todos';
      applyFilters();
    });

    applyFilters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProductFilters, { once: true });
  } else {
    initProductFilters();
  }
})();
