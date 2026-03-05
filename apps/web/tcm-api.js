class TCMClinicClient {
  constructor(baseURL) {
    this.baseURL = (baseURL || "").replace(/\/+$/, "");
  }

  setBaseURL(url) {
    this.baseURL = (url || "").replace(/\/+$/, "");
  }

  async request(path, { method = "GET", body } = {}) {
    const res = await fetch(`${this.baseURL}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${text}`);
    }

    return await res.json();
  }

  health() {
    return this.request("/health");
  }

  chat({ message, caseId, stage = "initial" }) {
    return this.request("/chat", {
      method: "POST",
      body: { message, case_id: caseId || null, stage },
    });
  }

  startRevisit(lastCaseId) {
    return this.request(`/revisit/start?last_case_id=${encodeURIComponent(lastCaseId)}`, {
      method: "POST",
    });
  }

  listCases() {
    return this.request("/cases");
  }

  getCase(caseId) {
    return this.request(`/case/${encodeURIComponent(caseId)}`);
  }

  exportCase(caseId, fmt = "pdf") {
    return this.request(`/export/${encodeURIComponent(caseId)}?fmt=${encodeURIComponent(fmt)}`, {
      method: "POST",
    });
  }
}

window.TCMClinicClient = TCMClinicClient;
