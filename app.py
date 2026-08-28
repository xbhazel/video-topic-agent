"""
网页入口：用 Streamlit 做一个最简单的网页。
运行方式见 README.md，一句话是：streamlit run app.py
"""

import streamlit as st
from config import get_config
from db import init_db, save_event, get_all_events
from ai import analyze_event

st.set_page_config(page_title="短视频选题助手", page_icon="🎬")

GRADE_ICON = {"A": "🟢", "B": "🟡", "C": "🔴"}


# ---------- 密码门：全家共用一个密码，防止陌生人看到你们的记录 ----------
def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("🎬 短视频选题 Agent")
    correct_password = get_config("APP_PASSWORD")

    if not correct_password:
        st.warning(
            "还没有配置 APP_PASSWORD，任何人都能直接进入。\n\n"
            "本地开发在 .env 里加一行 `APP_PASSWORD=你定的密码`；"
            "部署到 Streamlit Cloud 在后台 Secrets 里加。"
        )
        st.session_state["authenticated"] = True
        st.rerun()

    pwd = st.text_input("请输入密码", type="password")
    if st.button("进入"):
        if pwd == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密码不对，再试试")
    return False


if not check_password():
    st.stop()


# ---------- 数据库初始化：没配好 DATABASE_URL 时给出清晰提示，而不是白屏报错 ----------
try:
    init_db()
except Exception as e:
    st.error(
        f"数据库连接失败，请检查 DATABASE_URL 配置是否正确。\n\n错误信息：{e}"
    )
    st.stop()


st.title("🎬 短视频选题 Agent（MVP）")
st.caption("输入生活事件 → AI判断 → 保存 → 以后可以查看")

tab_new, tab_history = st.tabs(["✍️ 记录新事件", "📚 历史记录"])

# ---------- Tab 1：记录新事件 ----------
with tab_new:
    st.subheader("今天发生了什么？")

    # 用 st.form 包住输入框：加 clear_on_submit=True 后，
    # 点击提交按钮那一刻，Streamlit 会自动把表单里的输入框清空，不用自己手动清。
    with st.form("new_event_form", clear_on_submit=True):
        raw_text = st.text_area(
            "把今天发生的事情写下来，越具体越好",
            placeholder="例如：Food Bank 同事告诉我她下周会被 lay off。",
            height=120,
        )
        submitted = st.form_submit_button("🚀 让 AI 判断这个选题", type="primary")

    if submitted:
        if not raw_text.strip():
            st.warning("先写点什么吧～")
        else:
            with st.spinner("AI 正在判断..."):
                try:
                    analysis, raw_response = analyze_event(raw_text)
                    save_event(raw_text, analysis, raw_response)
                except Exception as e:
                    st.error(f"调用AI失败，请检查 API Key / BASE_URL 配置是否正确。\n\n错误信息：{e}")
                    st.stop()

            st.success("分析完成，已保存！")

            icon = GRADE_ICON.get(analysis.get("grade"), "⚪")
            st.markdown(f"### {icon} 选题等级：{analysis.get('grade', '-')}")
            st.markdown(f"**内容分类**：{analysis.get('category', '-')}")
            st.markdown(f"**隐私风险**：{analysis.get('privacy_risk', '-')}")
            st.markdown(f"**为什么值得/不值得拍**：{analysis.get('reason', '-')}")
            st.markdown(f"**核心冲突/反差**：{analysis.get('conflict', '-')}")
            st.markdown("**推荐选题角度**：")
            for angle in analysis.get("angles") or []:
                st.markdown(f"- {angle}")

# ---------- Tab 2：历史记录 ----------
with tab_history:
    st.subheader("以前保存过的事件")
    events = get_all_events()

    if not events:
        st.info("还没有记录，先去左边的 Tab 记一条吧。")
    else:
        grade_filter = st.multiselect(
            "按等级筛选", ["A", "B", "C"], default=["A", "B", "C"]
        )
        for e in events:
            if e["grade"] not in grade_filter:
                continue
            icon = GRADE_ICON.get(e["grade"], "⚪")
            created_str = e["created_at"].strftime("%Y-%m-%d %H:%M")
            title = f"{icon} [{e['grade']}] {e['raw_text'][:30]}  —  {created_str}"
            with st.expander(title):
                st.markdown(f"**原始事件**：{e['raw_text']}")
                st.markdown(f"**内容分类**：{e['category']}")
                st.markdown(f"**隐私风险**：{e['privacy_risk']}")
                st.markdown(f"**为什么值得/不值得拍**：{e['reason']}")
                st.markdown(f"**核心冲突/反差**：{e['conflict']}")
                st.markdown(f"**推荐选题角度**：\n\n{e['angles']}")
