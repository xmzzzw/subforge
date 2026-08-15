# subforge — 订阅锻造厂

> 塔台的升级版：一个跑在本地服务器 / Docker 的自托管订阅转换服务。
> 借鉴塔台（tower）、subconverter、sub-store 的设计，用管道式架构重新实现。
> 目标是做成一个「缝合怪」—— 集各家之长。

**设计文档见 [DESIGN.md](DESIGN.md)**

---

## 为什么做这个

| 方案 | 问题 |
|------|------|
| **塔台（tower）** | iOS App，门槛高（需 Xcode/iPhone）；单机；bug 多、不好用 |
| **subconverter** | C++ 后端，配置复杂、无 UI、无持久化订阅、维护难 |
| **sub-store** | Node.js 依赖重、功能分散、配置复杂 |

**subforge** 缝合三者优点：本地/Docker 部署 + 管道式架构 + 协议广度 + Web UI。

## 🧵 核心能力（缝合怪全家桶）

### 格式支持（6 种）
Surge · Clash/mihomo · Loon · Quantumult X · Shadowrocket · sing-box

### 协议支持（14 种）
SS · SSR · Trojan · AnyTLS · VMess · VLESS · Hysteria · Hysteria2 · TUIC · WireGuard · Snell · SOCKS5 · HTTP(S)

### 功能列表

| 功能 | 说明 |
|------|------|
| **订阅聚合** | 多机场订阅合并、按 server:port 去重、节点前缀区分、失败容错 |
| **订阅刷新** | proxy 模式（每次拉取上游）/ snapshot 模式（快照） |
| **流量/到期** | 透传 `subscription-userinfo`（上游提供时自动显示） |
| **国家分组** | 自动识别（emoji/代码/中文名）+ 单节点国家合并 + 自动选择 |
| **节点预览** | 转换前查看节点列表（按国家分组 + 协议统计 + 节点详情） |
| **延迟测试** | 节点 TCP 测速（并发、超时控制、Web UI 可视化延迟条） |
| **规则集管理** | 内置 my-rulesets 24 个 + 自定义规则集（URL/内联内容编辑） |
| **Profile 档案** | 一个 Profile 定义「订阅 + 转换规则 + 输出格式」，可持久化 |
| **Profile 测试** | 一键验证订阅 URL 连通性（节点数/流量/错误） |
| **二维码** | 节点 URI 二维码 + 订阅链接二维码（手机扫码导入） |
| **转换历史** | 自动记录最近 20 次转换 |
| **自动验证** | mihomo -t / surge-cli（有对应客户端时，无则降级） |
| **管道架构** | Fetch → Parse → Transform → Produce → Validate（可插拔、可测试） |

## 快速开始

### Docker

```bash
docker build -t subforge .
docker run -d -p 8000:8000 -v ~/.subforge:/data subforge
# 访问 http://localhost:8000
```

或使用 docker-compose：

```bash
docker compose up -d
```

### 本地

```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🖥️ Web UI

访问 `http://localhost:8000`：

| 标签页 | 功能 |
|--------|------|
| 仪表盘 | 服务状态、档案/订阅/格式/规则集统计 |
| 配置档案 | 创建/编辑/删除 Profile（订阅 + 前缀聚合 + 转换规则 + 格式） |
| 转换测试 | 粘贴订阅/配置 → 6 格式转换 + 节点预览 + 延迟测试 + 下载 |
| 规则集 | 查看内置规则集 + 添加/编辑自定义规则集（内容编辑） |
| 二维码 | 节点 URI / 订阅链接二维码生成 |
| 历史 | 最近转换记录 |
| API | 接口参考 |

## 📡 API 参考

```bash
# 健康检查
GET /api/health

# 订阅转换（最常用）
GET /api/subscribe?profile=<名称>
GET /api/subscribe?url=<机场订阅>&target=clash&include=香港

# 转换配置（POST）
POST /api/convert
{ "source": "...", "source_type": "auto", "target": "clash", "transforms": {...} }

# 节点预览
POST /api/nodes
{ "source": "...", "transforms": {...} }
→ { "count": N, "nodes": [{name, protocol, server, port, country, uri}] }

# 延迟测试
POST /api/latency
→ { "count": N, "summary": {total, ok, timeout, avg_ms, best_ms}, "results": [...] }

# Profile 连通性测试
POST /api/profile/test
{ "profile": "名称" } 或 { "urls": ["...", "..."] }

# 配置档案 CRUD
GET/POST /api/profiles
GET/PUT/DELETE /api/profiles/<id>

# 规则集管理
GET/POST /api/rulesets
GET/PUT/DELETE /api/rulesets/<id>

# 支持格式
GET /api/formats
→ {"formats": ["clash", "loon", "quanx", "shadowrocket", "singbox", "surge"]}

# 二维码
GET /api/qr/node?uri=ss://...          → 节点 PNG
GET /api/qr/subscribe?profile=flower   → 订阅 PNG

# 转换历史
GET/DELETE /api/history
```

### 客户端接入

把 subforge 的订阅 URL 填进客户端（Surge/FlClash/Clash Verge）：
```
http://<服务器>:8000/api/subscribe?profile=flower
```
客户端每次刷新 → subforge 拉取上游 → 转换 → 返回配置。节点实时更新。

## 🏗️ 项目结构

```
subforge/
├── DESIGN.md            # 设计文档
├── README.md
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── core/            # 管道引擎/协议/国家识别
│   ├── parsers/         # Surge/Clash/URI/Base64 解析器
│   ├── transforms/      # 国家分组/筛选
│   ├── producers/       # 6 生成器（Surge/Clash/Loon/QuanX/Shadowrocket/sing-box）
│   ├── validators/      # mihomo/surge-cli 验证器
│   ├── services/        # 聚合/延迟/规则集/二维码/Profile/历史/拉取
│   └── models/          # 数据模型
├── frontend/            # Web UI（单页零依赖）
├── tests/               # 30 个测试
├── Dockerfile           # Docker 部署
├── docker-compose.yml
└── examples/            # 配置示例
```

## 🔧 技术栈

Python 3.11+ · FastAPI · Pydantic · PyYAML · requests · qrcode[pil]

## ✅ 状态

- 测试：**30/30 通过**
- 格式：**6 种生成**
- 协议：**14 种解析**
- API：**20+ 个接口**
- Web UI：**7 个功能页**

## 📋 路线图

- [x] 多协议解析（SS/SSR/Trojan/AnyTLS/VMess/VLESS/Hysteria/Hysteria2/TUIC/WireGuard）
- [x] 多格式生成（Surge/Clash/Loon/QuanX/Shadowrocket/sing-box）
- [x] Web UI（订阅管理/节点预览/转换测试/二维码/规则集/历史）
- [x] 规则集管理（内置 my-rulesets + 自定义）
- [x] 订阅聚合（多机场合并去重）
- [x] 延迟测试 + 可视化
- [x] Profile 连通性测试
- [ ] Docker 实机部署测试
- [ ] 更多解析器优化（WireGuard 多 Peer 等）

## License

MIT
