/* HAP-F-030 … F-033: find a doctor, pick a free slot, book; see, reschedule and cancel (Prithviraj K). */
(function () {
  const { React, html, api, Msg, useAsync, fmt, time, today } = HAP;
  const { useState, useEffect } = React;

  function SlotPicker({ doctorId, day, onPick, picked }) {
    const [slots, setSlots] = useState(null), [err, setErr] = useState(null);
    useEffect(() => { setSlots(null); setErr(null); if (doctorId && day) api(`/slots?doctorId=${doctorId}&date=${day}`).then((r) => setSlots(r.slots), (e) => setErr(e.message)); }, [doctorId, day]);
    if (err) return html`<${Msg} error=${err} />`;
    if (!slots) return html`<p class="muted">Loading free times…</p>`;
    if (!slots.length) return html`<p class="muted">No free times on this day. Try another date.</p>`;
    return html`<div class="legend">Free times (tap to choose):</div><div class="slots">
      ${slots.map((s) => html`<button key=${s.slotId} type="button" class=${"slot free" + (picked && picked.slotId === s.slotId ? " picked" : "")}
        aria-pressed=${picked && picked.slotId === s.slotId} onClick=${() => onPick(s)}>${time(s.start)}</button>`)}</div>`;
  }

  function Book({ onBooked }) {
    const [spec, setSpec] = useState(""), [doctorId, setDoctorId] = useState(""), [day, setDay] = useState(today(1));
    const [picked, setPicked] = useState(null), [reason, setReason] = useState("");
    const [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const doctors = useAsync(() => api("/doctors" + (spec ? "?specialization=" + encodeURIComponent(spec) : "")), [spec]);
    const all = useAsync(() => api("/doctors"), []);
    const specs = [...new Set((all.data || []).map((d) => d.specialization))];
    async function confirm() {
      setErr(null); setOk(null);
      try { const a = await api("/appointments", { method: "POST", body: { slotId: picked.slotId, reason } });
        setOk(`Booked: ${a.doctorName}, ${fmt(a.start)}. A confirmation has been sent.`); setPicked(null); setReason(""); onBooked && onBooked(); }
      catch (e) { setErr(e.code === "SLOT_TAKEN" ? "Someone just booked this time. Please pick another slot." : e.message); setPicked(null); }
    }
    return html`<div class="card"><h2>Book an appointment</h2>
      <div class="row">
        <div><label for="sp">Specialization</label><select id="sp" value=${spec} onChange=${(e) => { setSpec(e.target.value); setDoctorId(""); }}>
          <option value="">All</option>${specs.map((s) => html`<option key=${s}>${s}</option>`)}</select></div>
        <div><label for="dr">Doctor</label><select id="dr" value=${doctorId} onChange=${(e) => { setDoctorId(e.target.value); setPicked(null); }}>
          <option value="">Choose a doctor…</option>${(doctors.data || []).map((d) => html`<option key=${d.id} value=${d.id}>${d.name} – ${d.specialization}</option>`)}</select></div>
        <div><label for="dy">Date</label><input id="dy" type="date" min=${today()} max=${today(30)} value=${day} onChange=${(e) => { setDay(e.target.value); setPicked(null); }} /></div>
      </div>
      ${doctorId && html`<${SlotPicker} doctorId=${doctorId} day=${day} picked=${picked} onPick=${setPicked} />`}
      ${picked && html`<label for="rs">Reason for visit</label><textarea id="rs" value=${reason} onChange=${(e) => setReason(e.target.value)} />
        <div class="actions"><button disabled=${reason.trim().length < 5} onClick=${confirm}>Book ${time(picked.start)}</button></div>`}
      <${Msg} error=${err} ok=${ok} /></div>`;
  }

  function Reschedule({ appt, onDone }) {
    const [day, setDay] = useState(appt.start.slice(0, 10)), [picked, setPicked] = useState(null), [err, setErr] = useState(null);
    async function save() {
      try { await api(`/appointments/${appt.id}/reschedule`, { method: "PATCH", body: { newSlotId: picked.slotId } }); onDone(); }
      catch (e) { setErr(e.message); }
    }
    return html`<div class="card"><h3>Move appointment with ${appt.doctorName}</h3>
      <label for="rd">New date</label><input id="rd" type="date" min=${today()} max=${today(30)} value=${day} onChange=${(e) => { setDay(e.target.value); setPicked(null); }} />
      <${SlotPicker} doctorId=${appt.doctorId} day=${day} picked=${picked} onPick=${setPicked} />
      <${Msg} error=${err} />
      <div class="actions"><button disabled=${!picked} onClick=${save}>Move here</button><button class="secondary" onClick=${() => onDone()}>Close</button></div></div>`;
  }

  function MyAppointments({ version }) {
    const list = useAsync(() => api("/appointments"), [version]);
    const [err, setErr] = useState(null), [moving, setMoving] = useState(null);
    async function cancel(a) { setErr(null); if (!confirm("Cancel this appointment?")) return; try { await api("/appointments/" + a.id, { method: "DELETE" }); list.reload(); } catch (e) { setErr(e.message); } }
    const items = (list.data && list.data.items) || [];
    return html`<div class="card"><h2>My appointments</h2><${Msg} error=${err || list.error} />
      ${items.length === 0 ? html`<p class="muted">No appointments yet.</p>` : html`<table><thead><tr><th>When</th><th>Doctor</th><th>Status</th><th></th></tr></thead><tbody>
        ${items.map((a) => html`<tr key=${a.id}><td>${fmt(a.start)}${a.needsReschedule ? html` <span class="chip CANCELLED">doctor on leave – please move</span>` : ""}</td>
          <td>${a.doctorName}</td><td><span class=${"chip " + a.status}>${a.status}</span></td>
          <td>${a.status === "BOOKED" && html`<div class="actions"><button class="secondary" onClick=${() => setMoving(a)}>Reschedule</button>
            <button class="danger" onClick=${() => cancel(a)}>Cancel</button></div>`}</td></tr>`)}</tbody></table>
        <p class="muted">Changes are possible up to 2 hours before the start time.</p>`}</div>
      ${moving && html`<${Reschedule} appt=${moving} onDone=${() => { setMoving(null); list.reload(); }} />`}`;
  }

  function BookingPage() {
    const [version, setVersion] = useState(0);
    return html`<${Book} onBooked=${() => setVersion(version + 1)} /><${MyAppointments} version=${version} />`;
  }

  HAP.SlotPicker = SlotPicker;
  HAP.registerPage({ id: "book", title: "Appointments", roles: ["PATIENT"], order: 20, component: BookingPage });
})();
