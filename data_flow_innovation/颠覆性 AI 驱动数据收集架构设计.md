# 颠覆性 AI 驱动数据收集架构设计

> **设计理念**：以大模型 + 多智能体协作为核心引擎，将人类从重复性的信息采集工作中彻底解放，仅在极端异常场景下保留人工介入通道。

---

## 一、现有流程痛点分析

| 痛点 | 具体表现 | 影响 |
|------|----------|------|
| 全程人工操作 | 人工登录、浏览、识别、下载 | 效率极低，无法规模化 |
| 多语言障碍 | 英/中/日/法/意/德等 | 人工需具备多语言能力 |
| Cloudflare 验证 | 反爬机制频繁触发 | 阻断自动化尝试 |
| 链接识别依赖经验 | 年报/季报/音频链接散落各处 | 错漏率高 |
| 数据质量无闭环 | 无自动核验机制 | 下错版本、漏传时难以发现 |
| Chrome 插件瓶颈 | 单机单任务操作模式 | 并发能力为零 |

---

## 二、整体架构蓝图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR  (总指挥 Agent)                     │
│              基于 LangGraph / AutoGen 有状态工作流引擎                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
          ┌─────────────────────┼──────────────────────┐
          │                     │                      │
          ▼                     ▼                      ▼
  ┌───────────────┐   ┌──────────────────┐   ┌─────────────────┐
  │  Task Agent   │   │  Web Recon Team  │   │  QA & Upload    │
  │  任务调度团队  │   │  网页侦察团队    │   │  质检 & 归档团队 │
  └───────────────┘   └──────────────────┘   └─────────────────┘
```

---

## 三、五大智能体团队详细设计

### 3.1 Task Orchestrator — 总指挥智能体

**职责**：全局任务调度、状态机管理、异常熔断、人工介入路由

```
技术栈：
  - LangGraph (有向无环图状态机)
  - Redis Streams (任务队列 + 事件总线)
  - OpenAI GPT-4o / Claude Sonnet (推理核心)

核心能力：
  ① 自动轮询任务大厅 API，按优先级生成任务队列
  ② 将每个金融公司任务分解为子任务树
  ③ 动态分配 Worker Agent 资源池
  ④ 实时监控各 Agent 心跳，自动重试 / 切换备用策略
  ⑤ 置信度 < 阈值时触发 Human-in-the-Loop 工单
```

**状态机流转**：

```
PENDING → DISPATCHED → RECON → DOWNLOADING → VERIFYING → UPLOADED → DONE
                                    │                          │
                                    └──── RETRY (≤3次) ────────┘
                                                  │
                                              ESCALATE → 人工队列
```

---

### 3.2 Auth & Session Agent — 认证会话智能体

**职责**：管理 oAuth2 令牌生命周期 + 处理各类网站验证

```
子能力模块：

  [A] oAuth2 Token Manager
      - 自动刷新 JWT（JWT refresh token 轮转）
      - 多账号令牌池管理，避免单点失效

  [B] Cloudflare Solver Agent
      - 使用真实浏览器指纹（Playwright + stealth 插件）
      - 集成住宅 IP 代理池（Oxylabs / Brightdata）轮换
      - AI 视觉模型（GPT-4o Vision）自动识别并完成
        可视化验证码 / Turnstile Challenge
      - 行为拟人化：随机鼠标轨迹、阅读停顿、滚动模式

  [C] Session State Keeper
      - 持久化 Cookie / Session，避免重复登录
      - 检测到会话失效时静默重新认证
```

---

### 3.3 Web Recon Team — 网页侦察团队

这是整个系统最核心的智能体团队，由 4 个专业 Agent 协作运行。

#### 3.3.1 Navigator Agent — 智能导航智能体

```
输入：金融公司官网 URL
输出：候选页面列表（含链接、语言标记、置信度评分）

技术实现：
  - Playwright headless browser（可切换 headed 模式应对检测）
  - DOM 快照 + 截图双通道输入给 LLM
  - GPT-4o Vision 理解页面结构，识别"投资者关系""IR""年报"
    等导航入口（无需语言预先知道——模型直接理解图像）
  - 多语言路由表（预置 IR 页面常见关键词向量索引）：
      英文: "Investor Relations", "Annual Report", "Earnings Call"
      中文: "投资者关系", "年度报告", "业绩发布"
      日文: "投資家情報", "年次報告書", "決算説明会"
      法文: "Relations Investisseurs", "Rapport Annuel"
      德文: "Investor Relations", "Geschäftsbericht"
      意文: "Relazioni Investitori", "Relazione Annuale"
  - 当页面结构复杂时，启动 Tree-of-Thought 推理链
    逐层探索网站地图
