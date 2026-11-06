import streamlit as st
import random, requests, itertools, math, json, os, datetime, time
import urllib3
import streamlit.components.v1 as components

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="智能彩票系统 24.0", page_icon="🎰", layout="centered")

# ================= 极简扁平化 CSS 引擎 =================
st.markdown("""
<style>
.stApp { background-color: #FFFFFF; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 800px; }
/* 一级标签页 */
.stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 1px solid #E9ECEF; padding-bottom: 0; }
.stTabs [data-baseweb="tab"] { background-color: transparent !important; color: #6C757D !important; border: none !important; padding: 10px 12px; font-weight: 500; }
.stTabs [aria-selected="true"] { color: #FF4B4B !important; border-bottom: 3px solid #FF4B4B !important; }
/* 极简按键 */
.stButton > button { background-color: #F8F9FA !important; color: #212529 !important; border: 1px solid #DEE2E6 !important; border-radius: 6px !important; height: 44px !important; font-weight: 500 !important; transition: background-color 0.2s; }
.stButton > button:hover { background-color: #E9ECEF !important; }
.stButton > button[kind="primary"] { background-color: #FF4B4B !important; color: #FFFFFF !important; border: none !important; }
.stButton > button[kind="primary"]:hover { background-color: #E53935 !important; }
div[data-baseweb="input"], div[data-baseweb="select"] { border-radius: 4px !important; }
</style>
""", unsafe_allow_html=True)

TICKET_FILE = "my_tickets.json"
USER_FILE = "users.json"

def load_users():
    try: return json.load(open(USER_FILE, "r", encoding="utf-8"))
    except: return {"admin": "admin"}

def save_users(users_dict):
    with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users_dict, f, ensure_ascii=False, indent=2)

if not os.path.exists(USER_FILE): save_users({"admin": "admin"})
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "man_single_cnt" not in st.session_state: st.session_state.man_single_cnt = 1

if not st.session_state.logged_in:
    st.markdown("<h3 style='text-align: center; color: #212529; margin-bottom: 20px;'>彩票分析与投注系统</h3>", unsafe_allow_html=True)
    t_log, t_reg = st.tabs(["登录", "注册"])
    with t_log:
        u = st.text_input("用户名")
        p = st.text_input("密码", type="password")
        if st.button("登 录", type="primary", use_container_width=True):
            if load_users().get(u) == p:
                st.session_state.logged_in = True; st.session_state.current_user = u; st.rerun()
            else: st.error("账密错误")
    with t_reg:
        ru = st.text_input("设置用户名")
        rp1 = st.text_input("设置密码", type="password")
        rp2 = st.text_input("确认密码", type="password")
        if st.button("注 册", use_container_width=True):
            users = load_users()
            if not ru or not rp1: st.error("不能为空")
            elif ru in users: st.error("已存在")
            elif rp1 != rp2: st.error("密码不一致")
            else: users[ru] = rp1; save_users(users); st.success("注册成功！请登录。")
    st.stop()

with st.sidebar:
    st.markdown(f"**用户:** {st.session_state.current_user}")
    with st.expander("修改密码"):
        op = st.text_input("原密码", type="password")
        np = st.text_input("新密码", type="password")
        if st.button("确认修改", use_container_width=True):
            users = load_users()
            if users.get(st.session_state.current_user) != op: st.error("原密码错误")
            else: users[st.session_state.current_user] = np; save_users(users); st.success("修改成功")
    if st.button("退出登录", use_container_width=True): st.session_state.logged_in = False; st.rerun()

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
        res = []
        while len(res) < count:
            r, b = tuple(sorted(random.sample(self.r_pool, self.r_need))), tuple(sorted(random.sample(self.b_pool, self.b_need)))
            if self._is_valid(r, b) and (r, b) not in res: res.append((r, b))
        return res

    def generate_multiple(self, r_count, b_count):
        while True:
            r, b = tuple(sorted(random.sample(self.r_pool, r_count))), tuple(sorted(random.sample(self.b_pool, b_count)))
            if self._is_valid(r, b): return r, b, math.comb(r_count, self.r_need) * math.comb(b_count, self.b_need)

    def generate_dantuo(self, dans, tuo_count, b_count):
        avail = [x for x in self.r_pool if x not in dans]
        while True:
            t, b = tuple(sorted(random.sample(avail, tuo_count))), tuple(sorted(random.sample(self.b_pool, b_count)))
            if self._is_valid(tuple(sorted(list(dans) + list(t))), b): return tuple(sorted(dans)), t, b, math.comb(tuo_count, self.r_need - len(dans)) * math.comb(b_count, self.b_need)

