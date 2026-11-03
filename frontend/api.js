/* Small fetch wrapper. The JWT is kept in memory only (never localStorage) – SAD 3.4. */
(function () {
  let token = null;
  async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (token) headers["Authorization"] = "Bearer " + token;
    let body = options.body;
    if (body !== undefined && !(body instanceof FormData)) { headers["Content-Type"] = "application/json"; body = JSON.stringify(body); }
    const resp = await fetch("/api/v1" + path, { method: options.method || "GET", headers, body });
    if (resp.status === 204) return null;
    const type = resp.headers.get("content-type") || "";
    if (!resp.ok) {
      let err = { code: "ERROR", message: "Request failed (" + resp.status + ")" };
      if (type.includes("json")) { const data = await resp.json(); if (data.error) err = data.error; }
      const e = new Error(err.message); e.code = err.code; e.status = resp.status;
      if (resp.status === 401 && token) window.dispatchEvent(new Event("hap-logout"));
      throw e;
    }
    if (options.raw) return resp;
    return type.includes("json") ? resp.json() : resp.text();
  }
  async function download(path, filename) {
    const resp = await api(path, { raw: true });
    const url = URL.createObjectURL(await resp.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }
  window.HAPApi = { api, download, setToken: (t) => { token = t; } };
})();
