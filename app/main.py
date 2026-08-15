"""subforge 主入口 —— FastAPI 应用。"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .core.pipeline import Pipeline
from .models.profile import ConvertRequest, Profile
from .parsers.surge import SurgeParser
from .parsers.clash import ClashParser
from .parsers.uri import URIParser
from .parsers.base64 import Base64Parser
from .producers.surge import SurgeProducer
from .producers.clash import ClashProducer
from .transforms.group import CountryGroupBuilder
from .transforms.filter import NodeFilter
from .services.fetcher import fetch_subscription
from .services.profile import ProfileStore
from .validators.mihomo import MihomoValidator
from .validators.surge import SurgeValidator

DATA_DIR = os.environ.get("SUBFORGE_DATA_DIR", os.path.expanduser("~/.subforge"))

# 创建应用
app = FastAPI(
    title="subforge — 订阅锻造厂",
    description="自托管订阅转换服务（塔台升级版）",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化管道
pipeline = Pipeline()
pipeline.register_parser("surge", SurgeParser())
pipeline.register_parser("clash", ClashParser())
pipeline.register_parser("uri", URIParser())
pipeline.register_parser("base64", Base64Parser())
pipeline.register_producer("surge", SurgeProducer())
pipeline.register_producer("clash", ClashProducer())
pipeline.register_validator("surge", SurgeValidator())
pipeline.register_validator("clash", MihomoValidator())

# 转换器
pipeline.add_transform(NodeFilter())
pipeline.add_transform(CountryGroupBuilder())

# Profile 存储
profile_store = ProfileStore(DATA_DIR)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/qr/node")
def qr_node(uri: str = None, box: int = 12):
    """节点二维码 —— 生成单个节点 URI 的二维码 PNG。

    用法: /api/qr/node?uri=ss://base64@host:port#name
    手机扫码可导入单个节点。
    """
    from fastapi.responses import Response
    from .services.qr import generate_qr_png, is_valid_uri

    if not uri or not is_valid_uri(uri):
        raise HTTPException(400, "无效的 URI，需为 ss:// trojan:// anytls:// 等协议链接")
    png = generate_qr_png(uri, box_size=box)
    return Response(content=png, media_type="image/png",
                    headers={"Content-Disposition": "inline; filename=node.png"})


@app.get("/api/qr/subscribe")
def qr_subscribe(profile: str = None, url: str = None, box: int = 12):
    """订阅二维码 —— 生成订阅链接的二维码 PNG。

    用法:
    - /api/qr/subscribe?profile=flower   (用已保存 Profile)
    - /api/qr/subscribe?url=<订阅>       (直接转换)
    手机扫码可导入整个订阅。
    """
    from fastapi.responses import Response
    from urllib.parse import urlencode
    from .services.qr import generate_qr_png, is_valid_uri

    # 构建订阅链接（二维码内容）
    if profile:
        p = profile_store.get_by_name(profile)
        if not p:
            raise HTTPException(404, f"Profile '{profile}' 不存在")
        sub_url = f"/api/subscribe?profile={profile}"
    elif url:
        if not is_valid_uri(url):
            raise HTTPException(400, "无效的订阅 URL")
        sub_url = f"/api/subscribe?{urlencode({'url': url})}"
    else:
        raise HTTPException(400, "需要 profile 或 url 参数")

    png = generate_qr_png(sub_url, box_size=box)
    return Response(content=png, media_type="image/png",
                    headers={"Content-Disposition": "inline; filename=subscribe.png"})


@app.get("/api/subscribe")
def subscribe(
    profile: str = None,
    url: str = None,
    target: str = "clash",
    include: str = None,
    exclude: str = None,
):
    """订阅转换（最常用）

    两种方式：
    1. ?profile=<name>  用已保存的档案
    2. ?url=<订阅>&target=<格式>&include=...&exclude=...  直接转换
    """
    from .models.profile import TransformConfig

    # 1. 用已保存的 Profile
    if profile:
        p = profile_store.get_by_name(profile)
        if not p:
            raise HTTPException(404, f"Profile '{profile}' 不存在")
        return _convert_profile(p)

    # 2. 直接转换
    if not url:
        raise HTTPException(400, "需要 profile 或 url 参数")

    transforms = TransformConfig()
    if include:
        transforms.include = [k.strip() for k in include.split(",")]
    if exclude:
        transforms.exclude = [k.strip() for k in exclude.split(",")]

    request = ConvertRequest(source=url, source_type="url", target=target, transforms=transforms)
    return _convert_request(request)


@app.post("/api/convert")
def convert(req: ConvertRequest):
    """转换配置"""
    return _convert_request(req)


@app.get("/api/profiles", response_model=list[Profile])
def list_profiles():
    return profile_store.list()


@app.post("/api/profiles", response_model=Profile)
def create_profile(profile: Profile):
    return profile_store.create(profile)


@app.get("/api/profiles/{pid}", response_model=Profile)
def get_profile(pid: str):
    p = profile_store.get(pid)
    if not p:
        raise HTTPException(404, "Profile 不存在")
    return p


@app.put("/api/profiles/{pid}", response_model=Profile)
def update_profile(pid: str, profile: Profile):
    p = profile_store.update(pid, profile)
    if not p:
        raise HTTPException(404, "Profile 不存在")
    return p


@app.delete("/api/profiles/{pid}")
def delete_profile(pid: str):
    if not profile_store.delete(pid):
        raise HTTPException(404, "Profile 不存在")
    return {"ok": True}


def _convert_profile(p: Profile) -> PlainTextResponse:
    """按 Profile 转换（合并所有订阅，逐订阅转换）"""
    from .models.profile import ConvertRequest

    # 拉取所有订阅并合并
    all_nodes = []
    errors = []
    for sub in p.subscriptions:
        try:
            content, info = fetch_subscription(sub.url, ua=sub.ua)
            nodes = pipeline.parse(content, "auto")
            all_nodes.extend(nodes)
        except Exception as e:
            errors.append(str(e))

    if not all_nodes:
        raise HTTPException(502, f"订阅拉取失败: {'; '.join(errors)}")

    # 转换
    nodes = pipeline.transform(all_nodes, p.transforms)
    content = pipeline.produce(nodes, p.target, transforms=p.transforms)
    return PlainTextResponse(content)


def _convert_request(req: ConvertRequest) -> PlainTextResponse:
    """单次转换请求"""
    try:
        result = pipeline.convert(req)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"转换失败: {e}")
    return PlainTextResponse(result["config"])


# 启动时打印信息
@app.on_event("startup")
def startup():
    print(f"⚙️  subforge v0.1.0 已启动")
    print(f"📂  数据目录: {DATA_DIR}")
    print(f"🔗  健康检查: http://localhost:8000/api/health")
