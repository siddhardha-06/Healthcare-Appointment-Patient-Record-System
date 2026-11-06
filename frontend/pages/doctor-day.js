/* HAP-F-040: doctor's day list and patient chart (Parth Kale). Consultation forms follow in Sprint 2. */
(function () {
  const { React, html, api, Msg, useAsync, fmt, time, today } = HAP;
  const { useState } = React;

  function Chart({ patientId }) {
    const chart = useAsync(() => api(`/patients/${patientId}/records`), [patientId]);
    if (chart.error) return html`<${Msg} error=${chart.error} />`;
    if (!chart.data) return html`<p class="muted">Loading chart…</p>`;
    const { patient, visits, prescriptions } = chart.data;
    return html`<div>
      ${patient.allergies.length > 0 ? html`<div class="allergy" role="alert">Allergies: ${patient.allergies.join(", ")}</div>`
                                     : html`<div class="muted">No known allergies</div>`}
      <p><b>${patient.name}</b> · ${patient.mrn} · ${patient.age} y · ${patient.gender} · blood group ${patient.bloodGroup || "—"}</p>
      <h3>Past visits</h3>${visits.length === 0 ? html`<p class="muted">No previous visits.</p>` : html`<table><tbody>
        ${visits.map((v) => html`<tr key=${v.consultationId}><td>${fmt(v.date)}</td><td>${v.doctor}</td><td>${v.diagnosis}</td><td class="muted">v${v.version}</td></tr>`)}</tbody></table>`}
      <h3>Prescriptions</h3>${prescriptions.length === 0 ? html`<p class="muted">None.</p>` : html`<table><tbody>
        ${prescriptions.map((p) => html`<tr key=${p.prescriptionId}><td>${fmt(p.date)}</td><td>${p.doctor}</td><td>${p.items} item(s)</td>
          <td><button class="secondary" onClick=${() => HAP.download(`/prescriptions/${p.prescriptionId}/pdf`, `rx-${p.prescriptionId}.pdf`)}>PDF</button></td></tr>`)}</tbody></table>`}
    </div>`;
  }

  function DoctorDay() {
    const [day, setDay] = useState(today()), [open, setOpen] = useState(null);
    const list = useAsync(() => api("/appointments?date=" + day), [day]);
    const items = (list.data && list.data.items) || [];
    return html`<div class="grid2"><div class="card"><h2>My day</h2>
        <label for="dd">Date</label><input id="dd" type="date" value=${day} onChange=${(e) => { setDay(e.target.value); setOpen(null); }} />
        <${Msg} error=${list.error} />
        <table><tbody>${items.map((a) => html`<tr key=${a.id} style=${open && open.id === a.id ? { background: "#e3f1ef" } : {}}>
          <td>${time(a.start)}</td><td>${a.patientName}<div class="muted">${a.reason}</div></td><td><span class=${"chip " + a.status}>${a.status}</span></td>
          <td><button class="secondary" onClick=${() => setOpen(a)}>Open</button></td></tr>`)}</tbody></table>
        ${items.length === 0 && html`<p class="muted">No appointments.</p>`}</div>
      <div class="card">${open ? html`<h2>Patient chart</h2><${Chart} key=${open.id + open.status} patientId=${open.patientId} />
`
        : html`<p class="muted">Open an appointment to see the chart.</p>`}</div></div>`;
  }

  HAP.registerPage({ id: "my-day", title: "My day", roles: ["DOCTOR"], order: 10, component: DoctorDay });
})();
