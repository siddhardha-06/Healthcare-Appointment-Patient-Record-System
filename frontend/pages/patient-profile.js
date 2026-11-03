/* HAP-F-010 / F-011: patient creates and edits their own profile (Raghav Budur). */
(function () {
  const { React, html, api, Msg } = HAP;
  const { useState, useEffect } = React;
  const BLOOD = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

  function ProfileForm({ initial, onSave, isNew }) {
    const [f, setF] = useState(initial);
    const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
    return html`<form onSubmit=${(e) => { e.preventDefault(); onSave(f); }}>
      <div class="row">
        <div><label for="pn">Full name</label><input id="pn" value=${f.fullName || ""} onChange=${set("fullName")} required /></div>
        <div><label for="pd">Date of birth</label><input id="pd" type="date" value=${f.dateOfBirth || ""} onChange=${set("dateOfBirth")} required disabled=${!isNew} /></div>
        <div><label for="pg">Gender</label><select id="pg" value=${f.gender || ""} onChange=${set("gender")} required disabled=${!isNew}>
          <option value="">Choose…</option><option>Male</option><option>Female</option><option>Other</option></select></div>
        <div><label for="pp">Mobile (10 digits)</label><input id="pp" value=${f.phone || ""} onChange=${set("phone")} pattern="\\d{10}" required /></div>
        <div><label for="pb">Blood group</label><select id="pb" value=${f.bloodGroup || ""} onChange=${set("bloodGroup")}>${BLOOD.map((b) => html`<option key=${b} value=${b}>${b || "—"}</option>`)}</select></div>
        <div><label for="pe">Email</label><input id="pe" type="email" value=${f.email || ""} onChange=${set("email")} /></div>
      </div>
      <label for="pa">Address</label><input id="pa" value=${f.address || ""} onChange=${set("address")} />
      <label for="pl">Known allergies (comma separated)</label><input id="pl" value=${f.allergies || ""} onChange=${set("allergies")} />
      <div class="row">
        <div><label for="ecn">Emergency contact name</label><input id="ecn" value=${f.emergencyContactName || ""} onChange=${set("emergencyContactName")} /></div>
        <div><label for="ecp">Emergency contact phone</label><input id="ecp" value=${f.emergencyContactPhone || ""} onChange=${set("emergencyContactPhone")} pattern="\\d{10}" /></div>
      </div>
      <div class="actions"><button type="submit">${isNew ? "Create profile" : "Save changes"}</button></div>
    </form>`;
  }

  function clean(f) { const out = {}; for (const [k, v] of Object.entries(f)) if (v !== "" && v !== null) out[k] = v; return out; }

  function MyProfile({ user }) {
    const [profile, setProfile] = useState(undefined);
    const [err, setErr] = useState(null), [ok, setOk] = useState(null);
    useEffect(() => { api("/patients/me").then(setProfile, () => setProfile(null)); }, []);
    async function save(f) {
      setErr(null); setOk(null);
      try {
        if (profile) {
          const { mrn, dateOfBirth, gender, id, ...editable } = clean(f);
          setProfile(await api("/patients/me", { method: "PATCH", body: editable })); setOk("Saved.");
        } else {
          setProfile(await api("/patients/me", { method: "POST", body: clean(f) })); setOk("Profile created.");
        }
      } catch (e) { setErr(e.message); }
    }
    if (profile === undefined) return html`<div class="card">Loading…</div>`;
    return html`<div class="card"><h2>My profile</h2>
      ${profile ? html`<p>Patient ID (MRN): <b>${profile.mrn}</b></p>` : html`<p>Please complete your profile before booking.</p>`}
      <${Msg} error=${err} ok=${ok} />
      <${ProfileForm} key=${profile ? profile.mrn : "new"} initial=${profile || { fullName: user.fullName, phone: user.phone || "" }} onSave=${save} isNew=${!profile} />
    </div>`;
  }

  HAP.ProfileForm = ProfileForm;
  HAP.cleanForm = clean;
  HAP.registerPage({ id: "profile", title: "My profile", roles: ["PATIENT"], order: 10, component: MyProfile });
})();
