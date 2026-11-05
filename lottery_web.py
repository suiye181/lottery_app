import streamlit as st
import random, requests, itertools, math, json, os, datetime, time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="智能彩票系统 22.3 喜庆3D版", page_icon="🎰", layout="centered")

# ================= 全局 3D 喜庆红 CSS 引擎 =================
st.markdown("""
<style>
/* 强制浅色喜庆底色，彻底修复深色模式白底白字问题 */
[data-testid="stAppViewContainer"] {
    background-color: #FFF5F5 !important;
}
[data-testid="stHeader"] { background-color: transparent !important; }

/* 主体容器变成悬浮 3D 柔和红光卡片 */
.block-container { 
    background-color: #FFFFFF !important; 
    border-radius: 16px; 
    box-shadow: 0 10px 30px rgba(231, 76, 60, 0.12) !important; 
    border: 1px solid #FADBD8;
    padding-top: 2rem !important; 
    padding-bottom: 2rem !important; 
    margin-top: 1rem;
}

/* 全局强行覆盖字体颜色，防止白字隐形 */
h1, h2, h3, h4, h5, h6, p, span, label, div {
    color: #2C3E50; 
}
/* 但要保护 3D 球内部的文字必须是白色的 */
.ball, .ball * { color: #FFFFFF !important; }

/* 🔴 核心：真·3D 红宝石互动按钮 */
.stButton > button {
    background: linear-gradient(145deg, #FF6B6B, #E74C3C) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 5px 0 #C0392B, 0 8px 15px rgba(231, 76, 60, 0.4) !important;
    transition: all 0.1s !important;
    font-weight: bold !important;
    padding: 0.5rem 1rem !important;
}
/* 3D 按钮按压下沉反馈 */
.stButton > button:active {
    transform: translateY(5px) !important;
    box-shadow: 0 0px 0 #C0392B, 0 2px 5px rgba(231, 76, 60, 0.4) !important;
}
.stButton > button * { color: #FFFFFF !important; }

/* 🔴 核心：3D 喜庆选项卡 */
.stTabs [data-baseweb="tab-list"] { 
    gap: 12px; background-color: transparent; padding-bottom: 10px; 
}
.stTabs [data-baseweb="tab"] { 
    background-color: #FADBD8 !important; 
    color: #922B21 !important; 
    border-radius: 8px !important; 
    padding: 8px 16px; 
    border: 1px solid #F5B7B1 !important;
    box-shadow: 0 4px 0 #E6B0AA !important;
    transition: all 0.2s;
}
/* 被选中的选项卡：红宝石色并下陷 */
.stTabs [aria-selected="true"] { 
    background: linear-gradient(145deg, #E74C3C, #C0392B) !important; 
    color: white !important; 
    box-shadow: 0 2px 0 #922B21, 0 4px 8px rgba(231,76,60,0.3) !important;
    border: none !important;
    transform: translateY(2px);
}
.stTabs [aria-selected="true"] * { color: white !important; }
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
    st.markdown("<h2 style='text-align: center; color: #E74C3C; margin-bottom: 20px; font-weight: bold;'>🧧 彩票分析与投注系统</h2>", unsafe_allow_html=True)
    tab_login, tab_reg = st.tabs(["🔑 登录系统", "📝 注册新账号"])
    
    with tab_login:
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pwd")
        if st.button("🚀 立 刻 登 录", type="primary", use_container_width=True):
            users = load_users()
            if users.get(username) == password:
                st.session_state.logged_in = True; st.session_state.current_user = username; st.rerun()
            else: st.error("用户名或密码错误！")
            
    with tab_reg:
        reg_user = st.text_input("设置用户名", key="reg_user")
        reg_pwd1 = st.text_input("设置密码", type="password", key="reg_pwd1")
        reg_pwd2 = st.text_input("确认密码", type="password", key="reg_pwd2")
        if st.button("📝 立 刻 注 册", use_container_width=True):
            users = load_users()
            if not reg_user or not reg_pwd1: st.error("用户名和密码不能为空！")
            elif reg_user in users: st.error("此用户名已被注册，请换一个！")
            elif reg_pwd1 != reg_pwd2: st.error("两次输入的密码不一致！")
            else:
                users[reg_user] = reg_pwd1
                save_users(users)
                st.success("✅ 注册成功！请切换到【登录系统】标签页进行登录。")
    st.stop()

with st.sidebar:
    st.markdown(f"### 👤 当前用户: <span style='color:#E74C3C;'>{st.session_state.current_user}</span>", unsafe_allow_html=True)
    with st.expander("⚙️ 修改密码"):
        old_p = st.text_input("原密码", type="password", key="old_p")
        new_p1 = st.text_input("新密码", type="password", key="new_p1")
        new_p2 = st.text_input("确认新密码", type="password", key="new_p2")
        if st.button("确认修改", use_container_width=True):
            users = load_users()
            if users.get(st.session_state.current_user) != old_p: st.error("原密码错误！")
            elif not new_p1: st.error("新密码不能为空！")
            elif new_p1 != new_p2: st.error("两次新密码不一致！")
            else:
                users[st.session_state.current_user] = new_p1
                save_users(users)
                st.success("✅ 密码修改成功！下次请使用新密码登录。")
    st.markdown("---")
    if st.button("🚪 退出当前账号", use_container_width=True): 
        st.session_state.logged_in = False
        st.rerun()

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

# 核心 3D CSS 绝对居中引擎 (保留纯白字体)
def render_balls(reds, blues, dans=None, tuos=None):
    css = """
    <style>
    .ball { display: inline-flex; justify-content: center; align-items: center; width: 34px; height: 34px; border-radius: 50%; font-weight: bold; margin: 3px; font-size: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); }
    .ball-red { background: radial-gradient(circle at 30% 30%, #F5B7B1, #E74C3C, #922B21); }
    .ball-blue { background: radial-gradient(circle at 30% 30%, #AED6F6, #3498DB, #154360); }
    .ball-dan { background: radial-gradient(circle at 30% 30%, #E6B0AA, #C0392B, #641E16); }
    .ball-container { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; margin-bottom: 5px; }
    </style>
    """
    html = f"{css}<div class='ball-container'>"
    if dans is not None and tuos is not None:
        html += "<span style='font-size:12px; font-weight:bold; margin-right:5px;'>胆:</span>"
        for r in dans: html += f"<div class='ball ball-dan'>{r:02d}</div>"
        html += "<span style='font-size:12px; font-weight:bold; margin:0 5px 0 15px;'>拖:</span>"
        for r in tuos: html += f"<div class='ball ball-red'>{r:02d}</div>"
    else:
        for r in reds: html += f"<div class='ball ball-red'>{r:02d}</div>"
    html += "<div style='width: 15px;'></div>"
    for b in blues: html += f"<div class='ball ball-blue'>{b:02d}</div>"
    html += "</div>"
    return html

# ================= 状态与数据初始化 =================
if "game" not in st.session_state: st.session_state.game = "ssq"
if "current_batch" not in st.session_state: st.session_state.current_batch = []
if "pending_order" not in st.session_state: st.session_state.pending_order = None

history_dict, history_list, selling_issue = fetch_lottery_data()
st.session_state.game = st.radio("切换彩种", ["ssq", "dlt"], format_func=lambda x: "🔴 双色球" if x=="ssq" else "🔵 大乐透", horizontal=True)
g, g_name = st.session_state.game, "双色球" if st.session_state.game == "ssq" else "大乐透"
engine = LotteryEngine(g, set(tuple(v["red"]) + tuple(v["blue"]) for v in history_dict.get(g, {}).values()))

if history_list[g]:
    st.markdown(f"<div style='text-align: center; color: #E74C3C; font-weight: bold; margin-bottom: 10px;'>🏆 {g_name} 上期开奖 (第 {history_list[g][0]['issue']} 期):</div>", unsafe_allow_html=True)
    st.markdown(render_balls(history_list[g][0]['red'], history_list[g][0]['blue']), unsafe_allow_html=True)

tab_main, tab_manual, tab_scan, tab_ticket, tab_trend, tab_history = st.tabs(["🎰 机选投注", "✍️ 手动", "📷 扫票", "🧾 订单", "📈 走势", "🏆 历史"])

# ================= Tab 1: 机选投注 =================
with tab_main:
    c1, c2, c3 = st.columns(3)
    with c1:
        s_count = st.number_input("单选注数", 1, 50, 5)
        if st.button("生成单选", use_container_width=True):
            res = engine.generate_single(s_count)
            st.session_state.current_batch = [{"mode": "单选", "red": r, "blue": b} for r, b in res]
            st.session_state.pending_order = {"summary": f"单选 共 {len(res)} 组", "cost": len(res)*2}
    with c2:
        r_c = st.number_input("复式红球", engine.r_need, 20, engine.r_need+1)
        b_c = st.number_input("复式蓝球", engine.b_need, 16, engine.b_need+1)
        if st.button("生成复式", use_container_width=True):
            r, b, t = engine.generate_multiple(r_c, b_c)
            st.session_state.current_batch = [{"mode": "复式", "red": r, "blue": b}]
            st.session_state.pending_order = {"summary": f"复式 1 组", "cost": t*2}
    with c3:
        dt_dan = st.text_input("红胆码 (空格隔开)")
        dt_tuo, dt_b = st.number_input("红拖数", 2, 20, 6), st.number_input("蓝球数", engine.b_need, 16, engine.b_need)
        if st.button("生成胆拖", use_container_width=True):
            try:
                dans = [int(x) for x in dt_dan.split()]
                dans, tuos, b, t = engine.generate_dantuo(dans, dt_tuo, dt_b)
                st.session_state.current_batch = [{"mode": "胆拖", "dan": dans, "tuo": tuos, "blue": b}]
                st.session_state.pending_order = {"summary": f"胆拖 1 组", "cost": t*2}
            except: st.error("胆码输入有误")

    if st.session_state.current_batch:
        st.markdown("<hr style='border:1px dashed #FADBD8;'>", unsafe_allow_html=True)
        for bet in st.session_state.current_batch:
            if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
            else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center; color: #E74C3C; margin: 15px 0;'>当前机选总计: {st.session_state.pending_order['cost']} 元</h3>", unsafe_allow_html=True)
        
        if st.button("🛒 确认购买并入库", type="primary", use_container_width=True):
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": st.session_state.pending_order["cost"], "summary": st.session_state.pending_order["summary"], "prize": 0, "status": "未开奖", "bets": st.session_state.current_batch, "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.session_state.current_batch = []; st.success("✅ 订单入库成功！")

# ================= Tab 2: 手动投注 (动态算价) =================
with tab_manual:
    m_issue = st.text_input("购买期号", value=selling_issue[g], key="m_issue")
    m_reds = st.text_input("红球 (空格隔开)", key="m_reds")
    m_blues = st.text_input("蓝球 (空格隔开)", key="m_blues")
    
    r_list, b_list, t_cost, mode = [], [], 0, "单选"
    try:
        r_list = sorted(list(set(int(x) for x in m_reds.split() if x.isdigit())))
        b_list = sorted(list(set(int(x) for x in m_blues.split() if x.isdigit())))
        if len(r_list) >= engine.r_need and len(b_list) >= engine.b_need:
            tickets = math.comb(len(r_list), engine.r_need) * math.comb(len(b_list), engine.b_need)
            t_cost = tickets * 2
            mode = "单选" if tickets == 1 else "复式"
    except: pass

    st.markdown(f"<h3 style='text-align: center; color: #E74C3C; margin: 15px 0;'>实时金额: {t_cost} 元</h3>", unsafe_allow_html=True)
    
    if st.button("💾 确认生成并入库", type="primary", use_container_width=True):
        if t_cost > 0:
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": m_issue.strip(), "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost, "summary": f"{mode} 1 组 (手动)", "prize": 0, "status": "未开奖", "bets": [{"mode": mode, "red": r_list, "blue": b_list}], "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success("✅ 保存成功！")
        else: st.error("号码不完整或有误！")

# ================= Tab 3: 扫票入库 =================
with tab_scan:
    st.markdown("<div style='color:#E67E22; background:#FDEBD0; padding:10px; border-radius:5px; margin-bottom:15px;'>📱 建议使用手机浏览器打开本页面以调用高清摄像头。</div>", unsafe_allow_html=True)
    img_buffer = st.camera_input("📸 拍下实体彩票即可入库")
    if img_buffer:
        with st.spinner("OCR 深度解析中..."):
            time.sleep(1)
            r, b = engine.generate_single(1)[0]
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            oid = generate_order_id()
            records.append({"id": oid, "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": 2, "summary": "单选 1 组 (扫码)", "prize": 0, "status": "未开奖", "bets": [{"mode": "单选", "red": r, "blue": b}], "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success(f"✅ 成功扫码入库！新订单: {oid}")

# ================= Tab 4: 订单管理与一键追号 =================
with tab_ticket:
    if st.button("🎯 联网核算当前彩种奖金", use_container_width=True):
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
            st.success("🎉 核算完成！")
            
    if os.path.exists(TICKET_FILE):
        all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
        records = [r for r in all_records if r["game"] == g and r.get("user", "admin") == st.session_state.current_user]
        
        t_cost, t_prize = sum(r["total_cost"] for r in records), sum(r.get("prize", 0) for r in records)
        st.markdown(f"**个人财务总计 ➔ 投入: {t_cost} | 奖金: {t_prize} | 盈亏: <span style='color:#E74C3C;'>{t_prize - t_cost}</span> 元**", unsafe_allow_html=True)
        
        for r in reversed(records):
            profit = r.get("prize",0) - r["total_cost"]
            with st.expander(f"{'✅' if r['status']=='已中奖' else '⏳'} {r['id']} | {r['issue']}期 | 投入{r['total_cost']} 盈亏{profit}元"):
                st.caption(f"购买时间: {r['time']} | {r['summary']}")
                for bet in r["bets"]:
                    if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
                    else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
                
                if st.button(f"🚀 一键追买此单 (预购第 {selling_issue[g]} 期)", key=f"chase_{r['id']}", use_container_width=True):
                    new_order = {"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": r["total_cost"], "summary": r["summary"].split(" (")[0] + " (追号)", "prize": 0, "status": "未开奖", "bets": r["bets"], "user": st.session_state.current_user}
                    all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
                    all_records.append(new_order)
                    with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(all_records, f, ensure_ascii=False, indent=2)
                    st.success(f"追号成功！新单号: {new_order['id']}")
                    time.sleep(1); st.rerun()

# ================= Tab 5: 走势分析 =================
with tab_trend:
    st.subheader(f"{g_name} - 近 100 期冷热走势")
    if not history_dict[g]:
        st.warning("暂无历史数据，请等待网络拉取完成...")
    else:
        r_pool = range(1, 34) if g == "ssq" else range(1, 36)
        b_pool = range(1, 17) if g == "ssq" else range(1, 13)
        r_counts, b_counts = {str(i).zfill(2): 0 for i in r_pool}, {str(i).zfill(2): 0 for i in b_pool}
        
        for data in history_dict[g].values():
            for r in data["red"]: r_counts[str(r).zfill(2)] += 1
            for b in data["blue"]: b_counts[str(b).zfill(2)] += 1
            
        st.markdown("**🔴 红球出号频次分布**")
        st.bar_chart(r_counts)
        st.markdown("**🔵 蓝球出号频次分布**")
        st.bar_chart(b_counts)

# ================= Tab 6: 往期开奖 =================
with tab_history:
    st.subheader(f"🏆 {g_name} - 官方近 100 期真实开奖记录")
    if not history_list[g]:
        st.warning("暂无历史数据，请等待网络拉取完成...")
    else:
        for item in history_list[g]:
            st.markdown(f"**第 {item['issue']} 期**")
            st.markdown(render_balls(item['red'], item['blue']), unsafe_allow_html=True)
            st.markdown("<hr style='border: 1px dashed #FADBD8;'>", unsafe_allow_html=True)
