# TCM Clinic 前端接入指南（适配版）

本项目已提供一套“可直接复用”的前端适配代码：
- `apps/web/index.html`：页面与交互入口
- `apps/web/tcm_api.js`（兼容保留 `tcm-api.js`）：前端 API 适配层（统一封装接口）
- `apps/web/main.js`：业务交互逻辑示例

---

## 1. 后端启动

```bash
pip install -r requirements.txt
cp .env.example .env
python -m apps.api_server
```

启动后：
- Swagger: `http://127.0.0.1:8000/docs`
- 内置前端 Demo: `http://127.0.0.1:8000/`

---

## 2. 前端适配思路

推荐你在真实前端项目（Vue/React/小程序）中照搬 `tcm_api.js` 的模式：

1. **单独封装 API Client**（不要把 fetch 分散在页面里）
2. 统一维护 `baseURL`（dev/prod 切换简单）
3. 统一处理错误（`res.ok` 判定 + 错误文本抛出）
4. 页面只管业务流程：问诊、复诊、导出、病例读取

---

## 3. 现成的适配代码（可复制到你的项目）

### 3.1 API 适配层（核心）

```js
class TCMClinicClient {
  constructor(baseURL) { this.baseURL = (baseURL || "").replace(/\/+$/, ""); }

  async request(path, { method = "GET", body } = {}) {
    const res = await fetch(`${this.baseURL}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return await res.json();
  }

  health() { return this.request("/health"); }
  chat({ message, caseId, stage = "initial" }) {
    return this.request("/chat", {
      method: "POST",
      body: { message, case_id: caseId || null, stage },
    });
  }
  startRevisit(lastCaseId) {
    return this.request(`/revisit/start?last_case_id=${encodeURIComponent(lastCaseId)}`, { method: "POST" });
  }
  listCases() { return this.request("/cases"); }
  getCase(caseId) { return this.request(`/case/${encodeURIComponent(caseId)}`); }
  exportCase(caseId, fmt = "pdf") {
    return this.request(`/export/${encodeURIComponent(caseId)}?fmt=${encodeURIComponent(fmt)}`, { method: "POST" });
  }
}
```

### 3.2 页面业务最小调用方式

```js
const client = new TCMClinicClient("http://127.0.0.1:8000");

// 首次问诊
const r1 = await client.chat({
  message: "最近夜里咳嗽，咽干，容易疲劳",
  caseId: null,
  stage: "initial",
});

// 后续追问
const r2 = await client.chat({
  message: "大便偏干，睡眠一般",
  caseId: r1.case_id,
  stage: "initial",
});

// 导出
await client.exportCase(r1.case_id, "pdf");
```

---

## 4. 接口清单（给前端联调）

- `GET /health`：健康检查
- `POST /chat`：问诊主入口
- `POST /revisit/start?last_case_id=...`：启动复诊
- `GET /cases`：病例列表
- `GET /case/{case_id}`：病例详情
- `POST /export/{case_id}?fmt=pdf|docx`：导出病例

`POST /chat` 请求体：

```json
{
  "message": "最近夜里咳嗽，咽干",
  "case_id": null,
  "stage": "initial"
}
```

---

## 5. 常见问题

1. **CORS 报错**
   - 在 `.env` 中配置：
   - `CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
   - 重启后端。

2. **没有 case_id**
   - 首轮问诊 `case_id` 为空是正常的，后端响应会返回新的 `case_id`。

3. **复诊流程怎么走**
   - 先输入上次病例 ID 调用 `/revisit/start`，拿到新 `case_id` 后继续用 `stage=revisit` 调 `/chat`。

4. **导出失败**
   - 确认 `case_id` 存在（先调 `GET /case/{case_id}`）。


5. **脚本 404（tcm-api.js / tcm_api.js）**
   - 当前前端默认引用：`/web/tcm_api.js`。
   - 为兼容旧版本，也保留了：`/web/tcm-api.js`。
   - 若你在 PowerShell 用 `curl`，它是 `Invoke-WebRequest` 别名；建议用：`curl.exe http://127.0.0.1:8000/web/tcm_api.js`。
