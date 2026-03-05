const caseIdInput = document.getElementById("caseId");
const messageInput = document.getElementById("message");
const stageSelect = document.getElementById("stage");
const chatLog = document.getElementById("chatLog");

function appendMessage(role, text, extra = "") {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<strong>${role === "user" ? "患者" : "系统"}：</strong>${text}<div class="meta">${extra}</div>`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status} ${err}`);
  }
  return res.json();
}

document.getElementById("sendBtn").addEventListener("click", async () => {
  const message = messageInput.value.trim();
  if (!message) {
    alert("请输入消息");
    return;
  }
  appendMessage("user", message);
  try {
    const data = await api("/chat", "POST", {
      message,
      case_id: caseIdInput.value.trim() || null,
      stage: stageSelect.value,
    });
    caseIdInput.value = data.case_id;
    appendMessage(
      "bot",
      data.message,
      `state=${data.state} | next=${(data.next_questions || []).join("；")}`
    );
    messageInput.value = "";
  } catch (e) {
    appendMessage("bot", `调用失败：${e.message}`);
  }
});

document.getElementById("loadCasesBtn").addEventListener("click", async () => {
  try {
    const data = await api("/cases");
    const ids = (data.cases || []).map((x) => x.case_id || x.id || "unknown");
    appendMessage("bot", `病例列表：${ids.join(", ") || "暂无"}`);
  } catch (e) {
    appendMessage("bot", `读取病例失败：${e.message}`);
  }
});

async function exportCase(fmt) {
  const caseId = caseIdInput.value.trim();
  if (!caseId) {
    alert("请先产生或输入 case_id");
    return;
  }
  try {
    const data = await api(`/export/${caseId}?fmt=${fmt}`, "POST");
    appendMessage("bot", `导出成功(${fmt})：${data.path}`);
  } catch (e) {
    appendMessage("bot", `导出失败：${e.message}`);
  }
}

document.getElementById("exportPdfBtn").addEventListener("click", () => exportCase("pdf"));
document.getElementById("exportDocxBtn").addEventListener("click", () => exportCase("docx"));
