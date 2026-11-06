/* HAP-F-011 / F-012 / F-013: Receptionist registers walk-ins and searches patients (Raghav Budur). */
(function () {
  const { React, html, api, Msg } = HAP;
  const { useState } = React;

  function Reception() {
    const [q, setQ] = useState(""), [result, setResult] = useState(null);
    const [err, setErr] = useState(null), [ok, setOk] = useState(null), [dup, setDup] = useState(null);
    async function search(e) { e && e.preventDefault(); setErr(null); try { setResult(await api("/patients?q=" + encodeURIComponent(q))); } catch (ex) { setErr(ex.message); } }
    async function register(f, confirm = false) {
      setErr(null); setOk(null); setDup(null);
      try {
        const p = await api("/patients" + (confirm ? "?confirm=true" : ""), { method: "POST", body: HAP.cleanForm(f) });
        setOk(`Registered ${p.fullName} – MRN ${p.mrn}`);
      } catch (ex) { if (ex.code === "POSSIBLE_DUPLICATE") setDup({ f, message: ex.message }); else setErr(ex.message); }
    }
    return html`<div class="card"><h2>Find a patient</h2>
        <form onSubmit=${search} class="actions"><input aria-label="Name, MRN or phone" placeholder="Name, MRN or phone" value=${q} onChange=${(e) => setQ(e.target.value)} />
          <button type="submit">Search</button></form>
        ${result && html`<table><thead><tr><th>MRN</th><th>Name</th><th>DOB</th><th>Phone</th><th>Allergies</th></tr></thead><tbody>
          ${result.items.map((p) => html`<tr key=${p.id}><td>${p.mrn}</td><td>${p.fullName}</td><td>${p.dateOfBirth}</td><td>${p.phone}</td><td>${p.allergies || "—"}</td></tr>`)}
          </tbody></table><p class="muted">${result.total} found</p>`}
      </div>
      <div class="card"><h2>Register a walk-in patient</h2>
        <${Msg} error=${err} ok=${ok} />
        ${dup && html`<div class="msg error">${dup.message}<div class="actions"><button onClick=${() => register(dup.f, true)}>Create anyway</button>
          <button class="secondary" onClick=${() => setDup(null)}>Cancel</button></div></div>`}
        ${HAP.ProfileForm ? html`<${HAP.ProfileForm} initial=${{}} onSave=${(f) => register(f)} isNew=${true} />` : html`<p class="muted">Loading form…</p>`}
      </div>`;
  }

  HAP.registerPage({ id: "reception", title: "Patients", roles: ["RECEPTIONIST", "ADMIN"], order: 20, component: Reception });
})();
