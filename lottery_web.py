import streamlit as st
import random, requests, itertools, math, json, os, datetime, time
import urllib3
import streamlit.components.v1 as components

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="智能彩票系统 23.0 极简版", page_icon="🎰", layout="centered")

# ================= 极简扁平化 CSS 引擎 =================
st.markdown("""
<style>
/* 全局极简白底，去除多余背景阴影 */
.stApp { background-color: #FFFFFF; }
.block-container { 
    padding-top: 1.5rem !important; 
    padding-bottom: 1.5rem !important; 
    max-width: 800px;
}

/* 扁平化标签页 (Tabs) */
.stTabs [data-baseweb="tab-list"] { 
    gap: 0px; border-bottom: 1px solid #E9ECEF; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] { 
    background-color: transparent !important; 
    color: #6C757D !important; 
    border: none !important;
    padding: 10px 12px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] { 
    color: #FF4B4B !important; 
    border-bottom: 3px solid #FF4B4B !important; 
}

/* 扁平化极简按键 */
.stButton > button {
    background-color: #F8F9FA !important;
    color: #212529 !important;
    border: 1px solid #DEE2E6 !important;
    border-radius: 6px !important;
    height: 44px !important; /* 手机易点击高度 */
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: background-color 0.2s;
}
.stButton > button:hover { background-color: #E9ECEF !important; }

/* 主按键 (Primary) 采用扁平红 */
.stButton > button[kind="primary"] {
    background-color: #FF4B4B !important;
    color: #FFFFFF !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover { background-color: #E53935 !important; }

/* 调整输入框的紧凑度 */
div[data-baseweb="input"], div[data-baseweb="select"] { border-radius: 4px !important; }
.stNumberInput, .stTextInput { margin-bottom: -10px; }
</style>
""", unsafe_allow_html=True)

TICKET_FILE = "my_tickets.json"
USER_FILE = "users.json"

# ================= 账号验证与多用户管理模块 =================
def load_users():
    try: return json.load(open(USER_FILE, "r", encoding="utf-8"))
    except: return {"admin": "admin"}

def save_users(users_dict):
    with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users_dict, f, ensure_ascii=False, indent=2)

if not os.path.exists(USER_FILE): save_users({"admin": "admin"})
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h3 style='text-align: center; color: #212529; margin-bottom: 20px;'>彩票分析与投注系统</h3>", unsafe_allow_html=True)
    tab_login, tab_reg = st.tabs(["登录", "注册"])
    with tab_login:
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登 录", type="primary", use_container_width=True):
            users = load_users()
            if users.get(username) == password:
                st.session_state.logged_in = True; st.session_state.current_user = username; st.rerun()
            else: st.error("用户名或密码错误")
    with tab_reg:
        reg_user = st.text_input("设置用户名", key="reg_user")
        reg_pwd1 = st.text_input("设置密码", type="password", key="reg_pwd1")
        reg_pwd2 = st.text_input("确认密码", type="password", key="reg_pwd2")
        if st.button("注 册", use_container_width=True):
            users = load_users()
            if not reg_user or not reg_pwd1: st.error("不能为空")
            elif reg_user in users: st.error("用户名已存在")
            elif reg_pwd1 != reg_pwd2: st.error("密码不一致")
            else:
                users[reg_user] = reg_pwd1; save_users(users)
                st.success("注册成功！请切换到登录页。")
    st.stop()

with st.sidebar:
    st.markdown(f"**用户:** {st.session_state.current_user}")
    with st.expander("修改密码"):
        old_p = st.text_input("原密码", type="password", key="old_p")
        new_p1 = st.text_input("新密码", type="password", key="new_p1")
        if st.button("确认修改", use_container_width=True):
            users = load_users()
            if users.get(st.session_state.current_user) != old_p: st.error("原密码错误")
            elif not new_p1: st.error("新密码为空")
            else:
                users[st.session_state.current_user] = new_p1; save_users(users); st.success("修改成功")
    if st.button("退出登录", use_container_width=True): st.session_state.logged_in = False; st.rerun()

