import streamlit as st
import requests
import pandas as pd
import base64
import os

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Inventory Control", page_icon=None, layout="wide", initial_sidebar_state="expanded")


def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGIN_BG = get_base64_image(os.path.join(os.path.dirname(__file__), "assets", "login-bg.jpg"))

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    :root {
        --ink:       #14181f;
        --ink-soft:  #3a4150;
        --line:      #d8dde3;
        --panel:     #ffffff;
        --bg:        #f4f5f7;
        --accent:    #b5530d;
        --ok:        #1a6b3c;
        --ok-bg:     #ecf6ef;
        --warn:      #946200;
        --warn-bg:   #fdf4e1;
        --crit:      #a32424;
        --crit-bg:   #fbe9e9;
        --mono:      'IBM Plex Mono', monospace;
    }

    .stApp { background: var(--bg); }
    #MainMenu, footer { visibility: hidden; }
    header { background: transparent !important; box-shadow: none !important; }

    [data-testid="stSidebar"] {
        min-width: 250px !important; max-width: 250px !important;
        width: 250px !important; transform: none !important;
        visibility: visible !important; background: var(--ink);
    }
    [data-testid="stSidebar"] * { color: #e7e9ec !important; }
    [data-testid="stSidebar"] hr { border-color: #3a4150; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    .block-container {
        padding-top: 1.4rem !important; padding-bottom: 1.4rem !important;
        padding-left: 2.2rem !important; padding-right: 2.2rem !important;
        max-width: 100% !important;
    }

    .topbar {
        display: flex; justify-content: space-between; align-items: baseline;
        border-bottom: 2px solid var(--ink); padding-bottom: 10px; margin-bottom: 18px;
    }
    .topbar-title { font-family: var(--mono); font-size: 1.05rem; font-weight: 700;
                    letter-spacing: 0.02em; color: var(--ink); text-transform: uppercase; }
    .topbar-sub   { font-family: var(--mono); font-size: 0.72rem; color: var(--ink-soft); letter-spacing: 0.04em; }

    .sec-label {
        font-family: var(--mono); font-size: 0.7rem; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-soft);
        border-bottom: 1px solid var(--line); padding-bottom: 6px; margin-bottom: 12px; margin-top: 4px;
    }

    .metric-row { display: flex; gap: 0; border: 1px solid var(--line); margin-bottom: 22px; background: var(--panel); }
    .metric-cell { flex: 1; padding: 14px 18px; border-right: 1px solid var(--line); }
    .metric-cell:last-child { border-right: none; }
    .metric-label { font-family: var(--mono); font-size: 0.66rem; font-weight: 600;
                    letter-spacing: 0.07em; text-transform: uppercase; color: var(--ink-soft); margin-bottom: 6px; }
    .metric-value { font-family: var(--mono); font-size: 1.7rem; font-weight: 700; color: var(--ink); line-height: 1; }
    .metric-value.warn { color: var(--warn); }
    .metric-value.crit { color: var(--crit); }
    .metric-value.ok   { color: var(--ok); }

    [data-testid="stDataFrame"] { border: 1px solid var(--line) !important; }
    [data-testid="stDataFrame"] * { font-family: var(--mono) !important; font-size: 0.8rem !important; }

    .stButton button {
        font-family: var(--mono); font-size: 0.78rem; font-weight: 600;
        letter-spacing: 0.03em; text-transform: uppercase; border-radius: 2px;
        border: 1px solid var(--ink); background: var(--ink); color: #fff; padding: 0.45rem 1rem;
    }
    .stButton button:hover { background: var(--accent); border-color: var(--accent); }

    .stTextInput input, .stNumberInput input, .stSelectbox > div, .stTextArea textarea {
        font-family: var(--mono) !important; font-size: 0.85rem !important;
        border-radius: 2px !important; border-color: var(--line) !important;
    }
    label { font-family: var(--mono) !important; font-size: 0.72rem !important;
            font-weight: 600 !important; text-transform: uppercase;
            letter-spacing: 0.04em; color: var(--ink-soft) !important; }

    [data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 0 !important; background: var(--panel); }
    h1, h2, h3 { font-family: var(--mono) !important; }
    .empty-state { font-family: var(--mono); font-size: 0.8rem; color: var(--ink-soft);
                   padding: 24px; text-align: center; border: 1px dashed var(--line); }
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────

