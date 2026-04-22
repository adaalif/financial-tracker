/**
 * History Page — Search, Sort, and Delete Modal logic.
 */

// ─── Live Search / Filter ───
const searchInput = document.getElementById('searchInput');
const tableBody = document.getElementById('tableBody');
const rowCountEl = document.getElementById('rowCount');

if (searchInput && tableBody) {
  searchInput.addEventListener('input', function () {
    const query = this.value.toLowerCase().trim();
    const rows = tableBody.querySelectorAll('tr');
    let visible = 0;
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const match = !query || text.includes(query);
      row.style.display = match ? '' : 'none';
      if (match) visible++;
    });
    if (rowCountEl) rowCountEl.textContent = visible;
  });
}

// ─── Column Sorting ───
document.querySelectorAll('.sortable').forEach(th => {
  th.style.cursor = 'pointer';
  th.style.userSelect = 'none';
  th.innerHTML =
    th.textContent +
    ' <span style="opacity:0.4; font-size:0.7rem;">&#9650;&#9660;</span>';

  th.addEventListener('click', function () {
    const table = document.getElementById('dataTable');
    const tbody = table.querySelector('tbody');
    const colIdx = parseInt(this.dataset.col);
    const type = this.dataset.type;

    const currentDir = this.dataset.dir || 'asc';
    const newDir = currentDir === 'asc' ? 'desc' : 'asc';

    document.querySelectorAll('.sortable').forEach(h => (h.dataset.dir = ''));
    this.dataset.dir = newDir;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
      let aVal = a.children[colIdx].textContent.trim();
      let bVal = b.children[colIdx].textContent.trim();

      if (type === 'number') {
        aVal = parseFloat(aVal.replace(/[^\d.-]/g, '')) || 0;
        bVal = parseFloat(bVal.replace(/[^\d.-]/g, '')) || 0;
      } else {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return newDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return newDir === 'asc' ? 1 : -1;
      return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
  });
});

// ─── Delete Confirmation Modal ───
const overlay = document.getElementById('deleteModal');
const modalName = document.getElementById('modalItemName');
const confirmBtn = document.getElementById('modalConfirmBtn');
const cancelBtn = document.getElementById('modalCancelBtn');
let pendingDeleteId = null;

document.querySelectorAll('.delete-trigger').forEach(btn => {
  btn.addEventListener('click', function () {
    pendingDeleteId = this.dataset.id;
    modalName.textContent = this.dataset.name;
    overlay.classList.add('active');
  });
});

if (cancelBtn) {
  cancelBtn.addEventListener('click', () => {
    overlay.classList.remove('active');
    pendingDeleteId = null;
  });
}

if (overlay) {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) {
      overlay.classList.remove('active');
      pendingDeleteId = null;
    }
  });
}

if (confirmBtn) {
  confirmBtn.addEventListener('click', () => {
    if (pendingDeleteId) {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/delete/' + pendingDeleteId;
      document.body.appendChild(form);
      form.submit();
    }
  });
}