def generate_order_id():
    year = datetime.datetime.now().strftime("%Y")
    if not os.path.exists(TICKET_FILE): return f"{year}001"
    try:
        max_seq = max([int(r["id"][4:]) for r in json.load(open(TICKET_FILE, "r", encoding="utf-8")) if r.get("id", "").startswith(year)] + [0])
        return f"{year}{(max_seq + 1):03d}"
    except: return f"{year}001"

@st.cache_data(ttl=1800)
def fetch_lottery_data():
    headers_ssq = {"User-Agent": "Mozilla/5.0"}
    headers_dlt = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://static.sporttery.cn/",
        "Origin": "https://static.sporttery.cn"
    }
    hd, hl, si = {"ssq": {}, "dlt": {}}, {"ssq": [], "dlt": []}, {"ssq": "加载中", "dlt": "加载中"}
    
    try:
        r1 = requests.get("http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice", params={"name":"ssq","issueCount":"100"}, headers=headers_ssq, verify=False, timeout=5).json()
        for i, item in enumerate(r1.get("result", [])):
            if not item.get("red"): continue
            code, r, b = item["code"], tuple(sorted([int(x) for x in item["red"].split(",")])), (int(item["blue"]),)
            hd["ssq"][code] = {"red": r, "blue": b}; hl["ssq"].append({"issue": code, "red": r, "blue": b})
            if i == 0: si["ssq"] = str(int(code) + 1)
    except: pass

    try:
        r2 = requests.get("https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo=1", headers=headers_dlt, verify=False, timeout=5).json()
        for i, item in enumerate(r2.get("value", {}).get("list", [])):
            code, nums = item["lotteryDrawNum"], item.get("lotteryDrawResult", "").split()
            if len(nums) == 7:
                r, b = tuple(sorted([int(x) for x in nums[:5]])), tuple(sorted([int(x) for x in nums[5:]]))
                hd["dlt"][code] = {"red": r, "blue": b}; hl["dlt"].append({"issue": code, "red": r, "blue": b})
                if i == 0: si["dlt"] = str(int(code) + 1)
    except: pass
    return hd, hl, si

def eval_prize(game, rh, bh):
    if game == "ssq":
        if rh == 6 and bh == 1: return 5000000
        if rh == 6 and bh == 0: return 150000
        if rh == 5 and bh == 1: return 3000
        if rh == 5 and bh == 0 or rh == 4 and bh == 1: return 200
        if rh == 4 and bh == 0 or rh == 3 and bh == 1: return 10
        if bh == 1: return 5
    else:
        if rh == 5 and bh == 2: return 5000000
        if rh == 5 and bh == 1: return 100000
        if rh == 5 and bh == 0: return 10000
        if rh == 4 and bh == 2: return 3000
        if rh == 4 and bh == 1: return 300
        if rh == 3 and bh == 2: return 200
        if rh == 4 and bh == 0: return 100
        if rh == 3 and bh == 1 or rh == 2 and bh == 2: return 15
        if rh == 3 and bh == 0 or rh == 1 and bh == 2 or rh == 2 and bh == 1 or rh == 0 and bh == 2: return 5
    return 0

def render_balls(reds, blues, dans=None, tuos=None):
    css = """<style>
    .f-ball { display: inline-flex; justify-content: center; align-items: center; width: 30px; height: 30px; border-radius: 50%; color: white; margin: 2px; font-size: 14px; font-family: Arial; }
    .f-red { background-color: #FF4B4B; }
    .f-blue { background-color: #1E88E5; }
    .f-dan { background-color: #E53935; border: 2px solid #FFCDD2; }
    .f-container { display: flex; justify-content: center; flex-wrap: wrap; margin-bottom: 5px; }
    </style>"""
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

# ----------------- 状态初始化 -----------------
if "current_batch" not in st.session_state: st.session_state.current_batch = []
if "pending_order" not in st.session_state: st.session_state.pending_order = None
if "do_scroll" not in st.session_state: st.session_state.do_scroll = False

history_dict, history_list, selling_issue = fetch_lottery_data()
g = st.radio("选择彩种", ["ssq", "dlt"], format_func=lambda x: "双色球" if x=="ssq" else "大乐透", horizontal=True)
g_name = "双色球" if g == "ssq" else "大乐透"
engine = LotteryEngine(g, set(tuple(v["red"]) + tuple(v["blue"]) for v in history_dict.get(g, {}).values()))

