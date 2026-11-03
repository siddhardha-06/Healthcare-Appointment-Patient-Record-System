/* App shell: login/register, role-based navigation and a page registry.
   Each feature page lives in pages/<name>.js and calls HAP.registerPage({...}). */
(function () {
  const { useState, useEffect, useCallback } = React;
  const html = htm.bind(React.createElement);
  const { api, download, setToken } = window.HAPApi;
  const PAGES = ["patient-profile", "reception", "doctor-setup", "booking", "front-desk", "doctor-day",
                 "my-records", "notifications", "admin"];
  const registry = [];
  let rerender = () => {};

  function registerPage(page) { registry.push(page); registry.sort((a, b) => (a.order || 50) - (b.order || 50)); rerender(); }
  function fmt(dt) { return new Date(dt).toLocaleString([], { weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }); }
  function time(dt) { return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
  function today(offset = 0) { const d = new Date(); d.setDate(d.getDate() + offset); return d.toISOString().slice(0, 10); }

  function Msg({ error, ok }) {
    if (error) return html`<div class="msg error" role="alert">${error}</div>`;
    if (ok) return html`<div class="msg ok" role="status">${ok}</div>`;
    return null;
  }

  /* useAsync(fn) -> {data, error, reload} */
  function useAsync(fn, deps) {
    const [state, setState] = useState({ data: null, error: null });
    const reload = useCallback(() => { fn().then((data) => setState({ data, error: null }), (e) => setState({ data: null, error: e.message })); }, deps);
    useEffect(reload, [reload]);
    return { ...state, reload };
  }

  function Login({ onLogin }) {
    const [mode, setMode] = useState("login");
    const [f, setF] = useState({ email: "", password: "", fullName: "", phone: "" });
    const [err, setErr] = useState(null), [ok, setOk] = useState(null);
    const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
    async function submit(e) {
      e.preventDefault(); setErr(null); setOk(null);
      try {
        if (mode === "register") {
          await api("/auth/register", { method: "POST", body: { email: f.email, password: f.password, fullName: f.fullName, phone: f.phone || null } });
          setOk("Account created. You can log in now."); setMode("login"); return;
        }
        const t = await api("/auth/login", { method: "POST", body: { email: f.email, password: f.password } });
        setToken(t.accessToken);
        onLogin(await api("/auth/me"));
      } catch (ex) { setErr(ex.message); }
    }
    return html`<div class="center card">
      <h2>${mode === "login" ? "Log in" : "Create a patient account"}</h2>
      <form onSubmit=${submit}>
        ${mode === "register" && html`<label for="fn">Full name</label><input id="fn" value=${f.fullName} onChange=${set("fullName")} required />
          <label for="ph">Mobile (10 digits)</label><input id="ph" value=${f.phone} onChange=${set("phone")} pattern="\\d{10}" />`}
        <label for="em">Email</label><input id="em" type="email" value=${f.email} onChange=${set("email")} required autocomplete="username" />
        <label for="pw">Password</label><input id="pw" type="password" value=${f.password} onChange=${set("password")} required autocomplete=${mode === "login" ? "current-password" : "new-password"} />
        ${mode === "register" && html`<div class="muted">At least 8 characters with a letter and a digit.</div>`}
        <${Msg} error=${err} ok=${ok} />
        <div class="actions"><button type="submit">${mode === "login" ? "Log in" : "Create account"}</button>
          <button type="button" class="secondary" onClick=${() => { setMode(mode === "login" ? "register" : "login"); setErr(null); }}>
            ${mode === "login" ? "New patient? Register" : "Back to log in"}</button></div>
      </form></div>`;
  }

  function Home({ user }) {
    return html`<div class="card"><h2>Welcome, ${user.fullName}</h2>
      <p>You are logged in as <b>${user.role.toLowerCase()}</b>. Use the menu above.</p></div>`;
  }

  function App() {
    const [, force] = useState(0);
    const [user, setUser] = useState(null);
    const [route, setRoute] = useState(location.hash.slice(1) || "home");
    useEffect(() => { rerender = () => force((n) => n + 1); }, []);
    useEffect(() => { const h = () => setRoute(location.hash.slice(1) || "home"); addEventListener("hashchange", h); return () => removeEventListener("hashchange", h); }, []);
    useEffect(() => { const out = () => { setToken(null); setUser(null); }; addEventListener("hap-logout", out); return () => removeEventListener("hap-logout", out); }, []);
    if (!user) return html`<header><h1>HAP Clinic</h1></header><main><${Login} onLogin=${setUser} /></main>`;
    const pages = registry.filter((p) => p.roles.includes(user.role));
    const page = pages.find((p) => p.id === route) || (route === "home" ? pages[0] : null);
    return html`
      <header><h1>HAP Clinic</h1>
        <nav aria-label="Main">${pages.map((p) => html`<a key=${p.id} href=${"#" + p.id} class=${page && p.id === page.id ? "active" : ""}>${p.title}</a>`)}</nav>
        <span class="who">${user.fullName} · ${user.role.toLowerCase()}</span>
        <button class="secondary" onClick=${() => { setToken(null); setUser(null); location.hash = ""; }}>Log out</button>
      </header>
      <main>${page ? html`<${page.component} user=${user} />` : html`<${Home} user=${user} />`}</main>`;
  }

  window.HAP = { React, html, api, download, registerPage, Msg, useAsync, fmt, time, today };
  for (const name of PAGES) {                     // pages added in later sprints simply appear when present
    const s = document.createElement("script");
    s.src = "pages/" + name + ".js"; s.onerror = () => console.info("page not installed yet:", name);
    document.body.appendChild(s);
  }
  ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
})();
