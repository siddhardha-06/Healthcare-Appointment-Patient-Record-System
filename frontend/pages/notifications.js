/* HAP-F-050: in-app notifications for patients (P Manas Siddhardha). */
(function () {
  const { React, html, api, Msg, useAsync, fmt } = HAP;

  function Notifications() {
    const list = useAsync(() => api("/notifications/me"), []);
    async function read(n) { await api(`/notifications/${n.id}/read`, { method: "PATCH" }); list.reload(); }
    const items = list.data || [];
    return html`<div class="card"><h2>Notifications</h2><${Msg} error=${list.error} />
      ${items.length === 0 ? html`<p class="muted">Nothing yet.</p>` : html`<table><tbody>
      ${items.map((n) => html`<tr key=${n.id} style=${n.isRead ? { color: "#5f6b76" } : { fontWeight: 600 }}><td>${fmt(n.createdAt)}</td><td>${n.message}</td>
        <td>${!n.isRead && html`<button class="secondary" onClick=${() => read(n)}>Mark read</button>`}</td></tr>`)}</tbody></table>`}</div>`;
  }

  HAP.registerPage({ id: "notifications", title: "Notifications", roles: ["PATIENT"], order: 40, component: Notifications });
})();
