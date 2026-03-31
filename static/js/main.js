/* ─── EduManage — Global JS Helpers ─────────────────────────────────────── */

/**
 * Show Bootstrap toast notification
 * @param {string} message
 * @param {string} type  success | danger | warning | info
 * @param {number} delay ms to show (default 3500)
 */
function showToast(message, type = 'success', delay = 3500) {
  const toastEl = document.getElementById('liveToast');
  const msgEl = document.getElementById('toastMsg');
  if (!toastEl || !msgEl) return;

  // Reset classes
  toastEl.className = 'toast align-items-center text-white border-0';
  toastEl.classList.add(`bg-${type}`);
  if (type === 'warning' || type === 'info') toastEl.classList.add('text-dark');
  else toastEl.classList.add('text-white');

  msgEl.textContent = message;

  const bsToast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay });
  bsToast.show();
}

/**
 * Render Bootstrap pagination
 * @param {number} totalPages
 * @param {number} currentPage
 * @param {Function} onPageClick  callback(page)
 */
function renderPagination(totalPages, currentPage, onPageClick) {
  const el = document.getElementById('pagination');
  if (!el) return;
  if (totalPages <= 1) { el.innerHTML = ''; return; }

  const makeItem = (label, page, disabled = false, active = false) => {
    const li = document.createElement('li');
    li.className = `page-item${disabled ? ' disabled' : ''}${active ? ' active' : ''}`;
    const a = document.createElement('a');
    a.className = 'page-link';
    a.href = '#';
    a.innerHTML = label;
    if (!disabled && !active) {
      a.addEventListener('click', e => { e.preventDefault(); onPageClick(page); });
    }
    li.appendChild(a);
    return li;
  };

  el.innerHTML = '';
  el.appendChild(makeItem('&laquo;', currentPage - 1, currentPage === 1));

  // Window of pages
  const window = 2;
  let start = Math.max(1, currentPage - window);
  let end   = Math.min(totalPages, currentPage + window);

  if (start > 1) {
    el.appendChild(makeItem('1', 1));
    if (start > 2) el.appendChild(makeItem('…', null, true));
  }

  for (let p = start; p <= end; p++) {
    el.appendChild(makeItem(p, p, false, p === currentPage));
  }

  if (end < totalPages) {
    if (end < totalPages - 1) el.appendChild(makeItem('…', null, true));
    el.appendChild(makeItem(totalPages, totalPages));
  }

  el.appendChild(makeItem('&raquo;', currentPage + 1, currentPage === totalPages));
}

/**
 * Debounce utility
 * @param {Function} fn
 * @param {number} delay ms
 */
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Preview image from file input
 * @param {HTMLInputElement} input
 * @param {string} previewId  id of <img> element
 */
function previewImg(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview) return;
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.classList.remove('d-none');
    };
    reader.readAsDataURL(input.files[0]);
  }
}

// ─── Sidebar Toggle ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('sidebarToggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const wrapper = document.getElementById('wrapper');
      const sidebar = document.getElementById('sidebar-wrapper');
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
      } else {
        wrapper.classList.toggle('toggled');
      }
    });
  }

  // Close sidebar on overlay click (mobile)
  document.addEventListener('click', e => {
    const sidebar = document.getElementById('sidebar-wrapper');
    const toggleBtn = document.getElementById('sidebarToggle');
    if (
      sidebar &&
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      e.target !== toggleBtn
    ) {
      sidebar.classList.remove('open');
    }
  });
});