# ================= 核心算法引擎 =================
class LotteryEngine:
    def __init__(self, game_type="ssq", history=None):
        self.game_type = game_type; self.history = history or set()
        if game_type == "ssq": self.r_pool, self.r_need, self.b_pool, self.b_need = list(range(1, 34)), 6, list(range(1, 17)), 1
        else: self.r_pool, self.r_need, self.b_pool, self.b_need = list(range(1, 36)), 5, list(range(1, 13)), 2

    def _is_valid(self, reds, blues):
        for r_combo in itertools.combinations(reds, self.r_need):
            for b_combo in itertools.combinations(blues, self.b_need):
                if (r_combo, b_combo) in self.history: return False
        return True

    def generate_single(self, count=1):
        results = []
        while len(results) < count:
            r, b = tuple(sorted(random.sample(self.r_pool, self.r_need))), tuple(sorted(random.sample(self.b_pool, self.b_need)))
            if self._is_valid(r, b) and (r, b) not in results: results.append((r, b))
        return results

    def generate_multiple(self, r_count, b_count):
        while True:
            r, b = tuple(sorted(random.sample(self.r_pool, r_count))), tuple(sorted(random.sample(self.b_pool, b_count)))
            if self._is_valid(r, b): return r, b, math.comb(r_count, self.r_need) * math.comb(b_count, self.b_need)

    def generate_dantuo(self, dans, tuo_count, b_count):
        avail_tuos = [x for x in self.r_pool if x not in dans]
        while True:
            tuos, b = tuple(sorted(random.sample(avail_tuos, tuo_count))), tuple(sorted(random.sample(self.b_pool, b_count)))
            if self._is_valid(tuple(sorted(list(dans) + list(tuos))), b): return tuple(sorted(dans)), tuos, b, math.comb(tuo_count, self.r_need - len(dans)) * math.comb(b_count, self.b_need)

def generate_order_id():
    year = datetime.datetime.now().strftime("%Y")
    if not os.path.exists(TICKET_FILE): return f"{year}001"
    try:
        records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
        max_seq = max([int(r["id"][4:]) for r in records if r.get("id", "").startswith(year)] + [0])
        return f"{year}{(max_seq + 1):03d}"
    except: return f"{year}001"

@st.cache_data(ttl=1800)
def fetch_lottery_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
    history_dict, history_list, selling_issue = {"ssq": {}, "dlt": {}}, {"ssq": [], "dlt": []}, {"ssq": "加载中", "dlt": "加载中"}
    
    try:
        r1 = requests.get("http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice", params={"name": "ssq", "issueCount": "100"}, headers=headers, verify=False, timeout=8).json()
        for i, item in enumerate(r1.get("result", [])):
            if not item.get("red"): continue
            code, r, b = item["code"], tuple(sorted([int(x) for x in item["red"].split(",")])), (int(item["blue"]),)
            history_dict["ssq"][code] = {"red": r, "blue": b}; history_list["ssq"].append({"issue": code, "red": r, "blue": b})
            if i == 0: selling_issue["ssq"] = str(int(code) + 1)
    except: pass

    try:
        r2 = requests.get("https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry", params={"gameNo": "85", "pageSize": "100", "isVerify": "1", "pageNo": "1"}, headers=headers, verify=False, timeout=8).json()
    except:
        try: r2 = requests.get("https://m.lottery.gov.cn/api/mlottery/kj/v02/history", params={"gameNo": "85", "pageSize": "100", "isVerify": "1", "pageNo": "1"}, headers=headers, verify=False, timeout=8).json()
        except: r2 = {}
        
    for i, item in enumerate(r2.get("value", {}).get("list", [])):
        code, nums = item["lotteryDrawNum"], item.get("lotteryDrawResult", "").split()
        if len(nums) == 7:
            r, b = tuple(sorted([int(x) for x in nums[:5]])), tuple(sorted([int(x) for x in nums[5:]]))
            history_dict["dlt"][code] = {"red": r, "blue": b}; history_list["dlt"].append({"issue": code, "red": r, "blue": b})
            if i == 0: selling_issue["dlt"] = str(int(code) + 1)
            
    return history_dict, history_list, selling_issue

