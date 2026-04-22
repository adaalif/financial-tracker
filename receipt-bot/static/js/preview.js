/**
 * Preview Page — dynamic item row insertion for scanned receipts.
 * Reads available categories from a hidden datalist element (#categories_data).
 */

document.getElementById('addItemBtn').addEventListener('click', () => {
  const list = document.getElementById('itemsList');

  // Build category options from the datalist injected by the server
  const datalist = document.getElementById('categories_data');
  let optionsHtml = '';
  if (datalist) {
    datalist.querySelectorAll('option').forEach(opt => {
      optionsHtml += `<option value="${opt.value}">${opt.value}</option>`;
    });
  }

  const row = document.createElement('div');
  row.className = 'item-row';
  row.innerHTML = `
    <input type="text" name="item_names" placeholder="Item name">
    <input type="number" name="item_prices" step="0.01" placeholder="Price">
    <input type="text" name="item_categories" list="categories_data" placeholder="Category">
  `;
  list.appendChild(row);
});
