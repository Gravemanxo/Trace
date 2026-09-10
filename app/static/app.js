(() => {
  const body = document.body;
  const toggles = document.querySelectorAll('[data-action="toggle-sidebar"]');
  const setSidebar = (open) => {
    body.classList.toggle('sidebar-open', open);
    toggles.forEach((button) => button.setAttribute('aria-expanded', String(open)));
  };
  toggles.forEach((button) => button.addEventListener('click', () => setSidebar(!body.classList.contains('sidebar-open'))));
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') setSidebar(false); });

  document.querySelectorAll('[data-dialog-open]').forEach((button) => {
    button.addEventListener('click', () => document.getElementById(button.dataset.dialogOpen)?.showModal());
  });
  document.querySelectorAll('[data-dialog-close]').forEach((button) => {
    button.addEventListener('click', () => button.closest('dialog')?.close());
  });
  document.querySelectorAll('dialog').forEach((dialog) => {
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  });

  document.querySelectorAll('[data-month-picker]').forEach((input) => {
    input.addEventListener('change', () => { if (input.value) window.location.assign(`${input.dataset.target}${encodeURIComponent(input.value)}`); });
  });
  document.querySelectorAll('[data-confirm]').forEach((button) => {
    button.addEventListener('click', (event) => { if (!window.confirm(button.dataset.confirm)) event.preventDefault(); });
  });

  const todayLink = document.querySelector('[data-today-link]');
  if (todayLink) {
    const localToday = new Date();
    const date = [localToday.getFullYear(), String(localToday.getMonth() + 1).padStart(2, '0'), String(localToday.getDate()).padStart(2, '0')].join('-');
    todayLink.href = `/days/${date}`;
  }

  const timer = document.querySelector('[data-live-timer]');
  if (timer) {
    const startedAt = timer.dataset.started ? new Date(timer.dataset.started).getTime() : null;
    const completedMs = Number(timer.dataset.completedSeconds || 0) * 1000;
    const render = () => {
      const elapsed = completedMs + (startedAt ? Math.max(0, Date.now() - startedAt) : 0);
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor(elapsed / 60000) % 60;
      const seconds = Math.floor(elapsed / 1000) % 60;
      const milliseconds = Math.floor(elapsed % 1000);
      timer.innerHTML = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}<span>.${String(milliseconds).padStart(3, '0')}</span>`;
    };
    render();
    if (startedAt) window.setInterval(render, 43);
  }
})();
