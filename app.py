import hashlib
import hmac
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="ScenarioForge | Digital Business Scenario Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#edf2f7; --muted:#97a6ba; --panel:#111a2b; --panel2:#162239; --accent:#63e6be; --blue:#7aa7ff; }
    html, body, [class*="css"] { font-family:'DM Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 75% -10%, #1d3357 0, #0a1120 38%, #070b14 100%); color:var(--ink); }
    h1,h2,h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:-.03em; }
    h1 { font-size:2.35rem !important; margin-bottom:.15rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#0d1728,#0a1020); border-right:1px solid #263650; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color:#dbe6f5 !important; }
    .eyebrow { color:var(--accent); text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; font-weight:700; }
    .subtitle { color:var(--muted); font-size:1rem; margin-bottom:1.2rem; }
    .panel { background:rgba(17,26,43,.78); border:1px solid #263650; border-radius:18px; padding:1.15rem 1.25rem; box-shadow:0 15px 45px rgba(0,0,0,.16); }
    .scenario-badge { display:inline-block; background:rgba(99,230,190,.12); border:1px solid rgba(99,230,190,.35); color:#9af3d2; padding:.35rem .7rem; border-radius:99px; font-size:.78rem; font-weight:600; }
    .kpi-label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
    .kpi-value { font-family:'Space Grotesk'; font-size:1.65rem; font-weight:700; color:#f7fbff; margin-top:.25rem; }
    .kpi-delta { font-size:.78rem; margin-top:.25rem; }
    .positive { color:#63e6be; } .negative { color:#ff8e8e; } .neutral { color:#97a6ba; }
    .stSlider [data-baseweb="slider"] { margin-top:-.2rem; }
    div[data-testid="stMetric"] { background:#111a2b; border:1px solid #263650; padding:1rem; border-radius:14px; }
    </style>
    """, unsafe_allow_html=True,
)

# ---------- Secure admin authentication ----------
def _password_matches(password: str, stored_value: str) -> bool:
    """Validate a PBKDF2 password hash stored as salt_hex:hash_hex."""
    try:
        salt_hex, expected_hex = stored_value.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


def require_admin() -> None:
    """Gate the dashboard behind credentials stored in Streamlit Secrets."""
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.success("تم تسجيل الدخول كمسؤول")
            if st.button("تسجيل الخروج", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()
        return

    st.markdown("<div style='max-width:520px;margin:8vh auto 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">SCENARIOFORGE / ADMIN ACCESS</div>', unsafe_allow_html=True)
    st.title("تسجيل دخول الإدارة")
    st.markdown('<div class="subtitle">أدخل بيانات المسؤول للوصول إلى محرك السيناريوهات.</div>', unsafe_allow_html=True)
    with st.form("admin_login"):
        username = st.text_input("اسم المستخدم", placeholder="admin")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول آمن", use_container_width=True)
    if submitted:
        try:
            admin_config = st.secrets.get("admin", {})
        except Exception:
            admin_config = {}
        expected_username = admin_config.get("username", "")
        stored_hash = admin_config.get("password_hash", "")
        if not expected_username or not stored_hash:
            # Demo-only fallback. Replace with Streamlit Secrets for any real deployment.
            expected_username = "admin"
            stored_hash = "1b4c1bac112448be9e3635fb340d4f94:8851dd13377bcc36a4aa5064a4c2a490938006cc56f3bd301d9e5a73101e36f2"
        if username == expected_username and _password_matches(password, stored_hash):
            st.session_state.authenticated = True
            st.rerun()
        st.error("بيانات الدخول غير صحيحة.")
    st.caption("نسخة الديمو تستخدم بيانات دخول عامة للعرض فقط؛ لا تستخدمها مع بيانات حقيقية.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


require_admin()

# ---------- Calculation engine ----------
def calculate(fixed_costs: float, variable_cost: float, price: float, units: float) -> dict:
    contribution = price - variable_cost
    revenue = price * units
    variable_total = variable_cost * units
    profit = revenue - variable_total - fixed_costs
    margin = contribution / price if price > 0 else 0
    break_even = fixed_costs / contribution if contribution > 0 else float("inf")
    return {
        "revenue": revenue, "variable_total": variable_total, "profit": profit,
        "contribution": contribution, "margin": margin, "break_even": break_even,
        "units": units, "fixed_costs": fixed_costs, "variable_cost": variable_cost, "price": price,
    }

def money(value: float) -> str:
    if value == float("inf"):
        return "غير ممكن"
    return f"{value:,.0f}"

def pct(value: float) -> str:
    return f"{value:+.1%}"

# ---------- Sidebar inputs ----------
with st.sidebar:
    st.markdown('<div class="eyebrow">INPUT DASHBOARD</div>', unsafe_allow_html=True)
    st.header("بيانات النشاط الحالية")
    currency = st.selectbox("العملة", ["USD — دولار أمريكي", "SAR — ريال سعودي", "AED — درهم إماراتي", "EGP — جنيه مصري"], index=0)
    currency_code = currency.split(" ")[0]
    st.caption("أدخل أرقام الشهر الحالي. جميع النتائج تقديرية لدعم القرار وليست بديلاً عن المحاسبة.")
    fixed = st.number_input("التكاليف الثابتة الشهرية", min_value=0.0, value=8500.0, step=500.0)
    variable = st.number_input("التكلفة المتغيرة لكل وحدة", min_value=0.0, value=18.0, step=1.0)
    price = st.number_input("سعر البيع الحالي للوحدة", min_value=0.01, value=42.0, step=1.0)
    units = st.number_input("حجم المبيعات الشهري (وحدة)", min_value=0.0, value=900.0, step=50.0)
    st.divider()
    st.markdown('<div class="eyebrow">SCENARIO SLIDERS</div>', unsafe_allow_html=True)
    st.header("اختبر ماذا لو؟")
    price_change = st.slider("تغيير سعر البيع", -50, 100, 10, 1, format="%d%%")
    variable_change = st.slider("تغيير تكلفة الوحدة", -50, 100, -5, 1, format="%d%%")
    fixed_change = st.slider("تغيير التكاليف الثابتة", -50, 100, 8, 1, format="%d%%")
    volume_change = st.slider("تغيير حجم المبيعات", -50, 200, 15, 1, format="%d%%")

current = calculate(fixed, variable, price, units)
scenario = calculate(
    fixed * (1 + fixed_change / 100),
    variable * (1 + variable_change / 100),
    price * (1 + price_change / 100),
    units * (1 + volume_change / 100),
)

# ---------- Header ----------
st.markdown('<div class="eyebrow">DIGITAL BUSINESS INTELLIGENCE / 01</div>', unsafe_allow_html=True)
st.title("ScenarioForge")
st.markdown('<div class="subtitle">محرك سيناريوهات الأعمال الرقمية — حوّل افتراضاتك إلى قرارات أوضح.</div>', unsafe_allow_html=True)
st.markdown('<span class="scenario-badge">● LIVE SCENARIO SIMULATION</span>', unsafe_allow_html=True)
st.write("")

# ---------- KPI strip ----------
profit_delta = scenario["profit"] - current["profit"]
be_delta = scenario["break_even"] - current["break_even"] if scenario["break_even"] != float("inf") else 0
cols = st.columns(4)
with cols[0]:
    st.markdown(f'<div class="panel"><div class="kpi-label">الربح الشهري المتوقع</div><div class="kpi-value">{money(scenario["profit"])} {currency_code}</div><div class="kpi-delta {"positive" if profit_delta >= 0 else "negative"}">{pct(profit_delta / abs(current["profit"]) if current["profit"] else 0)} مقابل الوضع الحالي</div></div>', unsafe_allow_html=True)
with cols[1]:
    st.markdown(f'<div class="panel"><div class="kpi-label">نقطة التعادل</div><div class="kpi-value">{money(scenario["break_even"])} وحدة</div><div class="kpi-delta {"positive" if be_delta <= 0 else "negative"}">{money(abs(be_delta))} وحدة {"أقل" if be_delta <= 0 else "أعلى"}</div></div>', unsafe_allow_html=True)
with cols[2]:
    st.markdown(f'<div class="panel"><div class="kpi-label">هامش المساهمة</div><div class="kpi-value">{scenario["margin"]:.1%}</div><div class="kpi-delta neutral">لكل وحدة مباعة</div></div>', unsafe_allow_html=True)
with cols[3]:
    st.markdown(f'<div class="panel"><div class="kpi-label">الإيرادات الشهرية</div><div class="kpi-value">{money(scenario["revenue"])} {currency_code}</div><div class="kpi-delta positive">{pct((scenario["revenue"]-current["revenue"])/current["revenue"] if current["revenue"] else 0)} نمو</div></div>', unsafe_allow_html=True)

st.write("")
# ---------- Comparison charts ----------
left, right = st.columns([1, 1])
plot_template = "plotly_dark"
with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("مقارنة الأداء المالي")
    comparison = pd.DataFrame({"المؤشر": ["الإيرادات", "التكاليف المتغيرة", "الربح"], "الوضع الحالي": [current["revenue"], current["variable_total"], current["profit"]], "السيناريو المقترح": [scenario["revenue"], scenario["variable_total"], scenario["profit"]]})
    fig = go.Figure()
    fig.add_bar(name="الوضع الحالي", x=comparison["المؤشر"], y=comparison["الوضع الحالي"], marker_color="#526581")
    fig.add_bar(name="السيناريو المقترح", x=comparison["المؤشر"], y=comparison["السيناريو المقترح"], marker_color="#63e6be")
    fig.update_layout(template=plot_template, barmode="group", height=360, margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation="h", y=1.12), yaxis_title=currency_code)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("منحنى الربحية ونقطة التعادل")
    volume_range = [max(1, int(units * x / 100)) for x in range(25, 226, 10)]
    current_profit_line = [calculate(fixed, variable, price, v)["profit"] for v in volume_range]
    scenario_profit_line = [calculate(scenario["fixed_costs"], scenario["variable_cost"], scenario["price"], v)["profit"] for v in volume_range]
    line = go.Figure()
    line.add_trace(go.Scatter(x=volume_range, y=current_profit_line, name="الوضع الحالي", mode="lines", line=dict(color="#7aa7ff", width=3)))
    line.add_trace(go.Scatter(x=volume_range, y=scenario_profit_line, name="السيناريو المقترح", mode="lines", line=dict(color="#63e6be", width=3)))
    line.add_hline(y=0, line_dash="dot", line_color="#8493a9")
    line.update_layout(template=plot_template, height=360, margin=dict(l=10,r=10,t=10,b=10), legend=dict(orientation="h", y=1.12), xaxis_title="الوحدات المباعة", yaxis_title=f"الربح ({currency_code})")
    st.plotly_chart(line, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Break-even analysis ----------
st.write("")
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("حاسبة نقطة التعادل")
st.markdown("نقطة التعادل = **التكاليف الثابتة ÷ (سعر البيع − التكلفة المتغيرة لكل وحدة)**. عندما يكون هامش المساهمة موجبًا، تمثل النتيجة الحد الأدنى التقريبي من الوحدات اللازمة لتغطية التكاليف.")
be_cols = st.columns(2)
for col, label, data in [(be_cols[0], "الوضع الحالي", current), (be_cols[1], "السيناريو المقترح", scenario)]:
    with col:
        st.markdown(f"**{label}**")
        st.metric("وحدات التعادل", "غير ممكن" if data["break_even"] == float("inf") else f"{data['break_even']:,.0f}")
        st.progress(min(1.0, data["units"] / data["break_even"]) if data["break_even"] not in (0, float("inf")) else 0.0, text=f"تغطية {min(100, data['units']/data['break_even']*100) if data['break_even'] not in (0,float('inf')) else 0:.0f}% من نقطة التعادل")
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Detail table and insight ----------
st.write("")
info_col, table_col = st.columns([.85, 1.15])
with info_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("قراءة سريعة للسيناريو")
    if scenario["profit"] > current["profit"]:
        st.success("السيناريو المقترح يحسن الربحية الشهرية مقارنة بخط الأساس.")
    else:
        st.warning("السيناريو المقترح يخفض الربحية؛ راجع تأثير الأسعار أو التكاليف قبل التنفيذ.")
    if scenario["break_even"] < current["break_even"]:
        st.info("انخفضت نقطة التعادل، ما يعني أن النشاط يحتاج إلى وحدات أقل لتغطية تكاليفه.")
    else:
        st.info("ارتفعت نقطة التعادل؛ راقب التكاليف الثابتة والمتغيرة وحجم الطلب المتوقع.")
    st.markdown('</div>', unsafe_allow_html=True)
with table_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("تفاصيل الافتراضات")
    detail = pd.DataFrame({"المتغير": ["سعر البيع / وحدة", "التكلفة المتغيرة / وحدة", "التكاليف الثابتة", "حجم المبيعات"], "الحالي": [f"{current['price']:,.2f}", f"{current['variable_cost']:,.2f}", f"{current['fixed_costs']:,.0f}", f"{current['units']:,.0f}"], "السيناريو": [f"{scenario['price']:,.2f}", f"{scenario['variable_cost']:,.2f}", f"{scenario['fixed_costs']:,.0f}", f"{scenario['units']:,.0f}"], "التغير": [pct(price_change/100), pct(variable_change/100), pct(fixed_change/100), pct(volume_change/100)]})
    st.dataframe(detail, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("ScenarioForge • أداة تعليمية لاتخاذ القرار المبني على البيانات • النتائج تعتمد على الافتراضات المدخلة")
