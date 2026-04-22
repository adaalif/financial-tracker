/**
 * Add Expense Page — date defaults and dynamic row insertion.
 */

// Default date input to today
const dateInput = document.getElementById('date');
if (dateInput && !dateInput.value) {
  dateInput.value = new Date().toISOString().split('T')[0];
}

// Dynamic row insertion
document.getElementById('addItemBtn').addEventListener('click', () => {
  const list = document.getElementById('itemsList');
  const row = document.createElement('div');
  row.className = 'item-row';
  row.innerHTML = `
    <input type="text" name="item_names" placeholder="Item name" required>
    <input type="number" name="item_prices" step="0.01" placeholder="Price">
    <input type="text" name="item_categories" list="categories_list" placeholder="Category">
  `;
  list.appendChild(row);
  row.querySelector('input[name="item_names"]').focus();
});
