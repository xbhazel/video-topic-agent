# 短视频选题 Agent（MVP → 双人云端版）

验证这一条流程好不好用：
**输入生活事件 → AI判断 → 保存 → 以后可以查看**，现在支持你和家人在不同地方共用同一份数据。

## 项目结构

```
短视频选题Agent/
├── app.py                        # 网页入口（Streamlit）+ 密码门
├── ai.py                         # 调用AI、解析AI返回结果
├── db.py                         # 数据库读写（Postgres / Supabase）
├── config.py                     # 统一读配置：本地读 .env，云端读 st.secrets
├── requirements.txt              # Python依赖
├── .env.example                  # 本地开发配置模板（复制成 .env 使用）
└── .streamlit/
    └── secrets.toml.example      # 部署到 Streamlit Cloud 时，后台 Secrets 填的内容模板
```

## 数据库字段说明（Postgres 里的 `events` 表）

| 字段 | 含义 |
|---|---|
| id | 自增主键 |
| created_at | 记录时间（自动填当前时间）|
| raw_text | 你输入的原始事件 |
| category | AI判断的内容分类（美国旅行/汽车/职场观察/女性成长/其他）|
| grade | 选题等级 A/B/C |
| reason | 为什么值得或不值得拍 |
| conflict | 核心冲突或反差 |
| angles | 推荐选题角度（多个角度用换行分隔） |
| privacy_risk | 隐私风险：低/中/高 |
| raw_ai_response | AI的原始返回内容（排查问题用）|

---

## 一、注册免费云数据库（Supabase）—— 只需你自己做一次

1. 打开 https://supabase.com ，用邮箱注册一个账号（免费）
2. 创建一个新项目（New Project），设一个数据库密码（记住它，等下要用）
3. 项目建好后，进入 **Project Settings → Database → Connection string**，选择 **URI** 这种格式，复制出来
   - 长得像：`postgresql://postgres:你的密码@xxxxx.supabase.co:5432/postgres`
4. 这一串就是 `DATABASE_URL`，先存好，下面两个地方都要用

## 二、本地开发配置

```bash
cd "/Users/sunwenbo/Desktop/AI项目集/短视频选题Agent"
```

打开 `.env` 文件（没有就先 `cp .env.example .env`），补上两行：

```
DATABASE_URL=你上一步复制的那一串
APP_PASSWORD=你和家人共用的密码，自己定
```

AI 模型的三行（`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `MODEL_NAME`）你之前已经配过了，不用动。

安装新加的依赖：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

启动，确认本地能正常连上云数据库：

```bash
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，输入你设的密码，能正常记录+查看，说明数据库那步配置对了。

## 三、部署到 Streamlit Cloud，给老婆一个可以直接打开的网址

### 1. 把代码传到 GitHub（免费私有仓库即可，不用公开）

```bash
cd "/Users/sunwenbo/Desktop/AI项目集/短视频选题Agent"
git init
git add .
git commit -m "短视频选题 Agent MVP"
```

然后去 https://github.com/new 建一个新仓库（建议选 **Private**，不想被陌生人看到代码的话），按它给的提示把本地代码推上去，大概是：

```bash
git remote add origin 你的仓库地址
git branch -M main
git push -u origin main
```

> `.env` 和真实的 `secrets.toml` 已经在 `.gitignore` 里排除了，不会被传上去，放心。

### 2. 部署

1. 打开 https://share.streamlit.io ，用 GitHub 账号登录
2. 点 "New app"，选你刚建的仓库，Main file 选 `app.py`
3. 部署前先点 "Advanced settings" → **Secrets**，把 `.streamlit/secrets.toml.example` 里的内容复制过去，换成你的真实值（DATABASE_URL、APP_PASSWORD、AI的key这些）
4. 点 Deploy，等一两分钟

部署好之后会给你一个类似 `https://xxx.streamlit.app` 的网址，发给老婆，她浏览器打开、输入你们俩定的密码，就能直接用了，手机也行。

### 3. 以后怎么更新

以后如果我帮你改了代码，你在本地：

```bash
git add .
git commit -m "说明这次改了什么"
git push
```

Streamlit Cloud 会自动重新部署，不用手动操作。

---

## 安全提醒

- `APP_PASSWORD` 只是一道很简单的门，不是银行级别的安全措施，别用来存特别敏感的信息
- 部署后的网址虽然有密码保护，但**链接本身不要随便发给不相关的人**
- 密钥（AI Key、数据库密码）永远只放在 `.env` 或 Streamlit Cloud 的 Secrets 里，不要贴到聊天记录、不要传到 GitHub 上

## 之后如果想扩展（这一版先不用管）

- 按分类筛选历史记录
- 导出成 Excel/表格给自己复盘
- 给每条记录加"是否已拍摄"状态、"谁记录的"字段（区分你和老婆）
