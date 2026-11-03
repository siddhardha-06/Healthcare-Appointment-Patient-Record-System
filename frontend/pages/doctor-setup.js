/* HAP-F-020 / F-021 / F-022: doctor profiles (Admin), weekly availability and leave (Doctor) – Raghav Budur. */
(function () {
  const { React, html, api, Msg, useAsync } = HAP;
  const { useState, useEffect } = React;
  const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  function Availability() {
    const [rows, setRows] = useState([]), [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const [leave, setLeave] = useState(HAP.today(1));
    useEffect(() => { api("/doctors/me/availability").then((r) => setRows(r.map((x) => ({ ...x, startTime: x.startTime.slice(0, 5), endTime: x.endTime.slice(0, 5) }))), (e) => setErr(e.message)); }, []);
    const upd = (i, k) => (e) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: k === "weekday" ? Number(e.target.value) : e.target.value } : r)));
    async function save() { setErr(null); setOk(null); try { await api("/doctors/me/availability", { method: "PUT", body: rows }); setOk("Saved. Slots for the next 30 days were updated."); } catch (e) { setErr(e.message); } }
    async function markLeave() { setErr(null); setOk(null); try { const r = await api("/doctors/me/leave", { method: "POST", body: { day: leave } }); setOk(`Leave saved: ${r.blockedSlots} slots blocked. Booked patients were notified.`); } catch (e) { setErr(e.message); } }
    return html`<div class="card"><h2>Weekly availability</h2><${Msg} error=${err} ok=${ok} />
        <table><thead><tr><th>Day</th><th>From</th><th>To</th><th></th></tr></thead><tbody>
        ${rows.map((r, i) => html`<tr key=${i}><td><select aria-label="Day" value=${r.weekday} onChange=${upd(i, "weekday")}>${DAYS.map((d, n) => html`<option key=${n} value=${n}>${d}</option>`)}</select></td>
          <td><input aria-label="From" type="time" value=${r.startTime} onChange=${upd(i, "startTime")} /></td>
          <td><input aria-label="To" type="time" value=${r.endTime} onChange=${upd(i, "endTime")} /></td>
          <td><button class="danger" onClick=${() => setRows(rows.filter((_, j) => j !== i))}>Remove</button></td></tr>`)}
        </tbody></table>
        <div class="actions"><button class="secondary" onClick=${() => setRows([...rows, { weekday: 0, startTime: "09:00", endTime: "12:00" }])}>Add time range</button>
          <button onClick=${save}>Save availability</button></div></div>
      <div class="card"><h2>Mark leave</h2><label for="lv">Date</label><input id="lv" type="date" value=${leave} onChange=${(e) => setLeave(e.target.value)} />
        <div class="actions"><button class="danger" onClick=${markLeave}>Mark whole day as leave</button></div></div>`;
  }

  function DoctorProfiles() {
    const doctors = useAsync(() => api("/doctors"), []);
    const accounts = useAsync(() => api("/admin/users?role=DOCTOR"), []);
    const [f, setF] = useState({ userId: "", name: "", specialization: "", department: "", qualification: "", slotMinutes: 15 });
    const [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
    const linked = new Set((doctors.data || []).map((d) => d.userId));
    async function create(e) {
      e.preventDefault(); setErr(null); setOk(null);
      try { await api("/doctors", { method: "POST", body: { ...f, userId: Number(f.userId), slotMinutes: Number(f.slotMinutes) } }); setOk("Doctor profile created."); doctors.reload(); }
      catch (ex) { setErr(ex.message); }
    }
    return html`<div class="card"><h2>Doctors</h2>
        <table><thead><tr><th>Name</th><th>Specialization</th><th>Department</th><th>Slot</th></tr></thead><tbody>
        ${(doctors.data || []).map((d) => html`<tr key=${d.id}><td>${d.name}</td><td>${d.specialization}</td><td>${d.department}</td><td>${d.slotMinutes} min</td></tr>`)}
        </tbody></table></div>
      <div class="card"><h2>Add a doctor profile</h2><p class="muted">First create the Doctor login under Admin → Staff.</p>
        <${Msg} error=${err} ok=${ok} />
        <form onSubmit=${create}><div class="row">
          <div><label for="du">Doctor account</label><select id="du" value=${f.userId} onChange=${set("userId")} required><option value="">Choose…</option>
            ${(accounts.data || []).filter((u) => !linked.has(u.id)).map((u) => html`<option key=${u.id} value=${u.id}>${u.fullName} (${u.email})</option>`)}</select></div>
          <div><label for="dn">Display name</label><input id="dn" value=${f.name} onChange=${set("name")} required /></div>
          <div><label for="ds">Specialization</label><input id="ds" value=${f.specialization} onChange=${set("specialization")} required /></div>
          <div><label for="dd">Department</label><input id="dd" value=${f.department} onChange=${set("department")} required /></div>
          <div><label for="dq">Qualification</label><input id="dq" value=${f.qualification} onChange=${set("qualification")} required /></div>
          <div><label for="dm">Slot length</label><select id="dm" value=${f.slotMinutes} onChange=${set("slotMinutes")}>${[10, 15, 20, 30].map((m) => html`<option key=${m} value=${m}>${m} min</option>`)}</select></div>
        </div><div class="actions"><button type="submit">Create profile</button></div></form></div>`;
  }

  HAP.registerPage({ id: "availability", title: "My availability", roles: ["DOCTOR"], order: 40, component: Availability });
  HAP.registerPage({ id: "doctors", title: "Doctors", roles: ["ADMIN"], order: 30, component: DoctorProfiles });
})();
