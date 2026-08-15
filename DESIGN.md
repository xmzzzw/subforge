# subforge — 订阅锻造厂

> 塔台的升级版：一个跑在本地服务器 / Docker 的自托管订阅转换服务。
> 借鉴塔台（tower）、subconverter、sub-store 的设计，用工程思维重新实现。

---

## 1. 项目定位

### 1.1 要解决的问题

现有方案的问题：

| 方案 | 问题 |
|------|------|
| **塔台（tower）** | iOS 原生 App，门槛高（需 Xcode/iPhone）；单机；**用户反馈 bug 多、不好用** |
| **subconverter** | C++ 后端，功能强但配置复杂、无 UI、无持久化订阅、维护难 |
| **sub-store** | Node.js 依赖重、功能分散、配置复杂 |

**subforge 的目标**：做一个「塔台升级版」——具备塔台的易用性和订阅管理，但以 **本地服务/Docker** 形式跑，用现代工程架构避免塔台的 bug。

### 1.2 核心原则

1. **本地优先 / 可自托管**：跑在本地服务器或 Docker，数据不出内网
2. **订阅不落地**：不存储机场订阅的敏感信息（UUID/密码），只存转换规则
3. **管道式架构**：parse → transform → produce，可插拔、可测试
4. **协议广度**：支持主流协议（SS/SSR/VMess/VLESS/Trojan/AnyTLS/Hysteria/TUIC/WireGuard/...）
5. **格式广度**：生成 Surge/Clash/mihomo/Loon/Shadowrocket/QuanX/sing-box 等
6. **订阅刷新**：保留机场订阅的实时刷新能力（含流量/到期显示）
7. **规则自定义**：复用 my-rulesets 的规则集，或用户自定义

---

## 2. 技术选型

| 层 | 选型 | 理由 |
|----|------|------|
| 语言 | **Python 3.11+** | 生态好、可读性高、跨平台、易部署 |
| Web 框架 | **FastAPI** | 异步、自动文档、类型校验、REST 友好 |
| 配置 | **YAML + Pydantic** | 结构化、可校验 |
| 数据库 | **SQLite** | 轻量、零依赖、适合单机 |
| 前端 | **单页 HTML（原生 JS）** | 无构建步骤、零依赖、易部署 |
| 部署 | **Docker + 本地运行** | 双模式 |
| 测试 | **pytest** | 标准、易写 |

**为什么不用 C++/Node.js**：
- C++（subconverter）：性能好但维护难，我们不需要极致性能
- Node.js（sub-store）：依赖重、内存占用高
- Python：平衡了开发效率、可维护性、部署便捷，性能足够（转换是 IO 密集为主）

---

## 3. 架构设计

### 3.1 总体架构

```
                    ┌─────────────────────────────┐
                    │         Web UI (单页)        │
                    │  订阅管理 / 节点预览 / 规则    │
                    │  转换测试 / 日志             │
                    └────────────┬────────────────┘
                                 │ HTTP
                    ┌────────────▼────────────────┐
                    │       REST API (FastAPI)    │
                    │  /api/subscribe             │
                    │  /api/convert               │
                    │  /api/profiles              │
                    │  /api/health                │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │      Core 管道引擎          │
                    │                             │
                    │  Fetch → Parse → Transform  │
                    │       → Produce → Validate  │
                    │                             │
                    └────────────┬────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼───────┐   ┌───────────▼───────┐   ┌─────────────▼─────┐
│  Parser 层     │   │  Transform 层      │   │  Producer 层       │
│ SS/VMess/...  │   │ 国家分组/筛选/重命名 │   │ Surge/Clash/...   │
│ Surge/Clash   │   │ 单节点合并/协议标注  │   │ sing-box/Loon     │
└───────────────┘   └───────────────────┘   └───────────────────┘
```

### 3.2 管道式核心（借鉴 sub-store）

```
输入订阅/节点
   ↓
[Fetch]     拉取订阅（处理 IP 限制 / 时间窗口 / UA）
   ↓
[Parse]     解析为统一 Node 模型（识别协议）
   ↓
[Transform] 节点操作管道：
   - 国家识别（emoji/代码/中文名）
   - 国家分组构建（select + 自动选择）
   - 单节点国家合并
   - 筛选（include/exclude）
   - 重命名 / 协议标注
   ↓
[Produce]   生成目标格式（Surge/Clash/mihomo/...）
   ↓
[Validate]  校验（surge-cli / mihomo -t）
   ↓
输出配置
```

**关键设计**：每个阶段是独立模块，可插拔、可测试。这正是塔台 bug 多的根源之一——耦合严重，subforge 用管道解耦。

### 3.3 目录结构

