/* HAP-F-040 … F-042: doctor's day list, patient chart, consultation notes and prescriptions (Parth Kale). */
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

  function ConsultationForm({ appt, onSaved }) {
    const [f, setF] = useState({ symptoms: "", diagnosis: "", notes: "", bp: "", pulse: "", tempC: "", weightKg: "" });
    const [items, setItems] = useState([{ medicine: "", dosage: "", frequency: "", durationDays: 5, instructions: "" }]);
    const [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
    const setItem = (i, k) => (e) => setItems(items.map((it, j) => (j === i ? { ...it, [k]: e.target.value } : it)));
    async function save(e) {
      e.preventDefault(); setErr(null); setOk(null);
      const vitals = {};
      if (f.bp) vitals.bp = f.bp; if (f.pulse) vitals.pulse = Number(f.pulse); if (f.tempC) vitals.tempC = Number(f.tempC); if (f.weightKg) vitals.weightKg = Number(f.weightKg);
      try {
        await api(`/appointments/${appt.id}/consultation`, { method: "POST", body: { symptoms: f.symptoms, diagnosis: f.diagnosis, notes: f.notes || null, vitals } });
        const rxItems = items.filter((it) => it.medicine.trim()).map((it) => ({ ...it, durationDays: Number(it.durationDays), instructions: it.instructions || null }));
        if (rxItems.length) await api(`/appointments/${appt.id}/prescriptions`, { method: "POST", body: { items: rxItems } });
        setOk("Saved. Prescription PDF ready." ); onSaved();
      } catch (ex) { setErr(ex.message); }
    }
    return html`<form onSubmit=${save}><h3>Consultation</h3>
      <div class="row"><div><label for="bp">BP</label><input id="bp" placeholder="120/80" value=${f.bp} onChange=${set("bp")} /></div>
        <div><label for="pu">Pulse</label><input id="pu" type="number" value=${f.pulse} onChange=${set("pulse")} /></div>
        <div><label for="tc">Temp °C</label><input id="tc" type="number" step="0.1" value=${f.tempC} onChange=${set("tempC")} /></div>
        <div><label for="wk">Weight kg</label><input id="wk" type="number" step="0.1" value=${f.weightKg} onChange=${set("weightKg")} /></div></div>
      <label for="sy">Symptoms</label><textarea id="sy" value=${f.symptoms} onChange=${set("symptoms")} required />
      <label for="dg">Diagnosis</label><input id="dg" value=${f.diagnosis} onChange=${set("diagnosis")} required />
      <label for="nt">Private notes</label><textarea id="nt" value=${f.notes} onChange=${set("notes")} />
      <h3>Prescription</h3>
      ${items.map((it, i) => html`<div class="row" key=${i}>
        <div><label>Medicine</label><input value=${it.medicine} onChange=${setItem(i, "medicine")} /></div>
        <div><label>Dosage</label><input value=${it.dosage} onChange=${setItem(i, "dosage")} /></div>
        <div><label>Frequency</label><input value=${it.frequency} onChange=${setItem(i, "frequency")} /></div>
        <div><label>Days</label><input type="number" min="1" value=${it.durationDays} onChange=${setItem(i, "durationDays")} /></div>
        <div><label>Instructions</label><input value=${it.instructions} onChange=${setItem(i, "instructions")} /></div></div>`)}
      <div class="actions"><button type="button" class="secondary" onClick=${() => setItems([...items, { medicine: "", dosage: "", frequency: "", durationDays: 5, instructions: "" }])}>Add medicine</button>
        <button type="submit">Save consultation</button></div><${Msg} error=${err} ok=${ok} /></form>`;
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
          ${open.status === "CHECKED_IN" && html`<${ConsultationForm} appt=${open} onSaved=${() => { list.reload(); setOpen({ ...open, status: "COMPLETED" }); }} />`}
          ${open.status === "BOOKED" && html`<p class="muted">Consultation notes open after the patient is checked in at the front desk.</p>`}`
        : html`<p class="muted">Open an appointment to see the chart.</p>`}</div></div>`;
  }

  HAP.registerPage({ id: "my-day", title: "My day", roles: ["DOCTOR"], order: 10, component: DoctorDay });
})();
