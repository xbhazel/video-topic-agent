"""
AI 判断模块：把一段生活事件发给AI，让它判断值不值得拍、怎么拍。

用的是 OpenAI 官方 SDK，但通过修改配置里的 OPENAI_BASE_URL，
同样可以接 DeepSeek / Moonshot / 通义千问 等兼容 OpenAI 接口格式的便宜模型，
不用改这份代码。
"""

import json
from openai import OpenAI
from config import get_config

API_KEY = get_config("OPENAI_API_KEY")
BASE_URL = get_config("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = get_config("MODEL_NAME", "gpt-4o-mini")

# 这里故意给一个占位符：如果还没配置好，程序不应该在“打开网页”这一步就崩溃，
# 而应该等到用户真正点击“让AI判断”按钮时，再把清晰的报错显示在网页上（见 app.py 里的 try/except）。
client = OpenAI(api_key=API_KEY or "not-configured", base_url=BASE_URL)

# 这段是给AI的固定说明，账号定位写死在这里，以后调账号方向就改这里
SYSTEM_PROMPT = """你是一个短视频选题分析助手，服务于一个内容账号。
账号内容方向固定为以下四类：
1. 美国旅行
2. 汽车 / 开车生活
3. 美国职场和生活观察
4. 女性成长视角

用户会给你一段"今天发生的生活小事"，请你判断这件事适不适合拍成短视频。
只输出下面这个JSON格式，不要输出任何多余的文字、也不要用markdown代码块包裹：

{
  "category": "上面四类中的一类；如果都不沾边，就填 其他",
  "grade": "A 或 B 或 C。A=值得优先拍，B=可以拍但不紧迫，C=不建议拍",
  "reason": "1到2句话，说明为什么值得拍或者不值得拍",
  "conflict": "这件事里的核心冲突或反差是什么；如果没有，就写 无明显冲突",
  "angles": ["推荐的选题角度1", "推荐的选题角度2"],
  "privacy_risk": "低 或 中 或 高。评估拍出来是否可能暴露他人隐私或引发麻烦"
}

angles 数组里给1到2个角度即可，没有第二个角度就只放1个。
"""


def _clean_json_text(text: str) -> str:
    """有些模型会习惯性地把JSON包在```json ... ```里，这里简单处理掉。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def analyze_event(raw_text: str) -> tuple[dict, str]:
    """
    调用AI分析一条生活事件。
    返回一个元组：(解析后的字典, AI原始返回的文本)
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.3,
    )
    raw_content = response.choices[0].message.content or ""
    cleaned = _clean_json_text(raw_content)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # AI没有按格式返回时，不要让程序崩溃，给一个能看懂的兜底结果
        data = {
            "category": "解析失败",
            "grade": "-",
            "reason": "AI返回的内容不是合法的JSON，请查看下方原始返回内容。",
            "conflict": "-",
            "angles": [],
            "privacy_risk": "-",
        }

    return data, raw_content