```

#### 3.3.2 Link Extractor Agent — 链接提取智能体

```
输入：候选页面 HTML + 截图
输出：带结构化元数据的文档链接列表

技术实现：
  - 双模态分析（文本 + 视觉）：
      · 文本模式：解析 <a href>, <iframe src>, JavaScript 动态加载
      · 视觉模式：GPT-4o 截图分析，识别"下载"按钮、PDF 图标
  - LLM 结构化输出（JSON Schema 强制约束）：
      {
        "type": "annual_report | quarterly_report | earnings_audio",
        "year": 2024,
        "quarter": "Q3",       // 季报专用
        "language": "zh-CN",
        "url": "https://...",
        "confidence": 0.97,
        "source_text": "2024年第三季度报告"
      }
  - 使用 RAG（向量数据库 Pinecone/Weaviate）检索该公司
    历史链接模式，提升新一轮采集准确率
  - 反混淆：自动处理 JavaScript 跳转、CDN 签名 URL、
    302 重定向链等复杂链接形态
```

#### 3.3.3 Language & Content Validator Agent — 语言内容核验智能体

```
职责：确认下载文件内容与预期匹配

核心逻辑：
  ① PDF 快速解析（PyMuPDF）提取首页文字
  ② 发送给 LLM 判断：
     - 文档类型是否匹配（年报/季报）
     - 报告期是否正确（年份/季度）
     - 公司名称是否匹配
  ③ 音频文件：调用 Whisper 模型转录前30秒
     确认为业绩发布会内容
  ④ 不合格文件标记为 MISMATCH，触发重新搜索
```

#### 3.3.4 Deep Search Agent — 深度搜索智能体

```
触发条件：Navigator + Link Extractor 两轮均未找到目标链接

搜索策略（级联）：
  ① 站内搜索框自动输入关键词搜索
  ② Google/Bing Site Search API：
     site:target-company.com "annual report" 2024 filetype:pdf
  ③ 调用 Exa / Tavily AI 搜索 API（专为 LLM 设计的搜索）
  ④ 访问 SEC EDGAR / 港交所披露易 / 上交所
     等监管机构数据库直接检索
  ⑤ 仍未找到 → 置信度标记为 LOW，上报 Orchestrator
```

---

### 3.4 Download & Processing Team — 下载处理团队

```
并行下载架构：
  - 每个任务独立 Docker 容器，完全隔离
  - 异步 IO（aiohttp + asyncio），支持断点续传
  - 动态限速：根据目标服务器响应自适应调整并发数
  - 文件完整性校验：SHA-256 哈希 + 文件大小验证

处理管道：
  PDF 文件  → 元数据提取 → 页数/大小验证 → 加密存储
  音频文件  → 格式转码（统一为 MP3/M4A）→ 时长验证 → 存储

上传至 AWS S3：
  - 结构化路径：s3://bucket/{company_id}/{year}/{type}/{filename}
  - 自动打标签（S3 Object Tags）：
      company, report_type, year, quarter, language, source_url
  - 触发 S3 Event → SQS → 下游处理管道通知
```

---

### 3.5 QA & Audit Agent — 质检审计智能体

```
自动质检维度：
  ① 完整性检查：任务要求的所有公司是否全部采集
  ② 时效性检查：是否为最新版本（对比历史记录）
  ③ 重复检查：MD5 去重，避免重复上传
  ④ 文件健康度：PDF 可读性、音频可播放性
  ⑤ 覆盖率报告：自动生成 Task Completion Report

审计日志（不可篡改）：
  - 每个操作写入 DynamoDB（带时间戳 + Agent ID）
  - 关键决策记录 LLM 推理链（Chain-of-Thought 存档）
  - 完整的数据血缘追踪（从 URL 到 S3 路径）
