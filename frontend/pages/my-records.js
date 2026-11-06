/* HAP-F-043: a patient's own visits and prescriptions, read-only, with PDF download (Parth Kale). */
(function () {
  const { React, html, api, Msg, useAsync, fmt } = HAP;
  const { useState } = React;

  function Prescription({ id }) {
    const rx = useAsync(() => api("/prescriptions/" + id), [id]);
    if (!rx.data) return html`<${Msg} error=${rx.error} />`;
    return html`<table><thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Days</th><th>Instructions</th></tr></thead><tbody>
      ${rx.data.items.map((it, i) => html`<tr key=${i}><td>${it.medicine}</td><td>${it.dosage}</td><td>${it.frequency}</td><td>${it.durationDays}</td><td>${it.instructions || ""}</td></tr>`)}
      </tbody></table>`;
  }

  function MyRecords() {
    const rec = useAsync(() => api("/patients/me/records"), []);
    const [open, setOpen] = useState(null);
    if (rec.error) return html`<div class="card"><${Msg} error=${rec.error} /></div>`;
    if (!rec.data) return html`<div class="card">Loading…</div>`;
    const { visits, prescriptions } = rec.data;
    return html`<div class="card"><h2>My visits</h2>${visits.length === 0 ? html`<p class="muted">No visits yet.</p>` : html`<table><thead><tr><th>Date</th><th>Doctor</th><th>Diagnosis</th></tr></thead><tbody>
        ${visits.map((v) => html`<tr key=${v.consultationId}><td>${fmt(v.date)}</td><td>${v.doctor}</td><td>${v.diagnosis}</td></tr>`)}</tbody></table>`}</div>
      <div class="card"><h2>My prescriptions</h2>${prescriptions.length === 0 ? html`<p class="muted">No prescriptions yet.</p>` :
        prescriptions.map((p) => html`<div key=${p.prescriptionId} style=${{ marginBottom: "12px" }}><b>${fmt(p.date)}</b> – ${p.doctor}
          <div class="actions"><button class="secondary" onClick=${() => setOpen(open === p.prescriptionId ? null : p.prescriptionId)}>${open === p.prescriptionId ? "Hide" : "View"}</button>
            <button onClick=${() => HAP.download(`/prescriptions/${p.prescriptionId}/pdf`, `prescription-${p.prescriptionId}.pdf`)}>Download PDF</button></div>
          ${open === p.prescriptionId && html`<${Prescription} id=${p.prescriptionId} />`}</div>`)}</div>`;
  }

  HAP.registerPage({ id: "records", title: "My records", roles: ["PATIENT"], order: 30, component: MyRecords });
})();
