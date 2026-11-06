/* HAP-F-003, F-051, F-052: staff accounts, dashboard, CSV export and background jobs (P Manas Siddhardha). */
(function () {
  const { React, html, api, Msg, useAsync, today } = HAP;
  const { useState } = React;

  function Dashboard() {
    const d = useAsync(() => api("/admin/dashboard"), []);
    const [from, setFrom] = useState(today(-30)), [to, setTo] = useState(today()), [err, setErr] = useState(null);
    async function exportCsv() { setErr(null); try { await HAP.download(`/admin/reports/appointments.csv?from=${from}&to=${to}`, `appointments_${from}_${to}.csv`); } catch (e) { setErr(e.message); } }
    if (!d.data) return html`<div class="card"><${Msg} error=${d.error} />Loading…</div>`;
    return html`<div class="card"><h2>Today (${d.data.date})</h2>
        ${d.data.todayByDoctor.length === 0 ? html`<p class="muted">No appointments today.</p>` : html`<table><thead><tr><th>Doctor</th><th>Total</th><th>By status</th></tr></thead><tbody>
        ${d.data.todayByDoctor.map((r) => html`<tr key=${r.doctorId}><td>${r.doctor}</td><td>${r.total}</td><td>${Object.entries(r.byStatus).map(([s, n]) => html`<span key=${s} class=${"chip " + s}>${s} ${n}</span> `)}</td></tr>`)}</tbody></table>`}
        <p>No-show rate (last 30 days): <b>${d.data.noShowRate30Days}%</b></p></div>
      <div class="card"><h2>Slot utilisation this week</h2><table><thead><tr><th>Doctor</th><th>Used / generated</th><th>%</th></tr></thead><tbody>
        ${d.data.utilisationThisWeek.map((u) => html`<tr key=${u.doctorId}><td>${u.doctor}</td><td>${u.usedSlots} / ${u.generatedSlots}</td><td>${u.utilisationPercent}%</td></tr>`)}</tbody></table></div>
      <div class="card"><h2>Export appointments (CSV)</h2><div class="row"><div><label for="ef">From</label><input id="ef" type="date" value=${from} onChange=${(e) => setFrom(e.target.value)} /></div>
        <div><label for="et">To</label><input id="et" type="date" value=${to} onChange=${(e) => setTo(e.target.value)} /></div></div>
        <div class="actions"><button onClick=${exportCsv}>Download CSV</button></div><${Msg} error=${err} /></div>`;
  }

  function Staff() {
    const users = useAsync(() => api("/admin/users"), []);
    const [f, setF] = useState({ email: "", fullName: "", role: "DOCTOR" }), [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
    async function create(e) {
      e.preventDefault(); setErr(null); setOk(null);
      try { const u = await api("/admin/users", { method: "POST", body: f }); setOk(`Created ${u.email}. One-time password: ${u.oneTimePassword}`); users.reload(); }
      catch (ex) { setErr(ex.message); }
    }
    async function toggle(u) { await api(`/admin/users/${u.id}`, { method: "PATCH", body: { isActive: !u.isActive } }); users.reload(); }
    return html`<div class="card"><h2>Create staff account</h2><form onSubmit=${create}><div class="row">
        <div><label for="se">Email</label><input id="se" type="email" value=${f.email} onChange=${set("email")} required /></div>
        <div><label for="sn">Full name</label><input id="sn" value=${f.fullName} onChange=${set("fullName")} required /></div>
        <div><label for="sr">Role</label><select id="sr" value=${f.role} onChange=${set("role")}><option>DOCTOR</option><option>RECEPTIONIST</option></select></div></div>
        <div class="actions"><button type="submit">Create</button></div></form><${Msg} error=${err} ok=${ok} /></div>
      <div class="card"><h2>Accounts</h2><table><thead><tr><th>Email</th><th>Name</th><th>Role</th><th>Active</th><th></th></tr></thead><tbody>
        ${(users.data || []).map((u) => html`<tr key=${u.id}><td>${u.email}</td><td>${u.fullName}</td><td>${u.role}</td><td>${u.isActive ? "yes" : "no"}</td>
          <td>${u.role !== "ADMIN" && html`<button class=${u.isActive ? "danger" : "secondary"} onClick=${() => toggle(u)}>${u.isActive ? "Deactivate" : "Reactivate"}</button>`}</td></tr>`)}</tbody></table></div>`;
  }

  function Jobs() {
    const jobs = useAsync(() => api("/admin/jobs"), []);
    const [msg, setMsg] = useState(null);
    async function run(name) { const r = await api(`/admin/jobs/${name}/run`, { method: "POST" }); setMsg(`${name}: ${r.processed} processed`); }
    return html`<div class="card"><h2>Background jobs</h2><p class="muted">These run automatically when ENABLE_SCHEDULER=1. You can also run them now.</p>
      <div class="actions">${(jobs.data || []).map((j) => html`<button key=${j.name} class="secondary" onClick=${() => run(j.name)}>Run ${j.name}</button>`)}</div><${Msg} ok=${msg} /></div>`;
  }

  HAP.registerPage({ id: "dashboard", title: "Dashboard", roles: ["ADMIN"], order: 10, component: Dashboard });
  HAP.registerPage({ id: "staff", title: "Staff", roles: ["ADMIN"], order: 20, component: () => html`<${Staff} /><${Jobs} />` });
})();