```

---

## 四、Human-in-the-Loop 机制（最小化人工介入）

人工介入仅在以下场景触发，且通过专属工单系统管理：

```
触发条件                          人工动作          预计频率
─────────────────────────────────────────────────────────
Cloudflare 人机验证无法自动通过    手动完成验证       < 2%
网站需要企业账号登录               提供凭证           < 1%
LLM 置信度持续 < 0.7              确认正确链接       < 5%
监管机构网站结构重大变更            提供新导航路径     极少
```

**人工介入界面**：
- Web 实时 Dashboard（任务状态全览）
- 钉钉 / Slack Bot 推送异常工单
- 一键确认/拒绝界面，人工操作 < 30秒/次

---

## 五、新旧流程对比

| 维度 | 现有流程 | 新 AI 架构 |
|------|----------|-----------|
| 人力需求 | 全程人工操作 | 仅 < 5% 异常场景 |
| 并发能力 | 1人 = 1任务 | 1000+ 任务并行 |
| 语言支持 | 依赖人员语言能力 | 100+ 语言自动识别 |
| Cloudflare | 人工手动通过 | AI 视觉 + 代理自动解决 |
| 错误率 | 人工疲劳导致漏采 | AI 多轮验证，< 0.1% |
| 运行时间 | 工作时间 8h | 7×24 不间断 |
| 可追溯性 | 无完整记录 | 全链路审计日志 |
| 扩展成本 | 线性增加人力 | 计算资源弹性扩缩 |

---

## 六、技术选型总览

```
层级              技术选型
──────────────────────────────────────────────────────
Agent 框架       LangGraph (状态机) + AutoGen (多Agent协作)
LLM 推理         GPT-4o (主力) + Claude 3.7 Sonnet (备用)
视觉理解         GPT-4o Vision / Gemini 2.0 Flash Vision
浏览器自动化     Playwright + playwright-stealth
搜索增强         Exa AI / Tavily / SerpAPI
向量数据库       Pinecone (历史模式 RAG)
音频转录         OpenAI Whisper large-v3
任务队列         Redis Streams + Celery
文件存储         AWS S3 + DynamoDB (元数据)
代理池           Brightdata / Oxylabs (住宅 IP)
容器化           Docker + Kubernetes (弹性伸缩)
监控             Grafana + Prometheus + LangSmith (LLM 追踪)
通知             Slack Bot / 钉钉 Webhook
```

---

## 七、落地路线图

### Phase 1 — 基础骨架（第 1-4 周）
- [ ] Orchestrator 状态机搭建（LangGraph）
- [ ] oAuth2 Token Manager 实现
- [ ] Navigator Agent MVP（处理英文网站）
- [ ] S3 上传管道打通

### Phase 2 — 智能核心（第 5-8 周）
- [ ] Link Extractor Agent（双模态）
- [ ] 多语言支持（接入 GPT-4o Vision）
- [ ] Cloudflare Solver 集成代理池
- [ ] QA Agent + 内容核验

### Phase 3 — 规模化与韧性（第 9-12 周）
- [ ] Deep Search Agent（Exa / 监管数据库）
- [ ] RAG 历史模式学习
- [ ] Kubernetes 弹性部署
- [ ] Human-in-the-Loop Dashboard
- [ ] 全链路监控告警

### Phase 4 — 持续自进化（第 13 周+）
- [ ] Fine-tuning 专属金融 IR 页面识别模型
- [ ] Agent 自我评估 + 策略优化闭环
- [ ] 新公司冷启动自动学习机制

---

## 八、架构创新亮点总结

1. **视觉原生理解**：不依赖 CSS 选择器或 XPath，用 GPT-4o Vision 直接"看懂"任意语言的网页，彻底消除语言壁垒。

2. **有记忆的 Agent 网络**：RAG 向量库积累每个金融公司的历史链接模式，后续采集自动"记得"从哪里找。

3. **自适应反反爬策略**：AI 动态调整行为模式（速度、点击位置、停顿时间），而非固定规则，对抗不断升级的检测机制。

4. **级联搜索容错**：4 级搜索策略（直接浏览 → 站内搜索 → AI 搜索 → 监管数据库），任一层成功即止，人工仅兜底。

5. **全链路可解释性**：每个 Agent 决策均记录 Chain-of-Thought，数据血缘从源 URL 到 S3 完全可追溯，满足合规审计需求。

6. **弹性并发，零人力边际成本**：Kubernetes + Celery Worker 池，任务量×10 只需多开实例，不需多招人。