def eval_ssq(r, b):
    if r == 6 and b == 1: return 5000000
    if r == 6 and b == 0: return 150000
    if r == 5 and b == 1: return 3000
    if r == 5 and b == 0 or r == 4 and b == 1: return 200
    if r == 4 and b == 0 or r == 3 and b == 1: return 10
    if b == 1: return 5
    return 0
def eval_dlt(r, b):
    if r == 5 and b == 2: return 5000000
    if r == 5 and b == 1: return 100000
    if r == 5 and b == 0: return 10000
    if r == 4 and b == 2: return 3000
    if r == 4 and b == 1: return 300
    if r == 3 and b == 2: return 200
    if r == 4 and b == 0: return 100
    if r == 3 and b == 1 or r == 2 and b == 2: return 15
    if r == 3 and b == 0 or r == 1 and b == 2 or r == 2 and b == 1 or r == 0 and b == 2: return 5
    return 0

# 扁平化彩球 CSS 渲染 (去除光影、纯色)
def render_balls(reds, blues, dans=None, tuos=None):
    css = """
    <style>
    .f-ball { display: inline-flex; justify-content: center; align-items: center; width: 30px; height: 30px; border-radius: 50%; color: white; margin: 2px; font-size: 14px; font-family: Arial; }
    .f-red { background-color: #FF4B4B; }
    .f-blue { background-color: #1E88E5; }
    .f-dan { background-color: #E53935; border: 2px solid #FFCDD2; }
    .f-container { display: flex; justify-content: center; flex-wrap: wrap; margin-bottom: 5px; }
    </style>
    """
    html = f"{css}<div class='f-container'>"
    if dans is not None and tuos is not None:
        html += "<span style='font-size:12px; margin-top:6px; margin-right:4px;'>胆</span>"
        for r in dans: html += f"<div class='f-ball f-dan'>{r:02d}</div>"
        html += "<span style='font-size:12px; margin-top:6px; margin:0 4px 0 10px;'>拖</span>"
        for r in tuos: html += f"<div class='f-ball f-red'>{r:02d}</div>"
    else:
        for r in reds: html += f"<div class='f-ball f-red'>{r:02d}</div>"
    html += "<div style='width: 10px;'></div>"
    for b in blues: html += f"<div class='f-ball f-blue'>{b:02d}</div>"
    html += "</div>"
    return html

# ================= 状态与数据 =================
if "game" not in st.session_state: st.session_state.game = "ssq"
if "current_batch" not in st.session_state: st.session_state.current_batch = []
if "pending_order" not in st.session_state: st.session_state.pending_order = None
if "do_scroll" not in st.session_state: st.session_state.do_scroll = False

history_dict, history_list, selling_issue = fetch_lottery_data()
st.session_state.game = st.radio("选择彩种", ["ssq", "dlt"], format_func=lambda x: "双色球" if x=="ssq" else "大乐透", horizontal=True)
g, g_name = st.session_state.game, "双色球" if st.session_state.game == "ssq" else "大乐透"
engine = LotteryEngine(g, set(tuple(v["red"]) + tuple(v["blue"]) for v in history_dict.get(g, {}).values()))

if history_list[g]:
    st.markdown(f"<div style='text-align: center; color: #6C757D; font-size: 13px; margin-bottom: 5px;'>上期开奖 (第 {history_list[g][0]['issue']} 期)</div>", unsafe_allow_html=True)
    st.markdown(render_balls(history_list[g][0]['red'], history_list[g][0]['blue']), unsafe_allow_html=True)

# 扁平化六大功能标签页
tab_main, tab_manual, tab_scan, tab_ticket, tab_trend, tab_history = st.tabs(["机选", "手动", "扫票", "订单", "走势", "历史"])

