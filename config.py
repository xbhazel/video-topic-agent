"""
配置读取模块：统一从这里拿配置值，不用关心现在是本地跑还是部署在云上。

- 本地开发：从项目目录下的 .env 文件读取
- 部署到 Streamlit Cloud：从网站后台设置的 Secrets 读取（st.secrets）

db.py 和 ai.py 都通过 get_config() 拿配置，不用各自判断"现在是哪种环境"。
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_config(key: str, default=None):
    # 部署到 Streamlit Cloud 后，密钥配置在网站后台的 Secrets 里
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # 本地用 `python xxx.py` 直接跑（不经过 streamlit run）时，st.secrets 可能取不到，
        # 这里不让它报错，直接往下走，改成读 .env
        pass

    return os.getenv(key, default)
