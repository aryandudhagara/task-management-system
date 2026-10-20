/**
 * script.js
 * ---------
 * All frontend logic for the Task Management System.
 *
 * This file:
 *  - Fetches tasks from the Flask REST API using the browser's built-in
 *    fetch() function.
 *  - Renders task cards into the DOM.
 *  - Handles Add / Edit / Delete / Complete actions.
 *  - Implements live search and filter controls.
 *  - Shows toast notifications for success and error feedback.
 *
 * No external libraries — just plain JavaScript (ES2021).
 */

"use strict";

// ─────────────────────────────────────────────
// 1. DOM REFERENCES
// ─────────────────────────────────────────────

const taskList         = document.getElementById("task-list");
const loadingIndicator = document.getElementById("loading-indicator");
const emptyState       = document.getElementById("empty-state");

// Stats
const countTotal     = document.getElementById("count-total");
const countPending   = document.getElementById("count-pending");
const countCompleted = document.getElementById("count-completed");

// Toolbar
const searchInput     = document.getElementById("search-input");
const filterStatus    = document.getElementById("filter-status");
const filterPriority  = document.getElementById("filter-priority");
const btnClearFilters = document.getElementById("btn-clear-filters");

// Modal
const taskModal      = document.getElementById("task-modal");
const modalTitle     = document.getElementById("modal-title");
const btnOpenModal   = document.getElementById("btn-open-modal");
const btnCloseModal  = document.getElementById("btn-close-modal");
const btnCancel      = document.getElementById("btn-cancel");
const taskForm       = document.getElementById("task-form");
const taskIdField    = document.getElementById("task-id");
const fieldTitle     = document.getElementById("field-title");
const fieldDesc      = document.getElementById("field-description");
const fieldPriority  = document.getElementById("field-priority");
const fieldDueDate   = document.getElementById("field-due-date");
const fieldStatus    = document.getElementById("field-status");
const statusGroup    = document.getElementById("status-group");
const btnSubmitLabel = document.getElementById("btn-submit-label");
const errorTitle     = document.getElementById("error-title");
const errorPriority  = document.getElementById("error-priority");
const formErrorMsg   = document.getElementById("form-error-msg");

// Confirm dialog
const confirmDialog   = document.getElementById("confirm-dialog");
const confirmMessage  = document.getElementById("confirm-message");
const btnConfirmOk    = document.getElementById("btn-confirm-ok");
const btnConfirmCancel= document.getElementById("btn-confirm-cancel");

// Toast
const toast = document.getElementById("toast");

// ─────────────────────────────────────────────
// 2. STATE
// ─────────────────────────────────────────────

let allTasks   = [];       // cached task list from last fetch
let searchTimer = null;    // debounce timer for search input
let pendingDeleteId = null; // task ID waiting for delete confirmation

// ─────────────────────────────────────────────
// 3. API HELPERS
// ─────────────────────────────────────────────

const API_BASE = "/api/tasks";

/**
 * Wrapper around fetch() that handles JSON parsing and throws a
 * descriptive error if the response is not OK.
 */
async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const json = await res.json();
  if (!res.ok || !json.success) {
    throw new Error(json.error || `HTTP ${res.status}`);
  }
  return json.data;
}

// ─────────────────────────────────────────────
// 4. TASK LOADING & RENDERING
// ─────────────────────────────────────────────

/**
 * Fetch tasks from the API (with optional filters) and render them.
 */
async function loadTasks() {
  showLoading(true);

  const params = new URLSearchParams();
  const status   = filterStatus.value;
  const priority = filterPriority.value;
  const search   = searchInput.value.trim();

  if (status)   params.set("status",   status);
  if (priority) params.set("priority", priority);
  if (search)   params.set("search",   search);

  const url = `${API_BASE}?${params.toString()}`;

  try {
    const data = await apiFetch(url);
    allTasks = data.tasks;
    updateCounts(data.counts);
    renderTasks(allTasks);
  } catch (err) {
    showToast("Failed to load tasks: " + err.message, "error");
  } finally {
    showLoading(false);
  }
}

/**
 * Update the summary stat cards.
 */
function updateCounts(counts) {
  countTotal.textContent     = counts.total;
  countPending.textContent   = counts.pending;
  countCompleted.textContent = counts.completed;
}

/**
 * Build and inject task card HTML for each task.
 */
