/* Busca incremental e seleção de clientes no formulário de recarga. */
(() => {
  'use strict';

  const init = () => {
    const search = document.getElementById('buscar-cliente-recarga');
    const list = document.getElementById('lista-clientes-recarga');
    const selectedBox = document.getElementById('cliente-selecionado');
    const hiddenEnrollment = document.getElementById('matricula-recarga');
    const amount = document.getElementById('valor-recarga');
    const confirmButton = document.getElementById('confirmar-recarga');
    const hint = document.getElementById('dica-busca-cliente');
    const noCustomers = document.getElementById('sem-clientes-recarga');
    const noResults = document.getElementById('sem-resultados-clientes');
    if (!search || !list) return;

    let selectedRow = null;
    const rows = Array.from(list.querySelectorAll('button.cliente-recarga'));

    const digits = value => String(value || '').replace(/\D/g, '');
    const enrollmentText = value => {
      const valueDigits = digits(value).slice(0, 14);
      if (!valueDigits) return '—';
      if (valueDigits.length === 14) {
        return `${valueDigits.slice(0, 4)} ${valueDigits.slice(4, 8)} ${valueDigits.slice(8, 13)} ${valueDigits.slice(13)}`;
      }
      return valueDigits;
    };

    rows.forEach(row => {
      const label = row.querySelector('.matricula-cliente-recarga');
      if (label) label.textContent = `Matrícula: ${enrollmentText(row.dataset.matricula)}`;
    });

    // A busca considera nome e somente os dígitos da matrícula, sem exigir máscara.
    const filter = () => {
      const query = search.value.trim().toLocaleLowerCase('pt-BR');
      const queryDigits = digits(query);
      let matches = 0;

      rows.forEach(row => {
        const name = (row.dataset.nome || '').toLocaleLowerCase('pt-BR');
        const enrollment = digits(row.dataset.matricula);
        const found = query.length > 0 &&
          (name.includes(query) || (queryDigits.length > 0 && enrollment.includes(queryDigits)));
        row.classList.toggle('d-none', !found);
        if (found) matches += 1;
      });

      list.classList.toggle('d-none', query.length === 0 || matches === 0);
      if (hint) hint.classList.toggle('d-none', query.length > 0);
      if (noCustomers) noCustomers.classList.toggle('d-none', rows.length > 0 || query.length > 0);
      if (noResults) noResults.classList.toggle('d-none', query.length === 0 || matches > 0 || rows.length === 0);
    };

    search.addEventListener('input', filter);
    search.addEventListener('search', filter);

    // A seleção guarda a matrícula no campo oculto usado pelo formulário de recarga.
    list.addEventListener('click', event => {
      const target = event.target instanceof Element ? event.target : event.target.parentElement;
      const row = target && target.closest('button.cliente-recarga');
      if (!row || !list.contains(row) || row.classList.contains('d-none')) return;

      selectedRow = row;
      if (hiddenEnrollment) hiddenEnrollment.value = row.dataset.matricula || '';
      rows.forEach(item => item.classList.toggle('active', item === row));

      if (selectedBox) {
        const icon = document.createElement('i');
        icon.className = 'bi bi-person-check-fill';
        const details = document.createElement('span');
        const name = document.createElement('strong');
        name.textContent = row.dataset.nome || 'Cliente';
        const enrollment = document.createElement('small');
        enrollment.textContent = `Matrícula ${enrollmentText(row.dataset.matricula)}`;
        details.append(name, enrollment);
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'btn btn-sm btn-outline-secondary ms-auto';
        removeButton.id = 'remover-cliente-recarga';
        removeButton.setAttribute('aria-label', 'Remover cliente selecionado');
        removeButton.title = 'Remover cliente';
        const removeIcon = document.createElement('i');
        removeIcon.className = 'bi bi-x-lg';
        removeButton.append(removeIcon);
        selectedBox.replaceChildren(icon, details, removeButton);
      }

      list.classList.add('d-none');
      if (hint) hint.classList.add('d-none');
      if (confirmButton) confirmButton.disabled = false;
      if (amount) amount.focus();
    });

    // Remover a seleção limpa o campo oculto e impede o envio sem cliente escolhido.
    selectedBox?.addEventListener('click', event => {
      const target = event.target instanceof Element ? event.target : event.target.parentElement;
      if (!target?.closest('#remover-cliente-recarga')) return;
      selectedRow = null;
      if (hiddenEnrollment) hiddenEnrollment.value = '';
      if (confirmButton) confirmButton.disabled = true;
      if (selectedBox) {
        const icon = document.createElement('i');
        icon.className = 'bi bi-person-check';
        const message = document.createElement('span');
        message.textContent = 'Nenhum cliente selecionado.';
        selectedBox.replaceChildren(icon, message);
      }
      search.value = '';
      rows.forEach(row => row.classList.remove('active'));
      list.classList.add('d-none');
      if (hint) hint.classList.remove('d-none');
      if (amount) amount.value = '';
      search.focus();
    });



    // Abre a confirmação antes de enviar a recarga ao servidor.
    const form = document.getElementById('form-recarga');
    const openConfirmation = () => {
      if (!hiddenEnrollment?.value) {
        alert('Selecione um cliente antes de realizar a recarga.');
        search.focus();
        return;
      }
      const rawAmount = String(amount?.value || '').trim();
      const normalized = rawAmount.replace(/[^\d,.-]/g, '').replace(/\./g, '').replace(',', '.');
      const numericAmount = Number(normalized);
      if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
        alert('Informe um valor de recarga maior que zero.');
        amount?.focus();
        return;
      }

      const customerName = selectedRow?.dataset.nome || 'Cliente';
      const enrollmentValue = enrollmentText(hiddenEnrollment.value);
      const formattedAmount = numericAmount.toLocaleString('pt-BR', {
        style: 'currency', currency: 'BRL'
      });
      const nameTarget = document.getElementById('confirmacao-cliente');
      const enrollmentTarget = document.getElementById('confirmacao-matricula');
      const amountTarget = document.getElementById('confirmacao-valor');
      const receiptCheck = document.getElementById('confirmacao-recebimento');
      if (nameTarget) nameTarget.textContent = customerName;
      if (enrollmentTarget) enrollmentTarget.textContent = enrollmentValue;
      if (amountTarget) amountTarget.textContent = formattedAmount;
      if (receiptCheck) receiptCheck.checked = false;

      const modalElement = document.getElementById('confirmar-recarga-modal');
      if (!modalElement || !window.bootstrap?.Modal) {
        alert('Não foi possível abrir a confirmação da recarga. Atualize a página e tente novamente.');
        return;
      }
      window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
    };

    document.getElementById('confirmar-recarga')?.addEventListener('click', openConfirmation);

    form?.addEventListener('submit', event => {
      const receiptCheck = document.getElementById('confirmacao-recebimento');
      if (!hiddenEnrollment?.value) {
        event.preventDefault();
        alert('Selecione um cliente antes de confirmar a recarga.');
        return;
      }
      if (!receiptCheck?.checked) {
        event.preventDefault();
        alert('Marque a confirmação de recebimento do dinheiro físico.');
        receiptCheck?.focus();
        return;
      }
    });

    filter();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();