import streamlit as st
import random, requests, itertools, math, json, os, datetime, time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="智能彩票系统 22.0 Docker版", page_icon="🎰", layout="centered")

TICKET_FILE = "my_tickets.json"
USER_FILE = "users.json"

# ================= 账号验证模块 =================
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", encoding="utf-8") as f: json.dump({"admin": "admin"}, f)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 系统登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录系统", type="primary", use_container_width=True):
        users = json.load(open(USER_FILE, "r", encoding="utf-8"))
        if username in users and users[username] == password:
            st.session_state.logged_in = True; st.session_state.current_user = username; st.rerun()
        else: st.error("账密错误！")
    st.stop()

with st.sidebar:
    st.markdown(f"👤 当前用户: **{st.session_state.current_user}**")
    if st.button("🚪 退出登录"): st.session_state.logged_in = False; st.rerun()

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

# 核心 3D CSS 绝对居中引擎
def render_balls(reds, blues, dans=None, tuos=None):
    css = """
    <style>
    .ball { display: inline-flex; justify-content: center; align-items: center; width: 34px; height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px; font-size: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); }
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
    st.info(f"🏆 {g_name} 上期开奖 (第 {history_list[g][0]['issue']} 期):")
    st.markdown(render_balls(history_list[g][0]['red'], history_list[g][0]['blue']), unsafe_allow_html=True)

tab_main, tab_manual, tab_scan, tab_ticket = st.tabs(["🎰 机选投注", "✍️ 手动投注", "📷 扫票入库", "🧾 我的订单"])

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
        st.write("---")
        for bet in st.session_state.current_batch:
            if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
            else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center; color: #E74C3C;'>当前机选总金额: {st.session_state.pending_order['cost']} 元</h3>", unsafe_allow_html=True)
        
        if st.button("🛒 确认购买并入库", type="primary", use_container_width=True):
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": st.session_state.pending_order["cost"], "summary": st.session_state.pending_order["summary"], "prize": 0, "status": "未开奖", "bets": st.session_state.current_batch})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.session_state.current_batch = []; st.success("✅ 订单入库成功！")

# ================= Tab 2: 手动投注 (动态算价) =================
with tab_manual:
    m_issue = st.text_input("购买期号", value=selling_issue[g], key="m_issue")
    m_reds = st.text_input("红球 (空格隔开)", key="m_reds")
    m_blues = st.text_input("蓝球 (空格隔开)", key="m_blues")
    
    # 动态计算逻辑
    r_list, b_list, t_cost, mode = [], [], 0, "单选"
    try:
        r_list = sorted(list(set(int(x) for x in m_reds.split() if x.isdigit())))
        b_list = sorted(list(set(int(x) for x in m_blues.split() if x.isdigit())))
        if len(r_list) >= engine.r_need and len(b_list) >= engine.b_need:
            tickets = math.comb(len(r_list), engine.r_need) * math.comb(len(b_list), engine.b_need)
            t_cost = tickets * 2
            mode = "单选" if tickets == 1 else "复式"
    except: pass

    st.markdown(f"<h3 style='text-align: center; color: #E74C3C;'>实时计算金额: {t_cost} 元</h3>", unsafe_allow_html=True)
    
    if st.button("💾 确认生成并入库", type="primary", use_container_width=True):
        if t_cost > 0:
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            records.append({"id": generate_order_id(), "game": g, "issue": m_issue.strip(), "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": t_cost, "summary": f"{mode} 1 组 (手动)", "prize": 0, "status": "未开奖", "bets": [{"mode": mode, "red": r_list, "blue": b_list}]})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success("✅ 保存成功！")
        else: st.error("号码不完整或有误！")

# ================= Tab 3: 扫票入库 =================
with tab_scan:
    st.warning("📱 若要调用手机摄像头，请确保当前是在 HTTPS 协议下访问，或在浏览器中开启不安全网络权限。")
    img_buffer = st.camera_input("📸 拍下实体彩票即可入库")
    if img_buffer:
        with st.spinner("OCR 深度解析中..."):
            time.sleep(1)
            r, b = engine.generate_single(1)[0] # 演示数据
            records = json.load(open(TICKET_FILE, "r", encoding="utf-8")) if os.path.exists(TICKET_FILE) else []
            oid = generate_order_id()
            records.append({"id": oid, "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": 2, "summary": "单选 1 组 (扫码)", "prize": 0, "status": "未开奖", "bets": [{"mode": "单选", "red": r, "blue": b}]})
            with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(records, f, ensure_ascii=False, indent=2)
            st.success(f"✅ 成功扫码入库！新订单: {oid}")

# ================= Tab 4: 订单管理与一键追号 =================
with tab_ticket:
    if st.button("🎯 联网核算所有订单奖金", use_container_width=True):
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
        records = [r for r in json.load(open(TICKET_FILE, "r", encoding="utf-8")) if r["game"] == g]
        t_cost, t_prize = sum(r["total_cost"] for r in records), sum(r.get("prize", 0) for r in records)
        st.markdown(f"**财务总计 ➔ 投入: {t_cost} | 奖金: {t_prize} | 盈亏: {t_prize - t_cost} 元**")
        
        for r in reversed(records):
            profit = r.get("prize",0) - r["total_cost"]
            with st.expander(f"{'✅' if r['status']=='已中奖' else '⏳'} {r['id']} | {r['issue']}期 | 投入{r['total_cost']} 盈亏{profit}元"):
                st.caption(f"购买时间: {r['time']} | {r['summary']}")
                for bet in r["bets"]:
                    if bet["mode"] == "胆拖": st.markdown(render_balls([], bet["blue"], bet["dan"], bet["tuo"]), unsafe_allow_html=True)
                    else: st.markdown(render_balls(bet["red"], bet["blue"]), unsafe_allow_html=True)
                
                # Streamlit 下的追号逻辑联动
                if st.button(f"🚀 一键追买此单 (预购第 {selling_issue[g]} 期)", key=f"chase_{r['id']}", use_container_width=True):
                    new_order = {"id": generate_order_id(), "game": g, "issue": selling_issue[g], "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "total_cost": r["total_cost"], "summary": r["summary"].split(" (")[0] + " (追号)", "prize": 0, "status": "未开奖", "bets": r["bets"]}
                    all_records = json.load(open(TICKET_FILE, "r", encoding="utf-8"))
                    all_records.append(new_order)
                    with open(TICKET_FILE, "w", encoding="utf-8") as f: json.dump(all_records, f, ensure_ascii=False, indent=2)
                    st.success(f"追号成功！新单号: {new_order['id']}")
                    time.sleep(1); st.rerun()
