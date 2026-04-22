/**
 * CategoryDropdown Class
 * Turns a standard input field into a highly styled combo-box with autocomplete
 * and 'Add New' capabilities according to our Refined Brutalist aesthetic.
 */
class CategoryDropdown {
  constructor(inputElement) {
    this.originalInput = inputElement;
    
    // Extract categories from the referenced datalist
    this.categories = [];
    const listId = this.originalInput.getAttribute('list');
    if (listId) {
      const dataList = document.getElementById(listId);
      if (dataList) {
        dataList.querySelectorAll('option').forEach(opt => {
          if (opt.value) this.categories.push(opt.value);
        });
      }
      // Remove datalist attribute so browser native datalist doesn't show
      this.originalInput.removeAttribute('list');
    }
    
    // We want to wrap the original input so we retain form bindings
    this.wrapper = document.createElement('div');
    this.wrapper.style.position = 'relative';
    this.wrapper.style.width = '100%';
    
    // Insert wrapper before input, then move input inside
    this.originalInput.parentNode.insertBefore(this.wrapper, this.originalInput);
    this.wrapper.appendChild(this.originalInput);
    
    // Prevent default autocomplete native dropdown
    this.originalInput.setAttribute('autocomplete', 'off');
    
    // Create Dropdown Menu with our design tokens
    this.menu = document.createElement('div');
    this.menu.className = 'custom-dropdown-menu';
    this.menu.style.display = 'none';
    this.menu.style.position = 'absolute';
    this.menu.style.top = '100%';
    this.menu.style.left = '0';
    this.menu.style.width = '100%';
    this.menu.style.zIndex = '50';
    this.menu.style.background = 'var(--bg-card)';
    this.menu.style.border = '2px solid var(--border)';
    this.menu.style.boxShadow = '4px 4px 0px var(--carbon-black)';
    this.menu.style.marginTop = '4px';
    this.menu.style.maxHeight = '250px';
    this.menu.style.overflowY = 'auto';
    // Add custom scrollbar styling dynamically via a class we'll inject
    this.menu.classList.add('hide-scrollbar');
    this.wrapper.appendChild(this.menu);
    
    // State
    this.isOpen = false;
    
    // Bind Events
    this.originalInput.addEventListener('focus', () => this.openMenu());
    this.originalInput.addEventListener('click', () => this.openMenu());
    this.originalInput.addEventListener('input', () => this.renderOptions());
    
    // Click outside to close
    document.addEventListener('mousedown', (e) => {
      if (!this.wrapper.contains(e.target)) {
        this.closeMenu();
      }
    });

    // Handle Keyboard Navigation
    this.originalInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeMenu();
      if (e.key === 'Enter' && this.isOpen) {
        // Find if there's only one visible option to auto-select
        e.preventDefault(); // prevent form submit
        const visibleItems = Array.from(this.menu.children);
        if (visibleItems.length > 0) {
          visibleItems[0].click();
        }
      }
    });
  }
  
  openMenu() {
    if (this.isOpen) return;
    this.isOpen = true;
    this.menu.style.display = 'block';
    
    // Force animation
    this.menu.animate([
      { opacity: 0, transform: 'translateY(-8px)', filter: 'blur(2px)' },
      { opacity: 1, transform: 'translateY(0)', filter: 'blur(0px)' }
    ], { duration: 150, easing: 'cubic-bezier(0.4, 0, 0.2, 1)' });
    
    this.renderOptions();
  }
  
  closeMenu() {
    if (!this.isOpen) return;
    this.isOpen = false;
    // Animate out
    const animation = this.menu.animate([
      { opacity: 1, transform: 'translateY(0)' },
      { opacity: 0, transform: 'translateY(-4px)' }
    ], { duration: 100, easing: 'ease-in' });
    
    animation.onfinish = () => {
      this.menu.style.display = 'none';
    };
  }
  
  renderOptions() {
    this.menu.innerHTML = '';
    const query = this.originalInput.value.toLowerCase().trim();
    
    // Filter categories
    const filtered = this.categories.filter(c => c.toLowerCase().includes(query));
    
    // Add exact match flag
    const exactMatch = this.categories.some(c => c.toLowerCase() === query);
    
    if (filtered.length > 0) {
      filtered.forEach(cat => this.addOptionElement(cat, false));
    }
    
    // If there is a query and it's not an exact match, show Add New
    if (query && !exactMatch) {
      this.addOptionElement(this.originalInput.value.trim(), true);
    }
    
    // If completely empty, show nice empty state
    if (filtered.length === 0 && !query) {
      const emptyItem = document.createElement('div');
      emptyItem.textContent = 'Type to search or create...';
      emptyItem.style.padding = '0.85rem 1rem';
      emptyItem.style.color = 'var(--text-muted)';
      emptyItem.style.fontStyle = 'italic';
      emptyItem.style.fontFamily = 'var(--font-display)';
      this.menu.appendChild(emptyItem);
    }
  }
  
  addOptionElement(text, isNew) {
    const item = document.createElement('div');
    item.style.padding = '0.75rem 1rem';
    item.style.cursor = 'pointer';
    item.style.borderBottom = '2px solid var(--border)';
    item.style.transition = 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)';
    item.style.fontFamily = 'var(--font-display)';
    item.style.fontSize = '0.95rem';
    item.style.display = 'flex';
    item.style.alignItems = 'center';
    item.style.justifyContent = 'space-between';
    
    if (isNew) {
      item.innerHTML = `
        <span style="color: var(--spicy-paprika); font-weight: 800;">
          + ADD <span style="color: var(--carbon-black);">${text}</span>
        </span>
        <span style="font-size: 0.70rem; background: var(--carbon-black); color: var(--floral-white); padding: 3px 8px; border-radius: 0px; font-weight: 800; letter-spacing: 0.05em;">NEW</span>
      `;
      item.style.background = 'var(--floral-white)';
    } else {
      item.textContent = text;
      item.style.fontWeight = '700';
    }
    
    // Hover Effects matching the aesthetic
    item.addEventListener('mouseenter', () => {
      item.style.background = 'var(--bg-hover)';
      item.style.paddingLeft = '1.5rem';
      if(isNew) {
         item.style.background = 'rgba(235, 94, 40, 0.1)'; // faint spicy-paprika
      }
    });
    
    item.addEventListener('mouseleave', () => {
      item.style.background = isNew ? 'var(--floral-white)' : 'transparent';
      item.style.paddingLeft = '1rem';
    });
    
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      this.originalInput.value = text;
      
      // If it's new, add it to our local cache so it appears immediately
      if (isNew && !this.categories.includes(text)) {
        this.categories.push(text);
      }
      
      this.closeMenu();
      
      // Trigger change event just in case
      const event = new Event('change', { bubbles: true });
      this.originalInput.dispatchEvent(event);
    });
    
    this.menu.appendChild(item);
  }
}