```
subforge/
├── DESIGN.md                  # 本设计文档
├── README.md                  # 项目总览
├── pyproject.toml             # 依赖管理
├── docker-compose.yml         # Docker 部署
├── Dockerfile                 # 镜像构建
├── app/
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置加载
│   ├── core/
│   │   ├── pipeline.py        # 管道引擎
│   │   ├── node.py            # 统一节点模型
│   │   ├── country.py         # 国家识别
│   │   └── protocol.py        # 协议识别
│   ├── parsers/
│   │   ├── base.py            # 解析器基类
│   │   ├── surge.py           # Surge .conf 解析
│   │   ├── clash.py           # Clash YAML 解析
│   │   ├── uri.py             # URI 协议解析 (ss:// trojan:// ...)
│   │   └── base64.py          # Base64 订阅解析
│   ├── transforms/
│   │   ├── group.py           # 国家分组构建
│   │   ├── filter.py          # 节点筛选
│   │   ├── rename.py          # 重命名/协议标注
│   │   └── merge.py           # 单节点合并
│   ├── producers/
│   │   ├── base.py            # 生成器基类
│   │   ├── surge.py           # Surge 生成
│   │   ├── clash.py           # Clash/mihomo 生成
│   │   ├── loon.py            # Loon 生成
│   │   ├── quanx.py           # Quantumult X 生成
│   │   ├── shadowrocket.py    # Shadowrocket 生成
│   │   └── singbox.py         # sing-box 生成
│   ├── validators/
│   │   ├── surge.py           # surge-cli 校验
│   │   └── mihomo.py          # mihomo -t 校验
│   ├── services/
│   │   ├── fetcher.py         # 订阅拉取（IP限制/窗口期处理）
│   │   ├── profile.py         # 配置档案管理
│   │   └── rules.py           # 规则集管理
│   ├── models/
│   │   ├── node.py            # Pydantic 节点模型
│   │   ├── profile.py         # 配置档案模型
│   │   └── request.py         # API 请求模型
│   └── api/
│       ├── subscribe.py       # 订阅转换 API
│       ├── convert.py         # 转换 API
│       ├── profiles.py        # 档案 API
│       └── health.py          # 健康检查
├── frontend/
│   └── index.html             # 单页 UI
├── tests/
│   ├── test_parsers.py
│   ├── test_transforms.py
│   ├── test_producers.py
│   └── test_pipeline.py
└── examples/
    └── config.yaml            # 配置示例
```

---

## 4. 核心数据模型

### 4.1 统一节点模型（Node）

所有协议的节点统一为：

```python
class Node(BaseModel):
    name: str                    # 节点名（可含 emoji）
    protocol: str                # ss/trojan/anytls/vmess/vless/...
    server: str
    port: int
    params: dict                 # 协议特定参数
    country: str = None          # 识别出的国家（🇭🇰 香港）
    tag: str = None              # 协议标注 ([ss]/[trojan]/[anytls])
```

**关键**：所有解析器输出统一 Node，所有生成器消费统一 Node。这样「解析新协议」和「生成新格式」互不影响——这是可插拔的核心。

### 4.2 配置档案（Profile）

类似塔台的方案/我的 my-rulesets：

```python
class Profile(BaseModel):
    name: str
    subscriptions: list[Subscription]   # 一个或多个机场订阅
    transforms: list[Transform]          # 管道配置（分组/筛选/重命名）
    target: str                          # 目标格式
    rules: RuleConfig                    # 规则集配置
```

**Profile 是核心抽象**：一个 Profile 定义一个「输入订阅 + 转换规则 + 输出格式」的完整配置。用户建一个 Profile，之后每次请求都按它转换。

---

## 5. API 设计

### 5.1 核心接口

```http
# 订阅转换（最常用）
GET /api/subscribe?profile=<name>
# 或直接传参
GET /api/subscribe?url=<订阅URL>&target=clash&include=香港&exclude=澳门

# 节点二维码（手机扫码导入单个节点）
GET /api/qr/node?uri=ss://...  → PNG

# 订阅二维码（手机扫码导入整个订阅）
GET /api/qr/subscribe?profile=flower  → PNG
GET /api/qr/subscribe?url=<订阅URL>   → PNG

# 转换配置
POST /api/convert
{ "source": "...", "target": "clash", "transforms": [...] }

# 节点预览（转换前查看节点，按国家分组）
POST /api/nodes
{ "source": "...", "transforms": {...} }

# 延迟测试（节点 TCP 测速）
POST /api/latency
{ "source": "...", "transforms": {...} }
→ { "count": N, "summary": {...}, "results": [...] }

# 支持格式列表
GET /api/formats
→ {"formats": ["clash", "surge", "loon", "quanx", "shadowrocket", "singbox"]}

# 规则集管理（内置 my-rulesets + 自定义）
GET/POST  /api/rulesets
DELETE    /api/rulesets/<id>

# 配置档案管理
GET/POST/PUT/DELETE /api/profiles

# 健康检查
GET /api/health
```

### 5.2 客户端用法