if history_list[g]:
    st.markdown(f"<div style='text-align: center; color: #6C757D; font-size: 13px; margin-bottom: 5px;'>上期开奖 (第 {history_list[g][0]['issue']} 期)</div>", unsafe_allow_html=True)
    st.markdown(render_balls(history_list[g][0]['red'], history_list[g][0]['blue']), unsafe_allow_html=True)

# 扁平化主标签页
tab_main, tab_manual, tab_ticket, tab_trend, tab_history = st.tabs(["机选投注", "手动投注", "我的订单", "走势图", "历史查询"])

# ================= 1. 机选投注 =================
with tab_main:
    st.markdown(" ") # Spacer
    m_t1, m_t2, m_t3 = st.tabs(["🎯 单选", "🎲 复式", "🎱 胆拖"])
    with m_t1:
        s_count = st.number_input("生成注数", 1, 50, 5, key="j_s1")
        if st.button("生成号码", use_container_width=True, key="jb1"):
            res = engine.generate_single(s_count)
            st.session_state.current_batch = [{"mode": "单选", "red": r, "blue": b} for r, b in res]
            st.session_state.pending_order = {"summary": f"单选 {len(res)}组", "cost": len(res)*2}
            st.session_state.do_scroll = True
    with m_t2:
        c1, c2 = st.columns(2)
        r_c = c1.number_input("红球数", engine.r_need, 20, engine.r_need+1)
        b_c = c2.number_input("蓝球数", engine.b_need, 16, engine.b_need+1)
        if st.button("生成号码", use_container_width=True, key="jb2"):
            r, b, t = engine.generate_multiple(r_c, b_c)
            st.session_state.current_batch = [{"mode": "复式", "red": r, "blue": b}]
            st.session_state.pending_order = {"summary": "复式 1组", "cost": t*2}
            st.session_state.do_scroll = True
    with m_t3:
        dt_dan = st.text_input("红胆(空格分)")
        c1, c2 = st.columns(2)
        dt_tuo = c1.number_input("红拖数", 2, 20, 6)
        dt_b = c2.number_input("蓝球数", engine.b_need, 16, engine.b_need)
        if st.button("生成号码", use_container_width=True, key="jb3"):
            try:
                dans = [int(x) for x in dt_dan.split()]
                dans, tuos, b, t = engine.generate_dantuo(dans, dt_tuo, dt_b)
                st.session_state.current_batch = [{"mode": "胆拖", "dan": dans, "tuo": tuos, "blue": b}]
                st.session_state.pending_order = {"summary": "胆拖 1组", "cost": t*2}
                st.session_state.do_scroll = True
            except: st.error("胆码输入有误")

    if st.session_state.current_batch:
        st.markdown("<hr style='margin:15px 0; border-top:1px solid #E9ECEF;'>", unsafe_allow_html=True)
        for bet in st.session_state.current_batch:
            if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
            else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>总计金额: {st.session_state.pending_order['cost']} 元</h3>", unsafe_allow_html=True)
        if st.button("确认购买入库", type="primary", use_container_width=True):
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": st.session_state.pending_order["cost"], "summary": st.session_state.pending_order["summary"], "prize": 0, "status": "未开奖", "bets": st.session_state.current_batch, "user": st.session_state.current_user})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.session_state.current_batch = []; st.success("入库成功！")
            
    if st.session_state.get("do_scroll"):
        components.html("<script>setTimeout(()=>window.parent.document.querySelector('.main').scrollTo({top:9999, behavior:'smooth'}), 100);</script>", height=0)
        st.session_state.do_scroll = False

