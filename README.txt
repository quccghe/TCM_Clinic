# TCM Clinic 系统前后端接入说明

本文档提供一个可直接运行的前端接入方案：
- 后端：FastAPI (`apps/api_server.py`)
- 前端示例：原生 HTML/JS (`apps/web/index.html` + `apps/web/main.js`)

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

复制并编辑环境变量：

```bash
cp .env.example .env
```

关键项：
- `APP_HOST` / `APP_PORT`：后端服务地址
- `CORS_ALLOW_ORIGINS`：允许跨域的前端域名，多个值用逗号分隔；开发期可用 `*`
- `OPENAI_API_KEY`：替换为你自己的 Key

## 3. 启动服务

```bash
python -m apps.api_server
```

启动后访问：
- API 文档：`http://127.0.0.1:8000/docs`
- 前端示例：`http://127.0.0.1:8000/`

## 4. 前端如何接入（两种方式）

### 方式 A：直接复用内置 demo

`apps/web` 已包含一个最小可用页面：
- 填写主诉后点击“发送问诊”会调用 `/chat`
- 自动维护 `case_id`
- 支持读取 `/cases`
- 支持 `/export/{case_id}` 导出 PDF/DOCX

### 方式 B：你的独立前端项目（Vue/React/小程序/H5）

只需对接以下接口：

1) 问诊主接口：
- `POST /chat`
- body:

```json
{
  "message": "最近夜里咳嗽，咽干",
  "case_id": null,
  "stage": "initial"
}
```

2) 续诊起始：
- `POST /revisit/start?last_case_id=<case_id>`

3) 读取病例：
- `GET /case/{case_id}`

4) 列出病例：
- `GET /cases`

5) 导出病历：
- `POST /export/{case_id}?fmt=pdf` 或 `fmt=docx`

## 5. 典型前端调用代码（可直接粘贴）

```js
async function chatWithBackend({ message, caseId, stage = "initial" }) {
  const res = await fetch("http://127.0.0.1:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      case_id: caseId || null,
      stage,
    }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return await res.json();
}
```

## 6. 常见问题

1) **跨域报错（CORS）**
- 在 `.env` 中设置：
  - `CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
- 重启后端生效。

2) **首轮没有 case_id**
- 这是正常的，后端会自动创建并在响应里返回 `case_id`。

3) **导出失败**
- 先确认该 `case_id` 已存在（可调用 `/case/{case_id}` 验证）。
