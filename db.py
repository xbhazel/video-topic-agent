"""
数据库模块：负责建表、存数据、读数据。

用的是 Postgres（Supabase 提供的免费云数据库），不再用本地 SQLite 文件了。
原因：部署到 Streamlit Cloud 之后，网页应用所在的容器不是永久保存的，
本地文件说没就没；换成云数据库之后，数据库和网页应用是分开的两个东西，
网页应用重启/休眠都不会影响已经存的数据，你和家人也能共享同一份数据。
"""

import psycopg2
import psycopg2.extras
from config import get_config


def get_conn():
    """打开一个数据库连接。"""
    database_url = get_config("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "没有配置 DATABASE_URL。本地开发请在 .env 里填好；"
            "部署到 Streamlit Cloud 请在网站后台的 Secrets 里填好。"
        )
    return psycopg2.connect(database_url)


def init_db():
    """建表，如果表已经存在就什么都不做。"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    raw_text TEXT NOT NULL,
                    category TEXT,
                    grade TEXT,
                    reason TEXT,
                    conflict TEXT,
                    angles TEXT,
                    privacy_risk TEXT,
                    raw_ai_response TEXT
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def save_event(raw_text: str, analysis: dict, raw_ai_response: str):
    """把一条事件和它的AI分析结果存进数据库。"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events
                    (raw_text, category, grade, reason, conflict, angles, privacy_risk, raw_ai_response)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    raw_text,
                    analysis.get("category", ""),
                    analysis.get("grade", ""),
                    analysis.get("reason", ""),
                    analysis.get("conflict", ""),
                    "\n".join(analysis.get("angles", []) or []),
                    analysis.get("privacy_risk", ""),
                    raw_ai_response,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_all_events():
    """按时间倒序拿到所有历史记录（最新的在最前面）。"""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM events ORDER BY id DESC")
            return cur.fetchall()
    finally:
        conn.close()
