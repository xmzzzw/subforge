# subforge — 订阅锻造厂

> 塔台的升级版：一个跑在本地服务器 / Docker 的自托管订阅转换服务。
> 借鉴塔台（tower）、subconverter、sub-store 的设计，用管道式架构重新实现。

**设计文档见 [DESIGN.md](DESIGN.md)**

---

## 为什么做这个

| 方案 | 问题 |
|------|------|
| **塔台（tower）** | iOS App，门槛高（需 Xcode/iPhone）；单机；bug 多、不好用 |
| **subconverter** | C++ 后端，配置复杂、无 UI、无持久化订阅、维护难 |
| **sub-store** | Node.js 依赖重、功能分散、配置复杂 |

**subforge** 结合三者优点：本地/Docker 部署 + 管道式架构 + 协议广度 + Web UI。

## 核心能力

- **多协议解析**：SS/SSR/Trojan/AnyTLS/VMess/VLESS/Hysteria/Hysteria2/TUIC/WireGuard
- **多格式生成**：Surge/Clash/mihomo（更多格式规划中）
- **管道式架构**：Fetch → Parse → Transform → Produce → Validate（可插拔、可测试）
- **国家分组**：自动识别（emoji/代码/中文名）+ 单节点国家合并 + 自动选择
- **订阅刷新**：proxy 模式（每次拉取上游）/ snapshot 模式（快照）
- **流量/到期**：透传 `subscription-userinfo`（上游提供时）
- **Profile 档案**：一个 Profile 定义「输入订阅 + 转换规则 + 输出格式」
- **自动验证**：mihomo -t / surge-cli（有对应客户端时）

## 快速开始

### Docker

```bash
docker build -t subforge .
docker run -d -p 8000:8000 -v ~/.subforge:/data subforge
# 访问 http://localhost:8000
```

### 本地

```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 使用

### API

```bash
# 健康检查
curl http://localhost:8000/api/health

# 订阅转换（最常用）
curl "http://localhost:8000/api/subscribe?url=<机场订阅>&target=clash&include=香港"

# 节点二维码（手机扫码导入单个节点）
curl "http://localhost:8000/api/qr/node?uri=ss://..." -o node.png

# 订阅二维码（手机扫码导入整个订阅）
curl "http://localhost:8000/api/qr/subscribe?profile=flower" -o sub.png

# 用已保存的 Profile
curl "http://localhost:8000/api/subscribe?profile=flower-ss"

# 转换配置（POST）
curl -X POST http://localhost:8000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"source":"...","target":"clash"}'
```

### Profile 管理

```bash
# 创建
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"name":"flower","subscriptions":[{"url":"..."}],"target":"clash"}'

# 列表
curl http://localhost:8000/api/profiles

# 删除
curl -X DELETE http://localhost:8000/api/profiles/<id>
```

### 客户端接入

把 subforge 的订阅 URL 填进客户端（Surge/FlClash/Clash Verge）：
```
http://<服务器>:8000/api/subscribe?profile=flower
```
客户端每次刷新 → subforge 拉取上游 → 转换 → 返回配置。节点实时更新。

## 项目结构

```
subforge/
├── DESIGN.md            # 设计文档
├── README.md
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── core/            # 管道引擎/协议/国家识别
│   ├── parsers/         # 订阅解析器（Surge/Clash/URI/Base64）
│   ├── transforms/      # 转换器（国家分组/筛选）
│   ├── producers/       # 配置生成器（Surge/Clash）
│   ├── validators/      # 验证器（mihomo/surge-cli）
│   ├── services/        # 订阅拉取/Profile 管理
│   └── models/          # 数据模型
├── tests/               # 测试
└── examples/            # 配置示例
```

## 技术栈

Python 3.11+ · FastAPI · Pydantic · PyYAML · SQLite（JSON 存储）

## 路线图

- [ ] 更多协议（hysteria2/tuic/wireguard 解析完善）
- [ ] 更多格式（Loon/QuanX/Shadowrocket/sing-box）
- [ ] Web UI（订阅管理/节点预览/转换测试）
- [ ] 规则集管理（复用 my-rulesets）
- [ ] 验证器完善
- [ ] 多订阅聚合

## License

MIT
