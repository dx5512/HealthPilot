import streamlit as st
import requests
import json
import os
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import time
import numpy as np
import pandas as pd
from datetime import datetime
from folium.plugins import HeatMap

# === 1. 页面基础配置 ===
st.set_page_config(
    page_title="智域卫康——社区慢病风险智能治理支撑系统",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# === 辅助函数：加载社区地图数据 ===
@st.cache_data(ttl=5)
def load_community_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'community_mock_data.json')
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


# === 辅助函数：加载历史病例档案 ===
@st.cache_data(ttl=10)
def load_medical_records():
    """
    读取 backend/reports 目录下的所有 JSON 文件
    组装成一个列表用于表格展示
    """
    records_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    if not os.path.exists(records_dir):
        return []

    all_records = []
    # 遍历文件夹
    for filename in os.listdir(records_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(records_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 提取关键字段用于表格显示
                    record = {
                        "档案文件": filename,
                        "居民ID": data.get('user_id', '未知'),
                        "时间": data.get('timestamp', '未知'),
                        "风险等级": data.get('risk_assessment', {}).get('level', '未知'),
                        "收缩压": data.get('vitals', {}).get('systolic', 0),
                        "舒张压": data.get('vitals', {}).get('diastolic', 0),
                        # 我们把完整的报告内容也存进去，方便点击查看
                        "full_content": data
                    }
                    all_records.append(record)
            except Exception as e:
                print(f"读取文件失败 {filename}: {e}")

    # 按时间倒序排列 (最新的在最上面)
    all_records.sort(key=lambda x: x['时间'], reverse=True)
    return all_records


# === 2. 侧边栏导航 ===
with st.sidebar:
    selected = option_menu(
        menu_title="主菜单",
        options=["健康分析", "社区态势感知", "历史档案", "系统设置"],
        icons=["activity", "geo-alt", "journal-text", "gear"],
        menu_icon="cast",
        default_index=0,
    )

# === 模块 A：个人健康分析 (保持不变) ===
if selected == "健康分析":
    st.title("🏥 智域卫康—社区慢病风险智能治理支撑系统")
    st.caption("基于 XGBoost + RAG + LLM 的全流程智能诊断")

    with st.expander("📝 录入居民体征", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            user_id = st.text_input("居民 ID", value="current_user_001")
            age = st.number_input("年龄", min_value=0, max_value=120, value=65)
            systolic = st.number_input("收缩压", min_value=60, max_value=250, value=120)
        with col2:
            height = st.number_input("身高", min_value=100, max_value=250, value=170)
            diastolic = st.number_input("舒张压", min_value=40, max_value=150, value=80)
            heart_rate = st.number_input("心率", min_value=40, max_value=200, value=95)
        with col3:
            weight = st.number_input("体重", min_value=30.0, max_value=150.0, value=65.0)
            spo2 = st.number_input("血氧 (%)", min_value=70.0, max_value=100.0, value=98.0)

    if st.button("🚀 开始智能分析", type="primary"):
        payload = {
            "user_id": user_id, "systolic": systolic, "diastolic": diastolic,
            "heart_rate": heart_rate, "spo2": spo2, "height": height,
            "weight": weight, "age": age
        }
        API_URL = "http://127.0.0.1:8000/api/v1/analyze/risk"

        with st.spinner("🤖 正在进行风险计算与智能分析..."):
            try:
                response = requests.post(API_URL, json=payload, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    risk_level = result.get('risk_level', '未知')
                    risk_score = result.get('risk_score', 0.0)

                    # 简化的结果显示
                    if risk_level == "高危":
                        emoji = "🔴"
                    elif risk_level == "中风险":
                        emoji = "🟡"
                    else:
                        emoji = "🟢"

                    st.markdown(f"### {emoji} 风险等级: **{risk_level}** (得分: {risk_score:.2f})")
                    st.divider()

                    col_left, col_right = st.columns([2, 1])
                    with col_left:
                        st.subheader("📝 AI 健康建议")
                        st.markdown(result.get('health_advice', ''))
                    with col_right:
                        st.subheader("📚 参考依据")
                        refs = result.get('guideline_refs', [])
                        if refs:
                            for ref in refs: st.info(f"📄 {ref}")

                    st.success("✅ 分析完成！数据已同步至地图和档案库。")
                    st.cache_data.clear()  # 清除缓存以刷新其他页面
                else:
                    st.error(f"后端异常: {response.text}")
            except Exception as e:
                st.error(f"连接失败: {e}")

# === 模块 B：社区态势感知 (混合模式：散点图 + 热力图) ===
elif selected == "社区态势感知":
    st.title("🗺️ 社区慢病风险态势感知")
    st.caption("实时监测：山东省青岛市西海岸新区三沙路1777号 | 底层热力展示风险密度，上层散点支持交互查询")

    residents = load_community_data()

    if not residents:
        st.warning("暂无数据")
    else:
        # 1. 顶部统计指标
        total = len(residents)
        high_risk = len([r for r in residents if r['status'] == '高危'])
        medium_risk = len([r for r in residents if r['status'] == '中风险'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("监测总人数", total)
        col2.metric("🔴 高危人数", high_risk, delta_color="inverse")
        col3.metric("🟡 关注人数", medium_risk)
        col4.metric("🟢 健康", total - high_risk - medium_risk)

        st.divider()

        # 2. 地图初始化
        avg_lat = sum([r['lat'] for r in residents]) / len(residents)
        avg_lng = sum([r['lng'] for r in residents]) / len(residents)

        # 使用 CartoDB positron 浅色底图，让热力图颜色更正
        m = folium.Map(location=[avg_lat, avg_lng], zoom_start=16, tiles="CartoDB positron")

        # ==========================================
        # 第一层：底层热力图
        # 作用：展示风险的空间聚集程度
        # ==========================================
        heat_data = []

        for r in residents:
            # 根据风险等级定义热力权重
            # 高危权重设大，让该区域显示为红色；低风险权重小，显示为蓝色
            if r['status'] == "高危":
                weight = 80
            elif r['status'] == "中风险":
                weight = 40
            else:
                weight = 5

            # HeatMap 格式: [lat, lng, weight]
            heat_data.append([r['lat'], r['lng'], weight])

        # 添加热力图层
        HeatMap(
            heat_data,
            min_opacity=0.4,
            max_opacity=0.8,
            radius=80,  # 光晕半径
            blur=30,  # 模糊度
            gradient={
                0.2: 'blue',
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
        ).add_to(m)

        # ==========================================
        # 第二层：顶层散点图
        # 作用：支持用户点击交互，查看具体信息
        # ==========================================
        for r in residents:
            is_current = r.get('is_current_user', False)

            # 弹窗内容
            html_content = f"""
            <h4>{r['name']}</h4>
            <b>状态:</b> {r['status']}<br>
            <b>血压:</b> {r['systolic']}/{r['diastolic']} mmHg<br>
            <b>更新:</b> {r['last_update']}<br>
            """

            # === 特殊处理：当前测试用户 (最醒目，覆盖在最上层) ===
            if is_current:
                # 使用自定义 HTML 图标，让它变大、变蓝、会闪烁
                icon_html = """
                <div style="font-size: 28px; color: #0078FF; animation: blink 1s infinite; text-shadow: 2px 2px 4px #fff;">
                    <i class="fa fa-user" aria-hidden="true"></i>
                </div>
                <style>
                @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
                </style>
                """
                icon = folium.DivIcon(
                    html=icon_html,
                    icon_size=(150, 36),
                    icon_anchor=(18, 18)
                )

                # 先加一个大的半透明蓝色圆圈作为背景光晕，防止被热力图淹没
                folium.CircleMarker(
                    location=[r['lat'], r['lng']],
                    radius=25,  # 非常大
                    color='#0078FF',
                    fill=True,
                    fill_color='#0078FF',
                    fill_opacity=0.2,
                    stroke=False
                ).add_to(m)

                # 再加具体的 Marker
                folium.Marker(
                    location=[r['lat'], r['lng']],
                    popup=folium.Popup(f"<b>【当前测试用户】</b><br>{html_content}", max_width=300),
                    tooltip="📍 当前测试用户 (点击查看)",
                    icon=icon
                ).add_to(m)

            else:
                # === 普通用户：标准散点标记 ===
                if r['status'] == "高危":
                    color = "red"
                elif r['status'] == "中风险":
                    color = "orange"
                else:
                    color = "green"

                folium.Marker(
                    location=[r['lat'], r['lng']],
                    popup=folium.Popup(html_content, max_width=300),
                    tooltip=f"{r['name']} ({r['status']})",
                    icon=folium.Icon(color=color, icon="circle", prefix='fa')
                ).add_to(m)

        # 渲染地图
        st_folium(m, width=1200, height=650)

        # 底部图例说明
        st.markdown("""
        **交互说明：**
        - **热力背景**：颜色越红，代表该区域风险聚集程度越高。
        - **散点图标**：🔴高危 🟠中风险 🟢健康，点击可查看详细档案。
        - **蓝色闪烁大图标**：当前刚测试/录入的居民位置。
        """)

# === 模块 C：历史档案 (新增模块) ===
elif selected == "历史档案":
    st.title("📚 历史病例档案库")
    st.caption("所有 AI 生成的诊断记录均在此留存，可供追溯和审计")

    records = load_medical_records()

    if not records:
        st.info("暂无历史记录，请先进行健康分析。")
    else:
        st.write(f"共找到 **{len(records)}** 份诊断记录：")

        # 将数据转换为 DataFrame 方便展示
        df = pd.DataFrame(records)

        # 使用 Streamlit 的数据编辑器/表格
        # 我们只展示关键列，隐藏 full_content
        display_df = df[["时间", "居民ID", "风险等级", "收缩压", "舒张压", "档案文件"]]

        # 这里的 config_options 可以让特定列有颜色
        st.dataframe(
            display_df,
            column_config={
                "风险等级": st.column_config.TextColumn(
                    "风险等级",
                    help="AI评估的风险等级",
                    width="medium",
                ),
                "档案文件": st.column_config.LinkColumn(
                    "查看详情",  # 实际上不能直接下载，这里只是展示文件名
                    display_text="查看报告"
                )
            },
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # 点击交互：选择某一行查看详细报告
        st.subheader("📄 报告详情查看")
        selected_index = st.selectbox(
            "选择一条记录查看详细内容",
            range(len(records)),
            format_func=lambda x: f"{records[x]['时间']} - {records[x]['居民ID']} ({records[x]['风险等级']})"
        )

        if selected_index is not None:
            record = records[selected_index]

            # 直接展示 Markdown 格式的报告
            st.markdown("### 📄 AI 智能诊断报告")
            st.divider()

            # 渲染 Markdown 内容
            st.markdown(record['full_content'].get('ai_report', '暂无报告内容'))

            # 可选：底部小字显示引用的指南来源
            refs = record['full_content'].get('rag_references', [])
            if refs:
                with st.expander("查看参考指南来源"):
                    for ref in refs:
                        st.caption(f"📄 {ref}")

# === 模块 D：系统设置 ===
elif selected == "系统设置":
    st.title("⚙️ 系统设置")
    st.write("当前版本: v1.0.0")
    if st.button("清空缓存数据"):
        st.cache_data.clear()
        st.success("缓存已清空！")