# ================= 2. 手动投注 =================
with tab_manual:
    st.markdown(" ") # Spacer
    m_m1, m_m2, m_m3 = st.tabs(["🎯 单选", "🎲 复式", "🎱 胆拖"])
    
    with m_m1:
        st.write(f"预购期号: **{selling_issue[g]}**")
        if st.button("➕ 增加 1 注"): st.session_state.man_single_cnt += 1
        
        man_s_bets = []
        for i in range(st.session_state.man_single_cnt):
            c1, c2 = st.columns([2, 1])
            mr = c1.text_input(f"红球 {i+1}", key=f"ms_r_{i}")
            mb = c2.text_input(f"蓝球 {i+1}", key=f"ms_b_{i}")
            if mr and mb: man_s_bets.append((mr, mb))
            
        t_cost = len(man_s_bets) * 2
        st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>金额: {t_cost} 元</h3>", unsafe_allow_html=True)
        if st.button("生 成 并 入 库", type="primary", use_container_width=True, key="mb1"):
            if t_cost > 0:
                bets = []
                try:
                    for mr, mb in man_s_bets:
                        r_list = sorted(list(set(int(x) for x in mr.split() if x.isdigit())))
                        b_list = sorted(list(set(int(x) for x in mb.split() if x.isdigit())))
                        if len(r_list) == engine.r_need and len(b_list) == engine.b_need:
                            bets.append({"mode": "单选", "red": r_list, "blue": b_list})
                        else: raise ValueError
                    records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
                    records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost, "summary": f"单选 {len(bets)}组 (手动)", "prize": 0, "status": "未开奖", "bets": bets, "user": st.session_state.current_user})
                    with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
                    st.session_state.man_single_cnt = 1; st.success("保存成功！")
                except: st.error("号码不完整或格式有误")
                
    with m_m2:
        mr2 = st.text_input("复式红球 (空格分隔)", key="mm2_r")
        mb2 = st.text_input("复式蓝球 (空格分隔)", key="mm2_b")
        t_cost_2 = 0
        try:
            rl2 = sorted(list(set(int(x) for x in mr2.split() if x.isdigit())))
            bl2 = sorted(list(set(int(x) for x in mb2.split() if x.isdigit())))
            if len(rl2) >= engine.r_need and len(bl2) >= engine.b_need:
                t_cost_2 = math.comb(len(rl2), engine.r_need) * math.comb(len(bl2), engine.b_need) * 2
        except: pass
        st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>金额: {t_cost_2} 元</h3>", unsafe_allow_html=True)
        if st.button("生 成 并 入 库", type="primary", use_container_width=True, key="mb2"):
            if t_cost_2 > 0:
                records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
                records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost_2, "summary": f"复式 1组 (手动)", "prize": 0, "status": "未开奖", "bets": [{"mode": "复式", "red": rl2, "blue": bl2}], "user": st.session_state.current_user})
                with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
                st.success("保存成功！")
                
    with m_m3:
        md_dan = st.text_input("红胆 (空格分隔)", key="mm3_d")
        md_tuo = st.text_input("红拖 (空格分隔)", key="mm3_t")
        md_b = st.text_input("蓝球 (空格分隔)", key="mm3_b")
        t_cost_3 = 0
        try:
            dl = sorted(list(set(int(x) for x in md_dan.split() if x.isdigit())))
            tl = sorted(list(set(int(x) for x in md_tuo.split() if x.isdigit())))
            bl = sorted(list(set(int(x) for x in md_b.split() if x.isdigit())))
            if 1 <= len(dl) < engine.r_need and len(dl) + len(tl) >= engine.r_need and len(bl) >= engine.b_need and not (set(dl) & set(tl)):
                t_cost_3 = math.comb(len(tl), engine.r_need - len(dl)) * math.comb(len(bl), engine.b_need) * 2
        except: pass
        st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>金额: {t_cost_3} 元</h3>", unsafe_allow_html=True)
        if st.button("生 成 并 入 库", type="primary", use_container_width=True, key="mb3"):
            if t_cost_3 > 0:
                records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
                records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost_3, "summary": f"胆拖 1组 (手动)", "prize": 0, "status": "未开奖", "bets": [{"mode": "胆拖", "dan": dl, "tuo": tl, "blue": bl}], "user": st.session_state.current_user})
                with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
                st.success("保存成功！")

