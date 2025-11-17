// pdfforge/static/js/toc.js
// Extracted from original toc.html inline script
(function () {
  let currentFile = null;
  let currentPageCount = 0;

  function byId(id) { return document.getElementById(id); }

  function showSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'spinner';
    const container = document.querySelector('.content') || document.body;
    container.appendChild(spinner);
  }

  function hideSpinner() {
    const el = byId('spinner');
    if (el) el.remove();
  }

  function showSuccess(message) {
    const alert = byId('successAlert');
    if (!alert) return;
    alert.textContent = message;
    alert.classList.add('active');
    setTimeout(() => alert.classList.remove('active'), 5000);
  }

  function showError(message) {
    const alert = byId('errorAlert');
    if (!alert) return;
    alert.textContent = message;
    alert.classList.add('active');
    setTimeout(() => alert.classList.remove('active'), 5000);
  }

  function displayFileInfo(filename, pageCount) {
    const fileName = byId('fileName');
    const pageCountEl = byId('pageCount');
    const fileInfo = byId('fileInfo');
    const bookmarksSection = byId('bookmarksSection');
    if (fileName) fileName.textContent = filename;
    if (pageCountEl) pageCountEl.textContent = pageCount;
    if (fileInfo) fileInfo.classList.add('active');
    if (bookmarksSection) bookmarksSection.classList.add('active');
  }

  function addBookmarkRow(bookmark) {
    const table = byId('bookmarksTable');
    const tbody = byId('bookmarksBody');
    const emptyState = byId('emptyState');
    if (!table || !tbody) return;

    emptyState.style.display = 'none';
    table.style.display = 'table';

    let pageValue = 1;
    if (bookmark && bookmark.page) pageValue = bookmark.page;

    const row = tbody.insertRow();
    row.innerHTML = `
        <td>
            <input type="text" class="bookmark-title" value="${bookmark ? (bookmark.title || '') : ''}" placeholder="Enter title...">
        </td>
        <td>
            <input type="number" class="bookmark-page" value="${pageValue}" min="1" max="${currentPageCount}">
        </td>
        <td>
            <select class="bookmark-level">
                <option value="0" ${!bookmark || bookmark.level === 0 ? 'selected' : ''}>Level 1</option>
                <option value="1" ${bookmark && bookmark.level === 1 ? 'selected' : ''}>Level 2</option>
                <option value="2" ${bookmark && bookmark.level === 2 ? 'selected' : ''}>Level 3</option>
            </select>
        </td>
        <td>
            <button class="delete-btn" onclick="deleteBookmarkRow(this)">🗑️ Delete</button>
        </td>
    `;
  }

  function displayBookmarks(bookmarks) {
    const emptyState = byId('emptyState');
    const table = byId('bookmarksTable');
    const tbody = byId('bookmarksBody');
    if (!tbody || !table) return;

    tbody.innerHTML = '';

    if (!bookmarks || bookmarks.length === 0) {
      emptyState.style.display = 'block';
      table.style.display = 'none';
    } else {
      emptyState.style.display = 'none';
      table.style.display = 'table';
      bookmarks.forEach(bm => addBookmarkRow(bm));
    }
  }

  function deleteBookmarkRow(btn) {
    const row = btn.closest('tr');
    if (row) row.remove();
    const tbody = byId('bookmarksBody');
    if (tbody.rows.length === 0) {
      byId('emptyState').style.display = 'block';
      byId('bookmarksTable').style.display = 'none';
    }
  }

  function prepareBookmarksForBackend() {
    const tbody = byId('bookmarksBody');
    const bookmarks = [];
    for (let row of tbody.rows) {
      const title = row.querySelector('.bookmark-title').value.trim();
      const page = parseInt(row.querySelector('.bookmark-page').value);
      const level = parseInt(row.querySelector('.bookmark-level').value);
      if (title && !isNaN(page)) bookmarks.push({ title, page, level });
    }
    return bookmarks;
  }

  function loadPDF(file) {
    currentFile = file;
    showSpinner();
    const formData = new FormData();
    formData.append('file', file);
    fetch('/toc/extract', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(data => {
        hideSpinner();
        if (!data.success) throw new Error(data.error || 'Failed to load PDF');
        currentPageCount = data.page_count || 0;
        displayFileInfo(data.filename, data.page_count);
        displayBookmarks(data.bookmarks || []);
      })
      .catch(err => { hideSpinner(); showError(err.message); });
  }

  function generateTOC() {
    const bookmarks = prepareBookmarksForBackend();
    if (bookmarks.length === 0) return showError('Please add at least one bookmark');
    if (!currentFile) return showError('No PDF file loaded');

    showSpinner();
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('bookmarks', JSON.stringify(bookmarks));
    const tocStyle = {
      title: byId('tocTitle').value,
      show_page_numbers: byId('showPageNumbers').checked,
      leader_dots: byId('leaderDots').checked,
      page_number_position: byId('tocPageNumberPosition').value,
    };
    formData.append('toc_style', JSON.stringify(tocStyle));

    fetch('/toc/generate', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(data => {
        hideSpinner();
        if (!data.success) return showError(data.error || 'Failed to generate TOC');
        if (data.download_url) window.location.href = data.download_url;
        showSuccess('TOC generated successfully!');
      })
      .catch(err => { hideSpinner(); showError('Error generating TOC: ' + err.message); });
  }

  function updateBookmarks() {
    const bookmarks = prepareBookmarksForBackend();
    if (bookmarks.length === 0) return showError('Please add at least one bookmark');
    if (!currentFile) return showError('No PDF file loaded');

    showSpinner();
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('bookmarks', JSON.stringify(bookmarks));

    fetch('/toc/update-bookmarks', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(data => {
        hideSpinner();
        if (!data.success) return showError(data.error || 'Failed to update bookmarks');
        if (data.download_url) window.location.href = data.download_url;
        showSuccess('Bookmarks updated successfully!');
      })
      .catch(err => { hideSpinner(); showError('Error updating bookmarks: ' + err.message); });
  }

  function initUpload() {
    const fileInput = byId('pdfFile');
    const uploadSection = byId('uploadSection');
    if (!fileInput || !uploadSection) return;

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) loadPDF(file);
    });

    uploadSection.addEventListener('dragover', (e) => { e.preventDefault(); uploadSection.classList.add('dragover'); });
    uploadSection.addEventListener('dragleave', () => uploadSection.classList.remove('dragover'));
    uploadSection.addEventListener('drop', (e) => {
      e.preventDefault(); uploadSection.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && file.type === 'application/pdf') {
        currentFile = file;
        fileInput.files = e.dataTransfer.files;
        loadPDF(file);
      } else {
        showError('Please drop a PDF file');
      }
    });
  }

  // Expose functions for onclick handlers
  window.addBookmarkRow = addBookmarkRow;
  window.deleteBookmarkRow = deleteBookmarkRow;
  window.generateTOC = generateTOC;
  window.updateBookmarks = updateBookmarks;

  document.addEventListener('DOMContentLoaded', initUpload);
})();
