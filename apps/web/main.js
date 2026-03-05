const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const caseIdInput = document.getElementById("caseId");
const lastCaseIdInput = document.getElementById("lastCaseId");
const messageInput = document.getElementById("message");
const stageSelect = document.getElementById("stage");
const chatLog = document.getElementById("chatLog");
const statusEl = document.getElementById("status");

const client = new TCMClinicClient(apiBaseUrlInput.value.trim());

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.style.color = isError ? "#b91c1c" : "#0f766e";
}

function appendMessage(role, text, extra = "") {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `<strong>${role === "user" ? "患者" : "系统"}：</strong>${text}<div class="meta">${extra}</div>`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function updateBaseURL() {
  client.setBaseURL(apiBaseUrlInput.value.trim());
}

apiBaseUrlInput.addEventListener("change", updateBaseURL);

document.getElementById("healthBtn").addEventListener("click", async () => {
  updateBaseURL();
  try {
    const data = await client.health();
    setStatus(`连接成功: ${JSON.stringify(data)}`);
  } catch (e) {
    setStatus(`连接失败: ${e.message}`, true);
  }
});

document.getElementById("sendBtn").addEventListener("click", async () => {
  updateBaseURL();
  const message = messageInput.value.trim();
  if (!message) {
    alert("请输入消息");
    return;
  }

  appendMessage("user", message);

  try {
    const data = await client.chat({
      message,
      caseId: caseIdInput.value.trim(),
      stage: stageSelect.value,
    });

    caseIdInput.value = data.case_id;
    appendMessage(
      "bot",
      data.message,
      `state=${data.state} | risk=${data?.risk?.level || "none"} | next=${(data.next_questions || []).join("；")}`
    );

    messageInput.value = "";
  } catch (e) {
    appendMessage("bot", `调用失败：${e.message}`);
  }
});

document.getElementById("loadCasesBtn").addEventListener("click", async () => {
  updateBaseURL();
  try {
    const data = await client.listCases();
    const ids = (data.cases || []).map((x) => x.case_id || "unknown");
    appendMessage("bot", `病例列表（最近）: ${ids.join(", ") || "暂无"}`);
  } catch (e) {
    appendMessage("bot", `读取病例失败：${e.message}`);
  }
});

document.getElementById("loadCaseBtn").addEventListener("click", async () => {
  updateBaseURL();
  const caseId = caseIdInput.value.trim();
  if (!caseId) {
    alert("请先填写 case_id");
    return;
  }
  try {
    const data = await client.getCase(caseId);
    appendMessage("bot", `病例详情: ${caseId}`, `stage=${data.stage} | state=${data.state}`);
  } catch (e) {
    appendMessage("bot", `读取病例详情失败：${e.message}`);
  }
});

document.getElementById("startRevisitBtn").addEventListener("click", async () => {
  updateBaseURL();
  const lastCaseId = lastCaseIdInput.value.trim();
  if (!lastCaseId) {
    alert("请填写上次 case_id");
    return;
  }
  try {
    const data = await client.startRevisit(lastCaseId);
    caseIdInput.value = data.case_id;
    stageSelect.value = "revisit";
    appendMessage("bot", `复诊已启动，新 case_id=${data.case_id}`, `state=${data.state}`);
  } catch (e) {
    appendMessage("bot", `启动复诊失败：${e.message}`);
  }
});

async function exportCase(fmt) {
  updateBaseURL();
  const caseId = caseIdInput.value.trim();
  if (!caseId) {
    alert("请先产生或输入 case_id");
    return;
  }

  try {
    const data = await client.exportCase(caseId, fmt);
    appendMessage("bot", `导出成功(${fmt})`, `path=${data.path}`);
  } catch (e) {
    appendMessage("bot", `导出失败：${e.message}`);
  }
}

document.getElementById("exportPdfBtn").addEventListener("click", () => exportCase("pdf"));
document.getElementById("exportDocxBtn").addEventListener("click", () => exportCase("docx"));
