"""国家识别 —— 从节点名自动识别所属国家（emoji/代码/中文名）。"""
import re
from typing import Dict, Optional

# 国家代码 → emoji + 中文名
COUNTRY_MAP: Dict[str, str] = {
    "HK": "🇭🇰 香港", "SG": "🇸🇬 新加坡", "JP": "🇯🇵 日本",
    "US": "🇺🇸 美国", "UK": "🇬🇧 英国", "GB": "🇬🇧 英国",
    "TW": "🇨🇳 台湾", "DE": "🇩🇪 德国", "AU": "🇦🇺 澳大利亚",
    "KR": "🇰🇷 韩国", "CA": "🇨🇦 加拿大", "NL": "🇳🇱 荷兰",
    "IN": "🇮🇳 印度", "FR": "🇫🇷 法国", "RU": "🇷🇺 俄罗斯",
    "TR": "🇹🇷 土耳其", "PH": "🇵🇭 菲律宾", "ID": "🇮🇩 印尼",
    "VN": "🇻🇳 越南", "ES": "🇪🇸 西班牙", "UA": "🇺🇦 乌克兰",
    "NO": "🇳🇴 挪威", "CH": "🇨🇭 瑞士", "SE": "🇸🇪 瑞典",
    "IE": "🇮🇪 爱尔兰", "MY": "🇲🇾 马来西亚", "TH": "🇹🇭 泰国",
    "AE": "🇦🇪 阿联酋", "EG": "🇪🇬 埃及", "BR": "🇧🇷 巴西",
    "IT": "🇮🇹 意大利", "MX": "🇲🇽 墨西哥", "AR": "🇦🇷 阿根廷",
    "NZ": "🇳🇿 新西兰", "PL": "🇵🇱 波兰", "PT": "🇵🇹 葡萄牙",
    "FI": "🇫🇮 芬兰", "DK": "🇩🇰 丹麦", "BE": "🇧🇪 比利时",
    "AT": "🇦🇹 奥地利", "HU": "🇭🇺 匈牙利", "CZ": "🇨🇿 捷克",
    "GR": "🇬🇷 希腊", "IL": "🇮🇱 以色列", "ZA": "🇿🇦 南非",
    "CL": "🇨🇱 智利", "CO": "🇨🇴 哥伦比亚", "PE": "🇵🇪 秘鲁",
}

# emoji → 中文名
EMOJI_MAP: Dict[str, str] = {
    "🇭🇰": "香港", "🇸🇬": "新加坡", "🇯🇵": "日本", "🇺🇸": "美国",
    "🇬🇧": "英国", "🇨🇳": "台湾", "🇹🇼": "台湾", "🇩🇪": "德国",
    "🇦🇺": "澳大利亚", "🇰🇷": "韩国", "🇨🇦": "加拿大", "🇳🇱": "荷兰",
    "🇮🇳": "印度", "🇫🇷": "法国", "🇷🇺": "俄罗斯", "🇹🇷": "土耳其",
    "🇵🇭": "菲律宾", "🇮🇩": "印尼", "🇻🇳": "越南", "🇪🇸": "西班牙",
    "🇺🇦": "乌克兰", "🇳🇴": "挪威", "🇨🇭": "瑞士", "🇸🇪": "瑞典",
    "🇮🇪": "爱尔兰", "🇲🇾": "马来西亚", "🇹🇭": "泰国", "🇦🇪": "阿联酋",
    "🇪🇬": "埃及", "🇧🇷": "巴西", "🇮🇹": "意大利", "🇲🇽": "墨西哥",
    "🇦🇷": "阿根廷", "🇳🇿": "新西兰", "🇵🇱": "波兰", "🇵🇹": "葡萄牙",
    "🇫🇮": "芬兰", "🇩🇰": "丹麦", "🇧🇪": "比利时", "🇦🇹": "奥地利",
    "🇭🇺": "匈牙利", "🇨🇿": "捷克", "🇬🇷": "希腊", "🇮🇱": "以色列",
    "🇿🇦": "南非", "🇨🇱": "智利", "🇨🇴": "哥伦比亚", "🇵🇪": "秘鲁",
}

# 中文名 → emoji+名
CN_NAME_MAP: Dict[str, str] = {v.split(" ", 1)[1]: v for v in COUNTRY_MAP.values()}

# 英文城市名 → 国家
CITY_MAP: Dict[str, str] = {
    "Hong Kong": "🇭🇰 香港", "HongKong": "🇭🇰 香港",
    "Singapore": "🇸🇬 新加坡", "Tokyo": "🇯🇵 日本", "Osaka": "🇯🇵 日本",
    "Los Angeles": "🇺🇸 美国", "New York": "🇺🇸 美国", "Seattle": "🇺🇸 美国",
    "Taiwan": "🇨🇳 台湾", "Seoul": "🇰🇷 韩国",
}


def detect_country(node_name: str) -> str:
    """自动识别节点所属国家（灵活匹配多种命名格式）"""
    # 1. emoji 匹配（如 🇭🇰 HK | 香港 01）
    for emoji, cn in EMOJI_MAP.items():
        if emoji in node_name:
            return f"{emoji} {cn}"

    # 2. 国家代码（HK/SG/JP/...）—— 匹配独立词或边界
    for code, full in COUNTRY_MAP.items():
        if code in ("US", "UK", "GB", "TW"):
            # 这些代码容易误匹配（如 "us" 在单词里），要求边界
            if re.search(rf'(?i)\b{code}\b', node_name) or f'|{code}' in node_name or f'{code}|' in node_name:
                return full
        else:
            if re.search(rf'(?i)\b{code}\b', node_name) or f'|{code}' in node_name or f'{code}|' in node_name:
                return full

    # 3. 中文名
    for cn, full in CN_NAME_MAP.items():
        if cn in node_name:
            return full

    # 4. 英文城市名
    for city, full in CITY_MAP.items():
        if city.lower() in node_name.lower():
            return full

    # 5. 其他
    return "🌍 其他地区"


def group_by_country(nodes) -> Dict[str, list]:
    """按国家分组节点"""
    from collections import defaultdict
    result = defaultdict(list)
    for node in nodes:
        if node.country:
            key = node.country
        else:
            key = detect_country(node.name)
            node.country = key
        result[key].append(node)
    return dict(result)


def merge_singletons(by_country: Dict[str, list], threshold: int = 1) -> Dict[str, list]:
    """单节点国家合并到其他地区"""
    result = dict(by_country)
    singletons = [c for c, names in result.items() if len(names) <= threshold]
    for c in singletons:
        result.setdefault("🌍 其他地区", []).extend(result[c])
        del result[c]
    return result
