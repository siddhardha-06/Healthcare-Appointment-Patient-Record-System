/* HAP-F-034 / F-035: today's arrivals, check-in, and booking on behalf of a patient (Prithviraj K). */
(function () {
  const { React, html, api, Msg, useAsync, fmt, time, today } = HAP;
  const { useState } = React;

  function Arrivals() {
    const [day, setDay] = useState(today());
    const list = useAsync(() => api("/appointments?date=" + day), [day]);
    const flagged = useAsync(() => api("/appointments?needsReschedule=true&status=BOOKED"), []);
    const [err, setErr] = useState(null);
    async function setStatus(a, status) { setErr(null); try { await api(`/appointments/${a.id}/status`, { method: "PATCH", body: { status } }); list.reload(); } catch (e) { setErr(e.message); } }
    async function cancel(a) { setErr(null); try { await api("/appointments/" + a.id, { method: "DELETE" }); list.reload(); flagged.reload(); } catch (e) { setErr(e.message); } }
    const items = (list.data && list.data.items) || [];
    return html`<div class="card"><h2>Arrivals</h2>
        <label for="ad">Date</label><input id="ad" type="date" value=${day} onChange=${(e) => setDay(e.target.value)} />
        <${Msg} error=${err || list.error} />
        <table><thead><tr><th>Time</th><th>Patient</th><th>Doctor</th><th>Status</th><th></th></tr></thead><tbody>
        ${items.map((a) => html`<tr key=${a.id}><td>${time(a.start)}</td><td>${a.patientName}<div class="muted">${a.patientMrn}</div></td>
          <td>${a.doctorName}</td><td><span class=${"chip " + a.status}>${a.status}</span></td>
          <td>${a.status === "BOOKED" && html`<div class="actions"><button onClick=${() => setStatus(a, "CHECKED_IN")}>Check in</button>
            <button class="secondary" onClick=${() => setStatus(a, "NO_SHOW")}>No-show</button><button class="danger" onClick=${() => cancel(a)}>Cancel</button></div>`}</td></tr>`)}
        </tbody></table>${items.length === 0 && html`<p class="muted">No appointments on this day.</p>`}</div>
      ${flagged.data && flagged.data.items.length > 0 && html`<div class="card"><h2>Need rescheduling (doctor on leave)</h2><table><tbody>
        ${flagged.data.items.map((a) => html`<tr key=${a.id}><td>${fmt(a.start)}</td><td>${a.patientName} (${a.patientMrn})</td><td>${a.doctorName}</td></tr>`)}</tbody></table></div>`}`;
  }

  function BookForPatient() {
    const [q, setQ] = useState(""), [patients, setPatients] = useState([]), [patient, setPatient] = useState(null);
    const [doctorId, setDoctorId] = useState(""), [day, setDay] = useState(today()), [picked, setPicked] = useState(null);
    const [reason, setReason] = useState(""), [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const doctors = useAsync(() => api("/doctors"), []);
    async function search(e) { e.preventDefault(); try { setPatients((await api("/patients?q=" + encodeURIComponent(q))).items); } catch (ex) { setErr(ex.message); } }
    async function book() {
      setErr(null); setOk(null);
      try { const a = await api("/appointments", { method: "POST", body: { slotId: picked.slotId, reason, patientId: patient.id } });
        setOk(`Booked ${a.patientName} with ${a.doctorName} at ${fmt(a.start)}.`); setPicked(null); }
      catch (e) { setErr(e.message); setPicked(null); }
    }
    return html`<div class="card"><h2>Book for a patient</h2>
      <form onSubmit=${search} class="actions"><input aria-label="Find patient" placeholder="Name, MRN or phone" value=${q} onChange=${(e) => setQ(e.target.value)} /><button type="submit">Find</button></form>
      ${patients.length > 0 && html`<label for="pk">Patient</label><select id="pk" onChange=${(e) => setPatient(patients.find((p) => p.id === Number(e.target.value)))}>
        <option value="">Choose…</option>${patients.map((p) => html`<option key=${p.id} value=${p.id}>${p.fullName} – ${p.mrn}</option>`)}</select>`}
      ${patient && html`<div class="row"><div><label for="bd">Doctor</label><select id="bd" value=${doctorId} onChange=${(e) => { setDoctorId(e.target.value); setPicked(null); }}>
          <option value="">Choose…</option>${(doctors.data || []).map((d) => html`<option key=${d.id} value=${d.id}>${d.name} – ${d.specialization}</option>`)}</select></div>
        <div><label for="bdy">Date</label><input id="bdy" type="date" value=${day} onChange=${(e) => { setDay(e.target.value); setPicked(null); }} /></div></div>
        ${doctorId && HAP.SlotPicker && html`<${HAP.SlotPicker} doctorId=${doctorId} day=${day} picked=${picked} onPick=${setPicked} />`}
        ${doctorId && !HAP.SlotPicker && html`<p class="muted">Slot picker not loaded.</p>`}
        ${picked && html`<label for="br">Reason</label><input id="br" value=${reason} onChange=${(e) => setReason(e.target.value)} />
          <div class="actions"><button disabled=${reason.trim().length < 5} onClick=${book}>Book ${time(picked.start)}</button></div>`}`}
      <${Msg} error=${err} ok=${ok} /></div>`;
  }

  HAP.registerPage({ id: "front-desk", title: "Front desk", roles: ["RECEPTIONIST"], order: 10,
                     component: () => html`<${Arrivals} /><${BookForPatient} />` });
})();