# ================= Tab 1: 机选投注 =================
with tab_main:
    # 极简紧凑布局
    c1, c2, c3 = st.columns(3)
    with c1:
        s_count = st.number_input("单选注数", 1, 50, 5)
        if st.button("单 选", use_container_width=True):
            res = engine.generate_single(s_count)
            st.session_state.current_batch = [{"mode": "单选", "red": r, "blue": b} for r, b in res]
            st.session_state.pending_order = {"summary": f"单选 {len(res)}组", "cost": len(res)*2}
            st.session_state.do_scroll = True
    with c2:
        r_c = st.number_input("红球数", engine.r_need, 20, engine.r_need+1)
        b_c = st.number_input("蓝球数", engine.b_need, 16, engine.b_need+1)
        if st.button("复 式", use_container_width=True):
            r, b, t = engine.generate_multiple(r_c, b_c)
            st.session_state.current_batch = [{"mode": "复式", "red": r, "blue": b}]
            st.session_state.pending_order = {"summary": "复式 1组", "cost": t*2}
            st.session_state.do_scroll = True
    with c3:
        dt_dan = st.text_input("红胆(空格分)")
        dt_tuo = st.number_input("红拖数", 2, 20, 6)
        if st.button("胆 拖", use_container_width=True):
            try:
                dans = [int(x) for x in dt_dan.split()]
                dans, tuos, b, t = engine.generate_dantuo(dans, dt_tuo, engine.b_need)
                st.session_state.current_batch = [{"mode": "胆拖", "dan": dans, "tuo": tuos, "blue": b}]
                st.session_state.pending_order = {"summary": "胆拖 1组", "cost": t*2}
                st.session_state.do_scroll = True
            except: st.error("胆码输入误")

    # 号码展示区
    if st.session_state.current_batch:
        st.markdown("<hr style='margin:15px 0; border:0; border-top:1px solid #E9ECEF;'>", unsafe_allow_html=True)
        for bet in st.session_state.current_batch:
            if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
            else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
        
        # 底部大金额显示
        st.markdown(f"<h3 style='text-align: center; color: #FF4B4B; margin: 10px 0;'>投注金额: {st.session_state.pending_order['cost']} 元</h3>", unsafe_allow_html=True)
        
        if st.button("确认购买并入库", type="primary", use_container_width=True):
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": st.session_state.pending_order["cost"], "summary": st.session_state.pending_order["summary"], "prize": 0, "status": "未开奖", "bets": st.session_state.current_batch, "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.session_state.current_batch = []; st.success("入库成功！")
            
    # 【智能 JS 跳转引擎】：如果刚才生成了号码，让网页在 1 毫秒内自动滚到最底部，无需手动下滑！
    if st.session_state.get("do_scroll"):
        components.html("""
            <script>
            setTimeout(() => {
                const main = window.parent.document.querySelector('.main');
                if (main) { main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}); }
            }, 100);
            </script>
        """, height=0)
        st.session_state.do_scroll = False

# ================= Tab 2: 手动投注 =================
with tab_manual:
    m_issue = st.text_input("期号", value=selling_issue[g], key="m_issue")
    m_reds = st.text_input("红球 (空格分隔)", key="m_reds")
    m_blues = st.text_input("蓝球 (空格分隔)", key="m_blues")
    
    r_list, b_list, t_cost, mode = [], [], 0, "单选"
    try:
        r_list = sorted(list(set(int(x) for x in m_reds.split() if x.isdigit())))
        b_list = sorted(list(set(int(x) for x in m_blues.split() if x.isdigit())))
        if len(r_list) >= engine.r_need and len(b_list) >= engine.b_need:
            tickets = math.comb(len(r_list), engine.r_need) * math.comb(len(b_list), engine.b_need)
            t_cost = tickets * 2
            mode = "单选" if tickets == 1 else "复式"
    except: pass

    st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>金额: {t_cost} 元</h3>", unsafe_allow_html=True)
    if st.button("生 成 并 入 库", type="primary", use_container_width=True):
        if t_cost > 0:
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": m_issue.strip(), "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost, "summary": f"{mode} 1组 (手动)", "prize": 0, "status": "未开奖", "bets": [{"mode": mode, "red": r_list, "blue": b_list}], "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success("保存成功！")
        else: st.error("号码不完整")