```bash
# 生成 Clash 配置
curl "http://localhost:8000/api/subscribe?profile=flower"

# 生成 Surge 配置（订阅刷新版）
curl "http://localhost:8000/api/subscribe?profile=flower&target=surge&refresh=1"

# 直接转换
curl "http://localhost:8000/api/subscribe?url=<机场订阅>&target=clash&include=香港"
```

---

## 6. 关键特性设计

### 6.1 订阅拉取（处理机场限制）

参考本次会话经验：

```python
def fetch_subscription(url):
    # 1. 默认直连（绕过本机代理，机场常限制代理 IP）
    # 2. 处理时间窗口（失败时提示"请打开机场后台开启订阅窗口"）
    # 3. 尝试多个 User-Agent
    # 4. 读取 subscription-userinfo 头（流量/到期）
    # 5. 识别 #!MANAGED-CONFIG 和 #!include
```

### 6.2 订阅刷新

两种模式：
- **代理模式（推荐）**：客户端直接用 subforge 生成的 URL 作为订阅，subforge 每次拉取上游并转换 → 节点实时刷新
- **快照模式**：subforge 定时拉取上游，存快照，客户端获取快照

### 6.3 流量/到期显示

- 上游提供 `subscription-userinfo` → 透传给客户端（自动显示流量/到期）
- 上游不提供 → 不伪造（避免不准确）

### 6.4 国家分组

遵循 my-rulesets 规格：
```
Proxies → 应用组 → 🎯Direct → ✈️Final → 国家分组 + 自动选择
```
- 单节点国家合并到 🌍 其他地区
- 每个国家：select + 自动选择（url-test）

### 6.5 规则集

- 内置 my-rulesets 的规则集（引用 GitHub URL）
- 支持自定义规则集（URL 或本地文件）
- 支持 Surge/Clash 双格式规则

### 6.6 验证

- Surge：用 `surge-cli profile check` 验证
- Clash/mihomo：用 `mihomo -t` 验证
- 转换前校验节点合法性，失败时明确报错（不产�生"看起来正常但连不上"的配置）

---

## 7. 与塔台/subconverter/sub-store 对比

| 特性 | 塔台 | subconverter | sub-store | **subforge** |
|------|------|-------------|-----------|-------------|
| 部署 | iOS App | 服务 | 服务 | **本地/Docker** |
| 协议支持 | 主流 | 多 | 极多 | **极多** |
| 格式支持 | 7 种 | 多 | 极多 | **极多** |
| UI | 原生 | 无 | 有 | **单页** |
| 订阅管理 | 有 | 无 | 有 | **有** |
| 订阅刷新 | 手动 | 无 | 有 | **代理/快照** |
| 规则自定义 | 有 | 有 | 有 | **有（复用 my-rulesets）** |
| 管道架构 | 无 | 部分 | **有** | **有** |
| 自动验证 | 无 | 无 | 无 | **有（surge-cli/mihomo）** |
| 流量显示 | 有 | 无 | 有 | **有** |
| 维护性 | 差（耦合） | 差（C++） | 中 | **好（Python/模块化）** |

---

## 8. 实现计划

### 阶段 1：核心骨架（本次）
- [x] 项目结构、依赖、配置
- [ ] 统一 Node 模型
- [ ] 订阅拉取（fetcher）
- [ ] Surge/Clash/URI 解析器
- [ ] 国家分组转换
- [ ] Surge/Clash 生成器
- [ ] FastAPI 基础接口
- [ ] 基础测试

### 阶段 2：完善功能
- [ ] 更多协议解析（hysteria2/tuic/wireguard）
- [ ] 更多格式生成（loon/quanx/shadowrocket/sing-box）
- [ ] Profile 档案管理（持久化）
- [ ] 订阅代理/快照模式
- [ ] Web UI
- [ ] 规则集管理

### 阶段 3：生产化
- [ ] Docker 部署
- [ ] 验证器集成（surge-cli/mihomo）
- [ ] 日志/监控
- [ ] 配置迁移/备份
- [ ] 文档完善

---

## 9. 为什么这个设计能避免塔台的 bug

塔台 bug 多的根源（从架构分析）：
1. **耦合严重**：AppModel 是中央状态，解析/识别/生成都耦合
2. **状态管理复杂**：@Observable 字典/集合反复修改导致 UI 失效
3. **iOS 平台限制**：网络/测速/后台限制多
4. **硬编码策略组**：部分策略组在 Swift 里写死

**subforge 的对策**：
1. **管道解耦**：每阶段独立模块，可插拔可测试
2. **无状态核心**：转换引擎无状态，Profile 持久化分离
3. **服务化**：无平台限制，网络/测速/后台不受 iOS 约束
4. **配置驱动**：策略组/规则全部配置化，不写死
5. **自动验证**：每次转换用 surge-cli/mihomo 验证，问题早暴露

---

## 10. 部署

### Docker（推荐）
```bash
docker compose up -d
# 访问 http://localhost:8000
```

### 本地
```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 软路由/服务器
- 可在 OpenWrt/iStoreOS 上跑
- 或部署到 VPS/群晖/树莓派