// Global scope instantiation
window.initCategoryDropdowns = function() {
  const categoryInputs = document.querySelectorAll('input[list="categories_data"], input[list="categories_list"], input[name="item_categories"], input[name="category"]');
  categoryInputs.forEach(input => {
    if (!input.hasAttribute('data-dropdown-initialized')) {
      new CategoryDropdown(input);
      input.setAttribute('data-dropdown-initialized', 'true');
    }
  });
}

// Initialize on DOM Ready
function runInit() {
  window.initCategoryDropdowns();
  
  // Inject some CSS to hide scrollbars for cleaner geometry
  const style = document.createElement('style');
  style.textContent = `
    .custom-dropdown-menu::-webkit-scrollbar { width: 8px; }
    .custom-dropdown-menu::-webkit-scrollbar-track { background: var(--floral-white); border-left: 2px solid var(--border); }
    .custom-dropdown-menu::-webkit-scrollbar-thumb { background: var(--carbon-black); }
    .custom-dropdown-menu::-webkit-scrollbar-thumb:hover { background: var(--spicy-paprika); }
    .custom-dropdown-menu > div:last-child { border-bottom: none !important; }
  `;
  document.head.appendChild(style);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', runInit);
} else {
  runInit();
}

// Listen for dynamic DOM mutations (for rows added via JS)
const observer = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.addedNodes.length > 0) {
      window.initCategoryDropdowns();
    }
  });
});

observer.observe(document.body, { childList: true, subtree: true });