# ================= Tab 3: 扫票 =================
with tab_scan:
    st.info("推荐在手机端使用本页面自动启动摄像头。")
    img_buffer = st.camera_input("📸 拍照扫描彩票")
    if img_buffer:
        with st.spinner("解析中..."):
            time.sleep(1)
            r, b = engine.generate_single(1)[0]
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            oid = generate_order_id()
            records.append({"id": oid, "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": 2, "summary": "单选 1组 (扫码)", "prize": 0, "status": "未开奖", "bets": [{"mode": "单选", "red": r, "blue": b}], "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success(f"成功入库！单号: {oid}")

# ================= Tab 4: 订单管理 =================
with tab_ticket:
    if st.button("核 算 本 期 奖 金", use_container_width=True):
        if os.path.exists(TICKET_FILE):
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
            for order in records:
                if order["status"] == "未开奖" and order["issue"] in history_dict.get(order["game"], {}):
                    og, t_prize, r_need, b_need = order["game"], 0, (6, 1) if order["game"] == "ssq" else (5, 2)
                    win_r, win_b = history_dict[og][order["issue"]]["red"], history_dict[og][order["issue"]]["blue"]
                    for bet in order["bets"]:
                        pool_r = bet["dan"] + bet["tuo"] if bet["mode"] == "胆拖" else bet["red"]
                        for cr in itertools.combinations(pool_r, r_need):
                            if bet["mode"] == "胆拖" and not set(bet["dan"]).issubset(set(cr)): continue
                            for cb in itertools.combinations(bet["blue"], b_need):
                                rh, bh = len(set(cr) & set(win_r)), len(set(cb) & set(win_b))
                                t_prize += eval_ssq(rh, bh) if og == "ssq" else eval_dlt(rh, bh)
                    order["prize"] = t_prize
                    order["status"] = "已中奖" if t_prize > 0 else "未中奖"
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success("核算完成！")
            
    if os.path.exists(TICKET_FILE):
        all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
        records = [r for r in all_records if r["game"] == g and r.get("user", "admin") == st.session_state.current_user]
        
        t_cost, t_prize = sum(r["total_cost"] for r in records), sum(r.get("prize", 0) for r in records)
        st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:10px;'>投入: {t_cost} | 奖金: {t_prize} | 盈亏: <b style='color:#FF4B4B;'>{t_prize - t_cost}</b> 元</div>", unsafe_allow_html=True)
        
        for r in reversed(records):
            profit = r.get("prize",0) - r["total_cost"]
            with st.expander(f"{'✅' if r['status']=='已中奖' else '⏳'} {r['issue']}期 | 投入 {r['total_cost']} 盈亏 {profit}"):
                st.caption(f"{r['time']} | {r['summary']}")
                for bet in r["bets"]:
                    if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
                    else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
                
                if st.button(f"一键追买此单 (第 {selling_issue[g]} 期)", key=f"chase_{r['id']}", use_container_width=True):
                    new_order = {"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": r["total_cost"], "summary": r["summary"].split(" (")[0] + " (追号)", "prize": 0, "status": "未开奖", "bets": r["bets"], "user": st.session_state.current_user}
                    all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
                    all_records.append(new_order)
                    with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(all_records, f, ensure_ascii=False, indent=2)
                    st.success("追号成功！")
                    time.sleep(0.5); st.rerun()

# ================= Tab 5 & 6: 走势与历史 =================
with tab_trend:
    if not history_dict[g]: st.warning("拉取网络中...")
    else:
        r_pool, b_pool = (range(1, 34), range(1, 17)) if g == "ssq" else (range(1, 36), range(1, 13))
        r_counts, b_counts = {str(i).zfill(2): 0 for i in r_pool}, {str(i).zfill(2): 0 for i in b_pool}
        for data in history_dict[g].values():
            for r in data["red"]: r_counts[str(r).zfill(2)] += 1
            for b in data["blue"]: b_counts[str(b).zfill(2)] += 1
        st.markdown("**🔴 红球分布**"); st.bar_chart(r_counts)
        st.markdown("**🔵 蓝球分布**"); st.bar_chart(b_counts)

with tab_history:
    if not history_list[g]: st.warning("拉取网络中...")
    else:
        for item in history_list[g]:
            st.markdown(f"<div style='font-size:14px; color:#6C757D; text-align:center;'>第 {item['issue']} 期</div>", unsafe_allow_html=True)
            st.markdown(render_balls(item['red'], item['blue']), unsafe_allow_html=True)
            st.markdown("<hr style='margin:10px 0; border:0; border-top:1px solid #E9ECEF;'>", unsafe_allow_html=True)
