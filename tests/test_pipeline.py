"""管道核心测试 —— 验证解析/转换/生成全流程。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.pipeline import Pipeline
from app.core.country import detect_country, group_by_country, merge_singletons
from app.parsers.surge import SurgeParser
from app.parsers.clash import ClashParser
from app.parsers.uri import URIParser
from app.producers.surge import SurgeProducer
from app.producers.clash import ClashProducer
from app.transforms.group import CountryGroupBuilder
from app.models.profile import TransformConfig


# ============ 测试数据 ============
SURGE_CONTENT = """[Proxy]
DIRECT = direct
🇭🇰 香港 01 = ss, 1.2.3.4, 10001, encrypt-method=aes-128-gcm, password=pass1, obfs=http, obfs-host=host.com
🇭🇰 香港 02 = ss, 1.2.3.4, 10002, encrypt-method=aes-128-gcm, password=pass1, obfs=http, obfs-host=host.com
🇺🇸 美国 01 = trojan, 5.6.7.8, 443, password=pass2, sni=us.example.com
🇯🇵 日本 01 = anytls, 9.10.11.12, 8443, password=pass3
"""


def test_surge_parser():
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    assert len(nodes) == 4
    assert nodes[0].protocol == "ss"
    assert nodes[0].port == 10001
    assert nodes[1].protocol == "ss"
    assert nodes[2].protocol == "trojan"
    assert nodes[3].protocol == "anytls"


def test_country_detection():
    assert detect_country("🇭🇰 HK | 香港 01") == "🇭🇰 香港"
    assert detect_country("🇺🇸 US | 美国 01") == "🇺🇸 美国"
    assert detect_country("日本 01") == "🇯🇵 日本"
    assert detect_country("Singapore") == "🇸🇬 新加坡"
    assert detect_country("HK") == "🇭🇰 香港"
    assert detect_country("未知节点") == "🌍 其他地区"


def test_group_and_merge():
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig()
    builder.apply(nodes, config)
    groups, by_country = builder.build_groups(nodes, config)

    # 4 节点：香港2（保留）、美国1+日本1（合并到其他地区）
    assert "🇭🇰 香港" in by_country
    assert len(by_country["🇭🇰 香港"]) == 2
    assert "🇺🇸 美国" not in by_country  # 单节点已合并
    assert "🇯🇵 日本" not in by_country
    assert "🌍 其他地区" in by_country


def test_single_node_merge():
    """单节点国家应合并到其他地区"""
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig()
    builder.apply(nodes, config)
    groups, by_country = builder.build_groups(nodes, config)

    # 美国、日本各 1 个节点，应合并到其他地区
    assert "🇺🇸 美国" not in by_country
    assert "🇯🇵 日本" not in by_country
    assert "🌍 其他地区" in by_country
    assert len(by_country["🌍 其他地区"]) == 2


def test_no_merge_single():
    """关闭合并时保留单节点国家"""
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig(merge_single=False)
    builder.apply(nodes, config)
    groups, by_country = builder.build_groups(nodes, config)

    assert "🇺🇸 美国" in by_country
    assert "🇯🇵 日本" in by_country


def test_surge_producer():
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig()
    builder.apply(nodes, config)
    producer = SurgeProducer()
    output = producer.generate(nodes, transforms=config)

    assert "[Proxy]" in output
    assert "[Proxy Group]" in output
    assert "[Rule]" in output
    assert "Proxies = select" in output
    assert "✈️Final" in output
    assert "FINAL,✈️Final" in output
    # 国家分组定义在 Final 后面（检查策略组段内定义行的先后）
    pg_section = output[output.index("[Proxy Group]"):output.index("[Rule]")]
    lines = pg_section.splitlines()
    final_idx = next(i for i, l in enumerate(lines) if l.startswith("✈️Final ="))
    country_idx = next(i for i, l in enumerate(lines) if l.startswith("🌍 其他地区 ="))
    assert final_idx < country_idx, f"Final 应在国家分组前: final={final_idx}, country={country_idx}"


def test_clash_producer():
    import yaml
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig()
    builder.apply(nodes, config)
    producer = ClashProducer()
    output = producer.generate(nodes, transforms=config)

    data = yaml.safe_load(output)
    assert len(data["proxies"]) == 4
    assert len(data["proxy-groups"]) > 0
    assert len(data["rule-providers"]) > 0
    assert "MATCH,✈️Final" in data["rules"]


def test_uri_parser():
    parser = URIParser()
    nodes = parser.parse("ss://YWVzLTI1Ni1nY206cGFzcw==@1.2.3.4:8388#测试节点")
    assert len(nodes) == 1
    assert nodes[0].protocol == "ss"


def test_full_pipeline():
    """完整管道：解析→转换→生成"""
    pipeline = Pipeline()
    pipeline.register_parser("surge", SurgeParser())
    pipeline.register_parser("clash", ClashParser())
    pipeline.register_parser("uri", URIParser())
    pipeline.register_producer("surge", SurgeProducer())
    pipeline.register_producer("clash", ClashProducer())
    pipeline.add_transform(NodeFilterStub())
    pipeline.add_transform(CountryGroupBuilder())

    nodes = pipeline.parse(SURGE_CONTENT, "surge")
    assert len(nodes) == 4

    config = TransformConfig()
    nodes = pipeline.transform(nodes, config)
    content = pipeline.produce(nodes, "surge", transforms=config)
    assert "Proxies = select" in content


class NodeFilterStub:
    """测试用空转换器"""
    def apply(self, nodes, config):
        return nodes


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} 通过")
