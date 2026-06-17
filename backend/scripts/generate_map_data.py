"""
生成社区模拟居民地理位置数据。
默认生成 45 条，坐标统一在青岛市西海岸新区三沙路街道。
"""
import numpy as np
import json
import sys
import os

# 将 backend/ 加入 path 以便引用 core 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 青岛市西海岸新区三沙路街道中心点
CENTER_LAT = 35.788058
CENTER_LNG = 120.029416


def generate_community_data(num_points: int = 45) -> list[dict]:
    np.random.seed(42)

    # 街道范围内随机偏移（东侧临海，经度偏移收窄避免越界入海）
    lats = CENTER_LAT + np.random.uniform(-0.005, 0.005, num_points)
    lngs = CENTER_LNG + np.random.uniform(-0.008, 0.005, num_points)

    # 风险分布：60% 低风险，25% 中风险，15% 高危
    risk_levels = ["低风险", "中风险", "高危"]
    statuses = np.random.choice(risk_levels, size=num_points, p=[0.6, 0.25, 0.15])

    surnames = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
                "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
                "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
                "苏", "卢", "蒋", "蔡", "贾"]

    data = []
    for i in range(num_points):
        # 根据风险等级生成不同范围的体征数据
        status = statuses[i]
        if status == "高危":
            systolic = int(np.random.randint(160, 200))
            diastolic = int(np.random.randint(95, 120))
        elif status == "中风险":
            systolic = int(np.random.randint(135, 165))
            diastolic = int(np.random.randint(85, 100))
        else:
            systolic = int(np.random.randint(105, 140))
            diastolic = int(np.random.randint(65, 90))

        data.append({
            "user_id": f"resident_{i + 1:03d}",
            "name": f"{surnames[i]}大爷" if i % 3 == 0 else f"{surnames[i]}奶奶" if i % 3 == 1 else f"{surnames[i]}阿姨",
            "lat": float(lats[i]),
            "lng": float(lngs[i]),
            "status": str(status),
            "last_update": f"2026-06-15 {np.random.randint(6, 20):02d}:{np.random.randint(0, 60):02d}",
            "systolic": systolic,
            "diastolic": diastolic,
        })

    return data


if __name__ == "__main__":
    from core.paths import COMMUNITY_DATA_PATH

    data = generate_community_data(45)
    COMMUNITY_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(COMMUNITY_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已生成 {len(data)} 条社区模拟数据: {COMMUNITY_DATA_PATH}")
    # 统计风险分布
    stats = {}
    for r in data:
        stats[r["status"]] = stats.get(r["status"], 0) + 1
    for k, v in stats.items():
        print(f"  {k}: {v} ({v/len(data)*100:.0f}%)")
