/* Ordenação das tabelas pelo cabeçalho, respeitando o conteúdo de cada coluna. */
(() => {
  'use strict';

  const pairedRowSelectors = [
    '.customer-row',
    '.product-table-row',
    '.usuario-linha'
  ];

  // Algumas linhas de edição pertencem ao registro anterior e devem se mover junto dele.
  function getMainRows(tbody) {
    const rows = Array.from(tbody.rows);
    const result = [];
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      if (!pairedRowSelectors.some(selector => row.matches(selector))) continue;
      const pair = [row];
      const next = rows[i + 1];
      if (next && (
        next.classList.contains('customer-edit-row') ||
        next.classList.contains('product-edit-row') ||
        next.classList.contains('users-expanded-row')
      )) {
        pair.push(next);
        i++;
      }
      result.push(pair);
    }
    return result;
  }

  function cellText(row, index) {
    const cell = row.cells[index];
    if (!cell) return '';
    return (cell.innerText || cell.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function parseNumber(value) {
    const cleaned = value.replace(/[^\d,.-]/g, '').trim();
    if (!cleaned) return NaN;
    if (cleaned.includes(',') && cleaned.includes('.')) {
      return Number(cleaned.lastIndexOf(',') > cleaned.lastIndexOf('.')
        ? cleaned.replace(/\./g, '').replace(',', '.')
        : cleaned.replace(/,/g, ''));
    }
    return Number(cleaned.replace(',', '.'));
  }

  // Interpreta valores monetários, saldos, matrículas e datas antes de comparar textos.
  function sortValue(text, heading) {
    const label = heading.toLocaleLowerCase('pt-BR');
    if (/saldo|preço|valor|estoque|matrícula/.test(label)) {
      const number = parseNumber(text);
      if (Number.isFinite(number)) return { type: 'number', value: number };
    }
    if (/data|nascimento|cadastro/.test(label)) {
      const brDate = text.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (brDate) return { type: 'number', value: Number(`${brDate[3]}${brDate[2]}${brDate[1]}`) };
    }
    return { type: 'text', value: text.toLocaleLowerCase('pt-BR') };
  }

  function compareRows(a, b, index, heading, direction) {
    const left = sortValue(cellText(a[0], index), heading);
    const right = sortValue(cellText(b[0], index), heading);
    let comparison = 0;
    if (left.type === 'number' && right.type === 'number') {
      comparison = left.value - right.value;
    } else {
      comparison = String(left.value).localeCompare(String(right.value), 'pt-BR', {
        numeric: true,
        sensitivity: 'base'
      });
    }
    return comparison * direction;
  }

  // Habilita ordenação por clique e teclado nos cabeçalhos marcados como ordenáveis.
  function setupTable(table) {
    const tbody = table.tBodies[0];
    if (!tbody) return;

    table.querySelectorAll('thead th[data-sortable]').forEach((th, index) => {
      th.classList.add('is-sortable');
      th.tabIndex = 0;
      th.setAttribute('role', 'button');
      th.setAttribute('aria-label', `${th.textContent.trim()}. Clique para ordenar.`);
      th.setAttribute('aria-sort', 'none');

      const sort = () => {
        const current = th.dataset.sortDirection;
        const direction = current === 'asc' ? -1 : 1;
        table.querySelectorAll('thead th[data-sortable]').forEach(other => {
          other.dataset.sortDirection = '';
          other.setAttribute('aria-sort', 'none');
          other.classList.remove('sort-ascending', 'sort-descending');
        });
        th.dataset.sortDirection = direction === 1 ? 'asc' : 'desc';
        th.setAttribute('aria-sort', direction === 1 ? 'ascending' : 'descending');
        th.classList.add(direction === 1 ? 'sort-ascending' : 'sort-descending');

        const groups = getMainRows(tbody);
        groups.sort((a, b) => compareRows(a, b, index, th.textContent.trim(), direction));
        const fragment = document.createDocumentFragment();
        groups.forEach(group => group.forEach(row => fragment.appendChild(row)));
        // Preserve any non-data rows (e.g. empty-state messages) after the sorted records.
        Array.from(tbody.rows).filter(row =>
          !pairedRowSelectors.some(selector => row.matches(selector)) &&
          !row.classList.contains('customer-edit-row') &&
          !row.classList.contains('product-edit-row') &&
          !row.classList.contains('users-expanded-row')
        ).forEach(row => fragment.appendChild(row));
        tbody.appendChild(fragment);
      };

      th.addEventListener('click', sort);
      th.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          sort();
        }
      });
    });
  }

  document.querySelectorAll(
    '.customers-table, .products-table, .users-table'
  ).forEach(setupTable);
})();