function renderTasks(tasks) {
  // Clear everything except the loading indicator
  taskList.querySelectorAll(".task-card").forEach(el => el.remove());

  if (tasks.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  tasks.forEach(task => {
    const card = buildTaskCard(task);
    taskList.appendChild(card);
  });
}

/**
 * Create a single task card DOM element.
 */
function buildTaskCard(task) {
  const card = document.createElement("article");
  card.className = `task-card ${task.status === "Completed" ? "completed" : "pending"}`;
  card.dataset.id = task.id;

  const priorityClass = {
    High:   "badge-high",
    Medium: "badge-medium",
    Low:    "badge-low",
  }[task.priority] || "badge-medium";

  const statusClass = task.status === "Completed" ? "badge-completed" : "badge-pending";

  const dueDateStr = task.due_date
    ? `<span class="task-meta-item">📅 ${formatDate(task.due_date)}</span>`
    : "";

  const descHtml = task.description
    ? `<p class="task-description">${escHtml(task.description)}</p>`
    : "";

  card.innerHTML = `
    <div class="task-info">
      <div class="task-title-row">
        <span class="task-title">${escHtml(task.title)}</span>
        <span class="badge ${priorityClass}">${task.priority}</span>
        <span class="badge ${statusClass}">${task.status}</span>
      </div>
      <div class="task-meta">
        <span class="task-meta-item">🕐 ${formatDateTime(task.created_at)}</span>
        ${dueDateStr}
      </div>
      ${descHtml}
    </div>
    <div class="task-actions">
      ${task.status !== "Completed"
        ? `<button class="btn-icon btn-complete" title="Mark as completed" aria-label="Mark task as completed" data-id="${task.id}">✓</button>`
        : ""}
      <button class="btn-icon btn-edit" title="Edit task" aria-label="Edit task" data-id="${task.id}">✎</button>
      <button class="btn-icon btn-delete" title="Delete task" aria-label="Delete task" data-id="${task.id}" style="color:#f87171;border-color:rgba(239,68,68,.3);">🗑</button>
    </div>
  `;

  // Wire up buttons inside this card
  const completBtn = card.querySelector(".btn-complete");
  if (completBtn) completBtn.addEventListener("click", () => handleComplete(task.id));
  card.querySelector(".btn-edit").addEventListener("click",   () => openEditModal(task));
  card.querySelector(".btn-delete").addEventListener("click", () => confirmDelete(task.id, task.title));

  return card;
}

// ─────────────────────────────────────────────
// 5. TASK ACTIONS
// ─────────────────────────────────────────────

/** Mark a task as completed via the PATCH endpoint. */
async function handleComplete(id) {
  try {
    await apiFetch(`${API_BASE}/${id}/complete`, { method: "PATCH" });
    showToast("Task marked as completed! 🎉", "success");
    loadTasks();
  } catch (err) {
    showToast("Could not complete task: " + err.message, "error");
  }
}

/** Ask the user to confirm before deleting. */
function confirmDelete(id, title) {
  pendingDeleteId = id;
  confirmMessage.textContent = `Are you sure you want to delete "${title}"? This action cannot be undone.`;
  confirmDialog.classList.remove("hidden");
}

/** Carry out the deletion after the user confirms. */
async function handleDelete() {
  confirmDialog.classList.add("hidden");
  if (!pendingDeleteId) return;
  try {
    await apiFetch(`${API_BASE}/${pendingDeleteId}`, { method: "DELETE" });
    showToast("Task deleted.", "info");
    loadTasks();
  } catch (err) {
    showToast("Could not delete task: " + err.message, "error");
  } finally {
    pendingDeleteId = null;
  }
}

// ─────────────────────────────────────────────
// 6. FORM (CREATE / EDIT)
// ─────────────────────────────────────────────

/** Open the modal in "Add" mode. */
function openAddModal() {
  taskIdField.value    = "";
  taskForm.reset();
  modalTitle.textContent   = "Add New Task";
  btnSubmitLabel.textContent = "Create Task";
  statusGroup.classList.add("hidden");
  clearFormErrors();
  taskModal.classList.remove("hidden");
  fieldTitle.focus();
}

/** Open the modal pre-filled with an existing task's data. */
function openEditModal(task) {
  taskIdField.value         = task.id;
  fieldTitle.value          = task.title;
  fieldDesc.value           = task.description || "";
  fieldPriority.value       = task.priority;
  fieldDueDate.value        = task.due_date || "";
  fieldStatus.value         = task.status;
  modalTitle.textContent    = "Edit Task";
  btnSubmitLabel.textContent = "Save Changes";
  statusGroup.classList.remove("hidden"); // show status selector when editing
  clearFormErrors();
  taskModal.classList.remove("hidden");
  fieldTitle.focus();
}

/** Close the modal and reset state. */
function closeModal() {
  taskModal.classList.add("hidden");
  taskForm.reset();
  taskIdField.value = "";
  clearFormErrors();
}

function clearFormErrors() {
  [errorTitle, errorPriority, formErrorMsg].forEach(el => {
    el.textContent = "";
    el.classList.add("hidden");
  });
  [fieldTitle, fieldPriority].forEach(el => el.classList.remove("invalid"));
}

/** Handle form submission for both create and update. */
async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const id       = taskIdField.value;
  const title    = fieldTitle.value.trim();
  const priority = fieldPriority.value;

  // Client-side validation
  let hasError = false;
  if (!title) {
    showFieldError(errorTitle, fieldTitle, "Title is required.");
    hasError = true;
  }
  if (!priority) {
    showFieldError(errorPriority, fieldPriority, "Please select a priority.");
    hasError = true;
  }
  if (hasError) return;

  const payload = {
    title,
    description: fieldDesc.value.trim(),
    priority,
    due_date: fieldDueDate.value || null,
  };

  // Include status only when editing
  if (id) {
    payload.status = fieldStatus.value;
  }

  try {
    if (id) {
      await apiFetch(`${API_BASE}/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showToast("Task updated successfully!", "success");
    } else {
      await apiFetch(API_BASE, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showToast("Task created successfully! 🚀", "success");
    }
    closeModal();
    loadTasks();
  } catch (err) {
    formErrorMsg.textContent = err.message;
    formErrorMsg.classList.remove("hidden");
  }
}

function showFieldError(errorEl, inputEl, message) {
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
  inputEl.classList.add("invalid");
}

// ─────────────────────────────────────────────
// 7. SEARCH & FILTERS
// ─────────────────────────────────────────────

/** Debounced search — waits 350 ms after typing stops. */
function onSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadTasks, 350);
}

function clearFilters() {
  searchInput.value    = "";
  filterStatus.value   = "";
  filterPriority.value = "";
  loadTasks();
}

// ─────────────────────────────────────────────
// 8. TOAST NOTIFICATIONS
// ─────────────────────────────────────────────

let toastTimer = null;

/**
 * Display a temporary notification at the bottom-right of the screen.
 * type: "success" | "error" | "info"
 */
function showToast(message, type = "info") {
  toast.textContent = message;
  toast.className   = `toast ${type}`;
  // Force reflow so the CSS transition fires again even if toast is visible
  toast.offsetHeight; // eslint-disable-line no-unused-expressions
  toast.classList.add("show");

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// ─────────────────────────────────────────────
// 9. UTILITIES
// ─────────────────────────────────────────────

function showLoading(visible) {
  if (visible) {
    loadingIndicator.style.display = "flex";
    emptyState.classList.add("hidden");
  } else {
    loadingIndicator.style.display = "none";
  }
}

/** Escape HTML to prevent XSS when inserting user content into innerHTML. */
function escHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(String(str)));
  return div.innerHTML;
}

/** Format "2026-12-31" → "31 Dec 2026" */
function formatDate(dateStr) {
  if (!dateStr) return "";
  const [year, month, day] = dateStr.split("-");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${parseInt(day)} ${months[parseInt(month) - 1]} ${year}`;
}

/** Format "2026-10-11 18:00:00" → "11 Oct 2026" */
function formatDateTime(dtStr) {
  if (!dtStr) return "";
  return formatDate(dtStr.split(" ")[0]);
}

// ─────────────────────────────────────────────
// 10. EVENT LISTENERS
// ─────────────────────────────────────────────

// Open/close modal
btnOpenModal.addEventListener("click",  openAddModal);
btnCloseModal.addEventListener("click", closeModal);
btnCancel.addEventListener("click",     closeModal);

// Close modal when clicking outside
taskModal.addEventListener("click", e => {
  if (e.target === taskModal) closeModal();
});

// Form submit
taskForm.addEventListener("submit", handleFormSubmit);

// Confirm dialog
btnConfirmOk.addEventListener("click",     handleDelete);
btnConfirmCancel.addEventListener("click", () => {
  confirmDialog.classList.add("hidden");
  pendingDeleteId = null;
});
confirmDialog.addEventListener("click", e => {
  if (e.target === confirmDialog) {
    confirmDialog.classList.add("hidden");
    pendingDeleteId = null;
  }
});

// Search & filters
searchInput.addEventListener("input",    onSearchInput);
filterStatus.addEventListener("change",  loadTasks);
filterPriority.addEventListener("change",loadTasks);
btnClearFilters.addEventListener("click",clearFilters);

// Keyboard: Escape closes modals
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (!taskModal.classList.contains("hidden"))    closeModal();
    if (!confirmDialog.classList.contains("hidden")) {
      confirmDialog.classList.add("hidden");
      pendingDeleteId = null;
    }
  }
});

// ─────────────────────────────────────────────
// 11. INITIALISE
// ─────────────────────────────────────────────

// Load tasks as soon as the page is ready
loadTasks();
