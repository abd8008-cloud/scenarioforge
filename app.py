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
    :root { --ink:#172033; --muted:#667085; --panel:#ffffff; --panel2:#f5f8fc; --accent:#087f5b; --blue:#2457c5; }
    html, body, [class*="css"] { font-family:'DM Sans', sans-serif; }
    .stApp { background:linear-gradient(135deg,#f7f9fc 0%,#eef3f9 100%); color:var(--ink); }
    h1,h2,h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:-.03em; color:#14213d; }
    h1 { font-size:2.35rem !important; margin-bottom:.15rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#ffffff,#f1f5fa); border-right:1px solid #d9e2ef; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color:#172033 !important; }
    .eyebrow { color:var(--accent); text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; font-weight:700; }
    .subtitle { color:var(--muted); font-size:1rem; margin-bottom:1.2rem; }
    .panel { background:rgba(255,255,255,.96); border:1px solid #d9e2ef; border-radius:18px; padding:1.15rem 1.25rem; box-shadow:0 10px 30px rgba(30,55,90,.08); }
    .scenario-badge { display:inline-block; background:#e5f7f0; border:1px solid #9adbc5; color:#087f5b; padding:.35rem .7rem; border-radius:99px; font-size:.78rem; font-weight:600; }
    .kpi-label { color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
    .kpi-value { font-family:'Space Grotesk'; font-size:1.65rem; font-weight:700; color:#14213d; margin-top:.25rem; }
    .kpi-delta { font-size:.78rem; margin-top:.25rem; }
    .positive { color:#087f5b; } .negative { color:#c92a2a; } .neutral { color:#667085; }
    .stSlider [data-baseweb="slider"] { margin-top:-.2rem; }
    div[data-testid="stMetric"] { background:#ffffff; border:1px solid #d9e2ef; padding:1rem; border-radius:14px; }
    div.stButton > button, div.stFormSubmitButton > button { border-radius:10px; min-height:2.7rem; font-weight:700; border:1px solid #087f5b; background:#087f5b; color:#ffffff; transition:all .2s ease; }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover { border-color:#055c42; background:#055c42; color:#ffffff; box-shadow:0 5px 15px rgba(8,127,91,.22); }
    div.stFormSubmitButton > button { background:linear-gradient(135deg,#087f5b,#0ca678); border:none; font-size:1rem; }
    div.stFormSubmitButton > button:hover { background:linear-gradient(135deg,#066c4e,#087f5b); }
    .section-label { color:#087f5b; font-size:.75rem; font-weight:800; letter-spacing:.12em; margin-top:1.4rem; margin-bottom:.35rem; }
    .section-intro { color:#667085; margin-bottom:.8rem; }
    .login-card { max-width:520px; margin:8vh auto 0; padding:1rem .5rem; }
    .login-footer { margin-top:1.8rem; padding-top:1rem; border-top:1px solid #e4eaf2; text-align:center; color:#667085; font-size:.9rem; }
    .whatsapp-link { display:inline-block; margin-top:.6rem; padding:.65rem 1.2rem; border-radius:10px; background:#25D366; color:#ffffff !important; text-decoration:none !important; font-weight:700; }
    .whatsapp-link:hover { background:#1da851; }
    .help-card { background:#ffffff; border:1px solid #d9e2ef; border-radius:16px; padding:1.25rem; min-height:155px; box-shadow:0 8px 24px rgba(30,55,90,.06); }
    .step-number { display:inline-flex; width:30px; height:30px; border-radius:50%; align-items:center; justify-content:center; background:#e5f7f0; color:#087f5b; font-weight:800; margin-left:.4rem; }
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

    st.markdown('<div class="login-card" style="max-width:520px;margin:8vh auto 0;">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">SCENARIOFORGE / ADMIN ACCESS</div>', unsafe_allow_html=True)
    st.title("مرحبًا بك في ScenarioForge")
    st.markdown('<div class="subtitle">سجّل الدخول للوصول إلى لوحة تحليل السيناريوهات المالية.</div>', unsafe_allow_html=True)
    with st.form("admin_login"):
        username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول إلى لوحة التحليل", use_container_width=True)
    if submitted:
        try:
            admin_config = st.secrets.get("admin", {})
        except Exception:
            admin_config = {}
        expected_username = admin_config.get("username", "")
        stored_hash = admin_config.get("password_hash", "")
        if not expected_username or not stored_hash:
            st.error("لم يتم إعداد حساب الإدارة. أضف username و password_hash في Streamlit Secrets.")
            st.stop()
        if username == expected_username and _password_matches(password, stored_hash):
            st.session_state.authenticated = True
            st.rerun()
        st.error("بيانات الدخول غير صحيحة.")
    st.caption("الوصول محمي بحساب الإدارة. لا تُعرض بيانات الدخول داخل الواجهة.")
    st.markdown('<div class="login-footer"><strong>عبدالله محمد</strong><br><span>للاستفسارات والدعم المباشر</span><br><a class="whatsapp-link" href="https://wa.me/598727698" target="_blank">تواصل عبر واتساب</a><br><small>+598727698</small></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


require_admin()

# ---------- App navigation and guidance screens ----------
with st.sidebar:
    st.divider()
    st.markdown('<div class="eyebrow">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.radio("اختر الشاشة", ["لوحة التحليل", "كيفية الاستخدام", "عن ScenarioForge"], label_visibility="collapsed")

if page == "كيفية الاستخدام":
    st.markdown('<div class="eyebrow">QUICK START GUIDE</div>', unsafe_allow_html=True)
    st.title("كيف تستخدم محرك السيناريوهات؟")
    st.markdown('<div class="subtitle">أربع خطوات بسيطة لتحويل أرقام مشروعك إلى مقارنة تساعدك على اتخاذ القرار.</div>', unsafe_allow_html=True)
    guide = st.columns(4)
    steps = [("01", "اختر السوق", "اختر السعودية أو أي سوق آخر، وستتغير العملة المعروضة تلقائيًا."), ("02", "أدخل خط الأساس", "أدخل التكاليف الثابتة وتكلفة الوحدة والسعر وحجم المبيعات."), ("03", "اختبر ماذا لو؟", "حرّك الشرائح لاختبار رفع السعر أو خفض التكلفة أو زيادة المبيعات."), ("04", "اقرأ القرار", "قارن الربح ونقطة التعادل والهامش واختر الفرضية الأنسب.")]
    for column, (number, title, text) in zip(guide, steps):
        with column:
            st.markdown(f'<div class="help-card"><div class="step-number">{number}</div><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("ما البيانات التي أحتاجها؟")
    st.markdown("استخدم أرقام آخر شهر أو متوسط آخر ثلاثة أشهر من فواتيرك ونظام المبيعات. لا تخلط بين إجمالي المبيعات وعدد الوحدات، ولا تدخل المصروفات الشخصية ضمن تكاليف النشاط.")
    examples = pd.DataFrame({"المدخل": ["التكاليف الثابتة", "التكلفة المتغيرة للوحدة", "سعر البيع للوحدة", "حجم المبيعات"], "مثال": ["8,500", "18", "42", "900 وحدة"], "مصدر مقترح": ["إيجار ورواتب واشتراكات", "فواتير المواد والتغليف", "الفواتير أو قائمة الأسعار", "الكاشير أو تقارير المتجر"]})
    st.dataframe(examples, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if page == "عن ScenarioForge":
    st.markdown('<div class="eyebrow">ABOUT THE ENGINE</div>', unsafe_allow_html=True)
    st.title("عن ScenarioForge")
    st.markdown('<div class="subtitle">أداة تعليمية لاتخاذ القرار المبني على البيانات للمشاريع الصغيرة.</div>', unsafe_allow_html=True)
    about_cols = st.columns(3)
    about = [("محاكاة سريعة", "اختبر قرارات التسعير والتكلفة والمبيعات خلال ثوانٍ."), ("رؤية مالية", "افهم الربح وهامش المساهمة ونقطة التعادل في شاشة واحدة."), ("أسواق متعددة", "اعرض النتائج بعملات عربية ودولية حسب السوق المستهدف.")]
    for column, (title, text) in zip(about_cols, about):
        with column:
            st.markdown(f'<div class="help-card"><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)
    st.write("")
    st.info("النتائج تعتمد على الأرقام التي تدخلها. اختيار السوق يغيّر العملة والتنسيق، لكنه لا يجلب بيانات منافسين أو أسعارًا حية تلقائيًا.")
    st.stop()

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

# ---------- Markets and currencies ----------
MARKETS = {
    "السعودية": {"currency": "SAR", "currency_name": "ريال سعودي", "locale": "ar-SA"},
    "الإمارات": {"currency": "AED", "currency_name": "درهم إماراتي", "locale": "ar-AE"},
    "الكويت": {"currency": "KWD", "currency_name": "دينار كويتي", "locale": "ar-KW"},
    "قطر": {"currency": "QAR", "currency_name": "ريال قطري", "locale": "ar-QA"},
    "البحرين": {"currency": "BHD", "currency_name": "دينار بحريني", "locale": "ar-BH"},
    "عُمان": {"currency": "OMR", "currency_name": "ريال عُماني", "locale": "ar-OM"},
    "الأردن": {"currency": "JOD", "currency_name": "دينار أردني", "locale": "ar-JO"},
    "مصر": {"currency": "EGP", "currency_name": "جنيه مصري", "locale": "ar-EG"},
    "المغرب": {"currency": "MAD", "currency_name": "درهم مغربي", "locale": "ar-MA"},
    "الولايات المتحدة": {"currency": "USD", "currency_name": "دولار أمريكي", "locale": "en-US"},
    "المملكة المتحدة": {"currency": "GBP", "currency_name": "جنيه إسترليني", "locale": "en-GB"},
    "السوق الدولي": {"currency": "USD", "currency_name": "دولار أمريكي", "locale": "en-US"},
}

# ---------- Sidebar inputs ----------
with st.sidebar:
    st.markdown('<div class="eyebrow">INPUT DASHBOARD</div>', unsafe_allow_html=True)
    st.header("بيانات النشاط الحالية")
    market = st.selectbox("السوق المستهدف للتحليل", list(MARKETS.keys()), index=0)
    market_profile = MARKETS[market]
    currency_code = market_profile["currency"]
    st.caption(f"العملة المستخدمة: {market_profile['currency_name']} ({currency_code}) • المنطقة: {market_profile['locale']}")
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
st.caption(f"السوق المختار: {market} • العملة: {market_profile['currency_name']} ({currency_code})")
st.write("")

st.markdown('<div class="section-label">01 / EXECUTIVE SUMMARY</div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">ملخص سريع يوضح أثر السيناريو المقترح على مؤشرات النشاط الأساسية.</div>', unsafe_allow_html=True)
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
st.markdown('<div class="section-label">02 / FINANCIAL PERFORMANCE</div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">قارن الإيرادات والتكاليف والربح، ثم راقب تغير الربحية مع حجم المبيعات.</div>', unsafe_allow_html=True)
# ---------- Comparison charts ----------
left, right = st.columns([1, 1])
plot_template = "plotly_white"
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

st.markdown('<div class="section-label">03 / SCENARIO INSIGHTS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">استخدم تحليل الحساسية لفهم أكثر المتغيرات تأثيرًا، ثم راجع مكونات الربح قبل اعتماد السيناريو.</div>', unsafe_allow_html=True)
insight_left, insight_right = st.columns([1, 1])
with insight_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("حساسية الربح للسعر")
    sensitivity_changes = [-20, -10, 0, 10, 20]
    sensitivity_profits = [calculate(scenario["fixed_costs"], scenario["variable_cost"], scenario["price"] * (1 + change / 100), scenario["units"])["profit"] for change in sensitivity_changes]
    sensitivity = go.Figure(go.Bar(x=[f"{change:+d}%" for change in sensitivity_changes], y=sensitivity_profits, marker_color=["#f08c8c", "#ffb4a2", "#7aa7ff", "#63e6be", "#087f5b"], text=[money(value) for value in sensitivity_profits], textposition="outside"))
    sensitivity.update_layout(template=plot_template, height=340, margin=dict(l=10,r=10,t=20,b=10), xaxis_title="تغير السعر", yaxis_title=f"الربح ({currency_code})", showlegend=False)
    st.plotly_chart(sensitivity, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
with insight_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("جسر الربح: من الإيراد إلى النتيجة")
    waterfall = go.Figure(go.Waterfall(orientation="v", measure=["absolute", "relative", "relative", "total"], x=["الإيرادات", "التكاليف المتغيرة", "التكاليف الثابتة", "الربح"], y=[scenario["revenue"], -scenario["variable_total"], -scenario["fixed_costs"], scenario["profit"]], connector={"line": {"color": "#b8c7da"}}, increasing={"marker": {"color": "#63e6be"}}, decreasing={"marker": {"color": "#f08c8c"}}, totals={"marker": {"color": "#2457c5"}}))
    waterfall.update_layout(template=plot_template, height=340, margin=dict(l=10,r=10,t=20,b=10), yaxis_title=currency_code, showlegend=False)
    st.plotly_chart(waterfall, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">04 / BREAK-EVEN ANALYSIS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">اكتشف عدد الوحدات التي يجب بيعها لتغطية التكاليف في كل حالة.</div>', unsafe_allow_html=True)
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

st.markdown('<div class="section-label">05 / ASSUMPTIONS & INSIGHTS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">راجع الافتراضات المستخدمة والقراءة السريعة قبل اتخاذ أي قرار.</div>', unsafe_allow_html=True)
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
    st.caption("مقارنة منظمة بين خط الأساس والقيم الجديدة بعد تطبيق السيناريو.")
    detail = pd.DataFrame({"المتغير": ["سعر البيع / وحدة", "التكلفة المتغيرة / وحدة", "التكاليف الثابتة", "حجم المبيعات"], "الوضع الحالي": [f"{current['price']:,.2f}", f"{current['variable_cost']:,.2f}", f"{current['fixed_costs']:,.0f}", f"{current['units']:,.0f}"], "السيناريو المقترح": [f"{scenario['price']:,.2f}", f"{scenario['variable_cost']:,.2f}", f"{scenario['fixed_costs']:,.0f}", f"{scenario['units']:,.0f}"], "نسبة التغير": [pct(price_change/100), pct(variable_change/100), pct(fixed_change/100), pct(volume_change/100)]})
    st.dataframe(detail, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("ScenarioForge • أداة تعليمية لاتخاذ القرار المبني على البيانات • النتائج تعتمد على الافتراضات المدخلة")