def login(username, password):
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
    return res.json()["access_token"] if res.status_code == 200 else None

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_get(path, params=None):
    res = requests.get(f"{BASE_URL}{path}", headers=auth_headers(), params=params)
    return res.json() if res.status_code == 200 else []

def api_post(path, payload):
    return requests.post(f"{BASE_URL}{path}", headers=auth_headers(), json=payload)

def df(data):
    return pd.DataFrame(data) if data else pd.DataFrame()


# ── Login ─────────────────────────────────────────────────────

if "token" not in st.session_state:
    bg_style = f"""
        .login-hero {{
            position: fixed; inset: 0;
            background:
                linear-gradient(150deg, rgba(8,9,11,0.88) 0%, rgba(8,9,11,0.55) 50%, rgba(8,9,11,0.90) 100%),
                url("data:image/jpg;base64,{LOGIN_BG}");
            background-size: cover; background-position: center 35%;
            filter: grayscale(100%) contrast(1.05); z-index: 0;
        }}
    """ if LOGIN_BG else """
        .login-hero {
            position: fixed; inset: 0;
            background: linear-gradient(150deg, rgba(8,9,11,0.92) 0%, rgba(8,9,11,0.75) 55%, rgba(8,9,11,0.94) 100%),
                        radial-gradient(ellipse at 30% 20%, #4a4d52 0%, #1c1d1f 45%, #050506 100%);
            z-index: 0;
        }
    """

    st.markdown("""<style>.block-container { padding: 0 !important; max-width: 100% !important; }</style>"""
        + f"<style>{bg_style}</style>" + """
    <style>
        .login-brand { position: fixed; left: 6vw; top: 0; bottom: 0; display: flex;
                       flex-direction: column; justify-content: center; z-index: 1; max-width: 480px; }
        .login-eyebrow { font-family: 'IBM Plex Mono',monospace; font-size: 0.74rem; font-weight: 600;
                         letter-spacing: 0.14em; text-transform: uppercase; color: #9aa1ab; margin-bottom: 14px; }
        .login-heading { font-family: 'IBM Plex Mono',monospace; font-size: 2.6rem; font-weight: 700;
                         color: #f4f5f7; line-height: 1.15; margin-bottom: 18px; }
        .login-desc { font-family: 'IBM Plex Sans',sans-serif; font-size: 0.92rem; color: #b6bbc4;
                      line-height: 1.6; max-width: 380px; margin-bottom: 28px; }
        .login-meta { font-family: 'IBM Plex Mono',monospace; font-size: 0.72rem; color: #6b7280;
                      border-top: 1px solid #3a4150; padding-top: 14px; letter-spacing: 0.03em; }
        .login-card-wrap { position: fixed; right: 7vw; top: 50%; transform: translateY(-50%); z-index: 1; width: 360px; }
        .login-card-head { font-family: 'IBM Plex Mono',monospace; font-size: 0.78rem; font-weight: 700;
                           letter-spacing: 0.06em; text-transform: uppercase; color: #14181f;
                           background: #f4f5f7; padding: 12px 18px; border-bottom: 2px solid #14181f; }
        .login-card-body { background: #fff; padding: 22px 18px 24px 18px; border: 1px solid #d8dde3; border-top: none; }
    </style>
    <div class="login-hero"></div>
    <div class="login-brand">
        <div class="login-eyebrow">Sonalika &middot; ITL Internal Systems</div>
        <div class="login-heading">Inventory<br>Control</div>
        <div class="login-desc">Real-time stock tracking across categories, suppliers, and warehouse locations.
             Built on PostgreSQL with full audit history and reorder alerting.</div>
        <div class="login-meta">SECURE ACCESS &middot; JWT AUTHENTICATED &middot; v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    col_spacer, col_card = st.columns([5, 3])
    with col_card:
        st.markdown('<div class="login-card-wrap"><div class="login-card-head">Sign In</div><div class="login-card-body">', unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In", use_container_width=True, key="login_btn"):
            token = login(username, password)
            if token:
                st.session_state.token = token
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-weight:700;font-size:0.95rem;'
                'letter-spacing:0.03em;text-transform:uppercase;padding:4px 0 14px 0;'
                'border-bottom:1px solid #3a4150;margin-bottom:14px;">Inventory Control</div>',
                unsafe_allow_html=True)
    page = st.radio("Navigate", ["Overview", "Products", "Transactions", "Audit Log"], label_visibility="collapsed")
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;color:#9aa1ab;">SIGNED IN AS</div>'
                f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.85rem;margin-bottom:14px;">{st.session_state.username}</div>',
                unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        del st.session_state.token
        st.rerun()


def topbar(title, sub):
    st.markdown(f'<div class="topbar"><div class="topbar-title">{title}</div>'
                f'<div class="topbar-sub">{sub}</div></div>', unsafe_allow_html=True)


# ── Overview ──────────────────────────────────────────────────

if page == "Overview":
    topbar("Overview", "STOCK STATUS / VALUATION SUMMARY")
    stats = api_get("/products/stats")
    total_products = stats.get("total_products", 0) or 0
    total_value    = float(stats.get("total_inventory_value") or 0)
    low_stock      = stats.get("low_stock", 0) or 0
    out_of_stock   = stats.get("out_of_stock", 0) or 0
    healthy        = stats.get("healthy", 0) or 0

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-cell"><div class="metric-label">Total SKUs</div><div class="metric-value">{total_products}</div></div>
        <div class="metric-cell"><div class="metric-label">Inventory Value</div><div class="metric-value">&#8377;{total_value:,.0f}</div></div>
        <div class="metric-cell"><div class="metric-label">Healthy Stock</div><div class="metric-value ok">{healthy}</div></div>
        <div class="metric-cell"><div class="metric-label">Low Stock</div><div class="metric-value warn">{low_stock}</div></div>
        <div class="metric-cell"><div class="metric-label">Out of Stock</div><div class="metric-value crit">{out_of_stock}</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="medium")
    with col1:
        st.markdown('<div class="sec-label">Reorder Required</div>', unsafe_allow_html=True)
        alerts = api_get("/reports/low-stock")
        if alerts:
            adf = df(alerts)[["sku", "name", "category", "stock_qty", "reorder_level", "units_needed"]]
            adf.columns = ["SKU", "PRODUCT", "CATEGORY", "QTY ON HAND", "REORDER AT", "UNITS NEEDED"]
            st.dataframe(adf, use_container_width=True, hide_index=True, height=300)
        else:
            st.markdown('<div class="empty-state">No products below reorder threshold</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sec-label">Value by Category</div>', unsafe_allow_html=True)
        summary = api_get("/reports/inventory-summary")
        if summary:
            sdf = df(summary)
            sdf.columns = ["CATEGORY", "SKUS", "UNITS", "VALUE (INR)"]
            sdf["VALUE (INR)"] = sdf["VALUE (INR)"].apply(lambda v: f"{float(v):,.0f}")
            st.dataframe(sdf, use_container_width=True, hide_index=True, height=300)
        else:
            st.markdown('<div class="empty-state">No category data</div>', unsafe_allow_html=True)


# ── Products ──────────────────────────────────────────────────

elif page == "Products":
    topbar("Products", "CATALOG / STOCK LEVELS")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1: search = st.text_input("Search", placeholder="Name or SKU")
    with col2:
        cats = api_get("/categories/")
        cat_map = {c["name"]: c["id"] for c in cats}
        cat_filter = st.selectbox("Category", ["All"] + list(cat_map.keys()))
    with col3: low_only = st.checkbox("Low stock only", value=False)

    params = {}
    if search: params["search"] = search
    if cat_filter != "All": params["category_id"] = cat_map[cat_filter]
    if low_only: params["low_stock"] = True
    params["page_size"] = 100

    products = api_get("/products/", params=params)
    st.markdown('<div class="sec-label">Catalog</div>', unsafe_allow_html=True)
    if products:
        pdf = df(products)
        cat_lookup = {c["id"]: c["name"] for c in cats}
        pdf["category"] = pdf["category_id"].map(cat_lookup).fillna("—")
        def status(row):
            if row["stock_qty"] == 0: return "OUT OF STOCK"
            elif row["stock_qty"] <= row["reorder_level"]: return "LOW"
            return "HEALTHY"
        pdf["status"] = pdf.apply(status, axis=1)
        pdf = pdf[["sku", "name", "category", "unit_price", "stock_qty", "reorder_level", "status"]]
        pdf.columns = ["SKU", "PRODUCT", "CATEGORY", "UNIT PRICE", "QTY", "REORDER AT", "STATUS"]
        st.dataframe(pdf, use_container_width=True, hide_index=True, height=380)
    else:
        st.markdown('<div class="empty-state">No products match the current filters</div>', unsafe_allow_html=True)

    with st.expander("Register New Product"):
        c1, c2, c3 = st.columns(3)
        with c1:
            sku = st.text_input("SKU", key="new_sku")
            name = st.text_input("Product Name", key="new_name")
        with c2:
            cat_name = st.selectbox("Category", list(cat_map.keys()), key="new_cat") if cat_map else None
            unit_price = st.number_input("Unit Price", min_value=0.0, step=0.5, key="new_price")
        with c3:
            reorder_lvl = st.number_input("Reorder Level", min_value=0, value=10, key="new_reorder")
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            submit = st.button("Create Product", use_container_width=True)
        if submit:
            if not sku or not name:
                st.error("SKU and product name are required.")
            else:
                res = api_post("/products/", {"sku": sku, "name": name, "category_id": cat_map.get(cat_name), "unit_price": unit_price, "reorder_level": reorder_lvl})
                if res.status_code == 201:
                    st.success(f"Product {sku} created.")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Could not create product."))


# ── Transactions ──────────────────────────────────────────────

elif page == "Transactions":
    topbar("Transactions", "STOCK MOVEMENT LOG")
    products = api_get("/products/", params={"page_size": 200})
    prod_map = {f'{p["sku"]} — {p["name"]}': p["id"] for p in products}
    col1, col2 = st.columns([1, 2], gap="medium")
    with col1:
        st.markdown('<div class="sec-label">Record Movement</div>', unsafe_allow_html=True)
        prod_label = st.selectbox("Product", list(prod_map.keys())) if prod_map else None
        txn_type = st.selectbox("Movement Type", ["IN", "OUT", "ADJUST"])
        quantity = st.number_input("Quantity", min_value=1, value=1)
        note = st.text_input("Reference", value="Manual entry")
        if st.button("Submit", use_container_width=True):
            res = api_post("/transactions/", {"product_id": prod_map[prod_label], "txn_type": txn_type, "quantity": quantity, "reference_note": note})
            if res.status_code == 201:
                st.success(f"{txn_type} of {quantity} units recorded.")
                st.rerun()
            else:
                st.error(res.json().get("detail", "Transaction failed."))
    with col2:
        st.markdown('<div class="sec-label">Recent Movement</div>', unsafe_allow_html=True)
        txns = api_get("/transactions/", params={"limit": 50})
        if txns:
            tdf = df(txns)[["created_at", "product_id", "txn_type", "quantity", "reference_note"]]
            tdf.columns = ["TIMESTAMP", "PRODUCT ID", "TYPE", "QTY", "REFERENCE"]
            st.dataframe(tdf, use_container_width=True, hide_index=True, height=440)
        else:
            st.markdown('<div class="empty-state">No transactions recorded yet</div>', unsafe_allow_html=True)


# ── Audit Log ─────────────────────────────────────────────────

elif page == "Audit Log":
    topbar("Audit Log", "FULL CHANGE HISTORY — PRODUCTS TABLE")
    limit = st.slider("Entries to display", 10, 300, 100)
    logs = api_get("/reports/audit-log", params={"limit": limit})
    st.markdown('<div class="sec-label">Change Records</div>', unsafe_allow_html=True)
    if logs:
        ldf = df(logs)[["changed_at", "table_name", "record_id", "action"]]
        ldf.columns = ["TIMESTAMP", "TABLE", "RECORD ID", "ACTION"]
        st.dataframe(ldf, use_container_width=True, hide_index=True, height=480)
    else:
        st.markdown('<div class="empty-state">No audit entries found</div>', unsafe_allow_html=True)