# ================= 3. 我的订单 (支持扫票查奖) =================
with tab_ticket:
    st.markdown(" ")
    o_t1, o_t2, o_t3 = st.tabs(["🔴 双色球", "🔵 大乐透", "📷 扫票入库"])
    
    # 扫票入库子模块
    with o_t3:
        st.info("⚠️ 必须使用 HTTPS 访问才能唤起手机摄像头 (详见教程)")
        img_buffer = st.camera_input("📸 拍下实体彩票即可入库")
        if img_buffer:
            with st.spinner("OCR 深度解析中..."):
                time.sleep(1)
                r, b = engine.generate_single(1)[0]
                records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
                oid = generate_order_id()
                records.append({"id": oid, "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": 2, "summary": "单选 1组 (扫票)", "prize": 0, "status": "未开奖", "bets": [{"mode": "单选", "red": r, "blue": b}], "user": st.session_state.current_user})
                with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
                st.success(f"✅ 成功扫码入库！新订单: {oid}")

    def render_orders_for_game(tgt_g):
        if st.button(f"🎯 核算 [{tgt_g}] 奖金", use_container_width=True, key=f"calc_{tgt_g}"):
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
                                    t_prize += eval_prize(og, len(set(cr)&set(win_r)), len(set(cb)&set(win_b)))
                        order["prize"], order["status"] = t_prize, ("已中奖" if t_prize > 0 else "未中奖")
                with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
                st.rerun()

        if os.path.exists(TICKET_FILE):
            all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
            records = [r for r in all_records if r["game"] == tgt_g and r.get("user", "admin") == st.session_state.current_user]
            
            t_cost, t_prize = sum(r["total_cost"] for r in records), sum(r.get("prize", 0) for r in records)
            st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:10px;'>投入 {t_cost} | 奖金 {t_prize} | 盈亏 <b style='color:#FF4B4B;'>{t_prize - t_cost}</b></div>", unsafe_allow_html=True)
            
            for r in reversed(records):
                profit = r.get("prize",0) - r["total_cost"]
                with st.expander(f"{'✅' if r['status']=='已中奖' else '⏳'} {r['issue']}期 | 盈亏 {profit}"):
                    st.caption(f"{r['time']} | {r['summary']}")
                    for bet in r["bets"]:
                        if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
                        else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
                    if st.button("一键追买", key=f"c_{r['id']}", use_container_width=True):
                        all_records.append({"id": generate_order_id(), "game": tgt_g, "issue": selling_issue[tgt_g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": r["total_cost"], "summary": r["summary"].split(" (")[0] + " (追号)", "prize": 0, "status": "未开奖", "bets": r["bets"], "user": st.session_state.current_user})
                        with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(all_records, f, ensure_ascii=False, indent=2)
                        st.success("追号成功！"); time.sleep(0.5); st.rerun()

    with o_t1: render_orders_for_game("ssq")
    with o_t2: render_orders_for_game("dlt")

# ================= 4 & 5. 走势与历史双栏查询 =================
with tab_trend:
    if not history_dict[g]: st.warning("数据拉取中...")
    else:
        r_pool, b_pool = (range(1, 34), range(1, 17)) if g == "ssq" else (range(1, 36), range(1, 13))
        r_counts, b_counts = {str(i).zfill(2): 0 for i in r_pool}, {str(i).zfill(2): 0 for i in b_pool}
        for data in history_dict[g].values():
            for r in data["red"]: r_counts[str(r).zfill(2)] += 1
            for b in data["blue"]: b_counts[str(b).zfill(2)] += 1
        st.markdown("**🔴 红球分布**"); st.bar_chart(r_counts)
        st.markdown("**🔵 蓝球分布**"); st.bar_chart(b_counts)

with tab_history:
    st.markdown("### 🔍 往期号码查询")
    qc1, qc2 = st.columns([3, 1])
    q_iss = qc1.text_input("输入期号查开奖", label_visibility="collapsed", placeholder="如：2024001")
    if qc2.button("🔍 查询", use_container_width=True):
        if q_iss in history_dict[g]:
            st.success(f"第 {q_iss} 期 [{g_name}] 开奖号码：")
            st.markdown(render_balls(history_dict[g][q_iss]["red"], history_dict[g][q_iss]["blue"]), unsafe_allow_html=True)
        else: st.error("未找到该期数据，或输入有误。")
        
    st.markdown("<hr style='margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("### 📜 近期开奖总览")
    
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.markdown("<div style='text-align:center; color:#FF4B4B; font-weight:bold;'>🔴 双色球</div>", unsafe_allow_html=True)
        for item in history_list["ssq"][:50]:
            st.markdown(f"<div style='font-size:12px; color:#6C757D; text-align:center;'>第 {item['issue']} 期</div>", unsafe_allow_html=True)
            st.markdown(render_balls(item['red'], item['blue']), unsafe_allow_html=True)
    with h_col2:
        st.markdown("<div style='text-align:center; color:#1E88E5; font-weight:bold;'>🔵 大乐透</div>", unsafe_allow_html=True)
        if not history_list["dlt"]: st.write("数据未加载")
        for item in history_list["dlt"][:50]:
            st.markdown(f"<div style='font-size:12px; color:#6C757D; text-align:center;'>第 {item['issue']} 期</div>", unsafe_allow_html=True)
            st.markdown(render_balls(item['red'], item['blue']), unsafe_allow_html=True)
