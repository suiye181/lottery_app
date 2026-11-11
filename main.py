from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random, itertools, math, json, os, datetime

app = FastAPI(title="彩票系统 API 接口")
TICKET_FILE = "my_tickets.json"

# ================= 核心算法库 (保持不变) =================
class LotteryEngine:
    def __init__(self, game_type="ssq"):
        self.game_type = game_type
        if game_type == "ssq": 
            self.r_pool, self.r_need, self.b_pool, self.b_need = list(range(1, 34)), 6, list(range(1, 17)), 1
        else: 
            self.r_pool, self.r_need, self.b_pool, self.b_need = list(range(1, 36)), 5, list(range(1, 13)), 2

    def generate_single(self, count=1):
        res = []
        while len(res) < count:
            r = tuple(sorted(random.sample(self.r_pool, self.r_need)))
            b = tuple(sorted(random.sample(self.b_pool, self.b_need)))
            if (r, b) not in res: res.append({"red": r, "blue": b})
        return res

engine_ssq = LotteryEngine("ssq")
engine_dlt = LotteryEngine("dlt")

# ================= 数据验证模型 (Pydantic) =================
class BetItem(BaseModel):
    mode: str  # "单选", "复式", "胆拖"
    red: Optional[List[int]] = None
    blue: List[int]
    dan: Optional[List[int]] = None
    tuo: Optional[List[int]] = None

class OrderRequest(BaseModel):
    game: str      # "ssq" 或 "dlt"
    issue: str     # 期号，如 "2024001"
    summary: str   # 描述，如 "单选 5 组"
    bets: List[BetItem]
    user: str = "admin"

# ================= API 路由接口 =================

@app.get("/")
def read_root():
    return {"status": "ok", "message": "彩票 API 服务已启动"}

@app.get("/api/generate")
def generate_numbers(game: str = "ssq", count: int = 5):
    """前端调用此接口获取机选号码"""
    engine = engine_ssq if game == "ssq" else engine_dlt
    try:
        results = engine.generate_single(count)
        return {"code": 200, "data": results, "cost": count * 2}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tickets")
def get_tickets(user: str = "admin"):
    """前端调用此接口获取用户的历史订单"""
    if not os.path.exists(TICKET_FILE): return {"code": 200, "data": []}
    with open(TICKET_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
    user_records = [r for r in records if r.get("user") == user]
    return {"code": 200, "data": user_records}

@app.post("/api/tickets")
def save_ticket(order: OrderRequest):
    """前端将用户选好的号码提交到此接口进行 JSON 入库"""
    records = []
    if os.path.exists(TICKET_FILE):
        with open(TICKET_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
            
    # 生成订单号
    year = datetime.datetime.now().strftime("%Y")
    max_seq = max([int(r['id'][4:]) for r in records if r.get('id', '').startswith(year)] + [0]) if records else 0
    order_id = f"{year}{(max_seq + 1):03d}"
    
    # 计算总金额
    total_cost = sum([2 for _ in order.bets]) # 此处为了演示简化为单注计费，实际需补充复式算价公式
    
    new_order = {
        "id": order_id,
        "game": order.game,
        "issue": order.issue,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_cost": total_cost,
        "summary": order.summary,
        "prize": 0,
        "status": "未开奖",
        "bets": [bet.dict(exclude_none=True) for bet in order.bets],
        "user": order.user
    }
    
    records.append(new_order)
    with open(TICKET_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        
    return {"code": 200, "message": "入库成功", "order_id": order_id}
