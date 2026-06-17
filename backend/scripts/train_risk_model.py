import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

# === 1. 配置路径 ===
# 确保模型保存到 backend/data 目录
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'risk_model.json')

# === 2. 模拟生成"国家级"健康数据 ===
def generate_mock_data(n_samples=5000):
    """
    生成 5000 条仿真居民健康数据
    特征: 年龄, 收缩压, 舒张压, 心率, 血氧, BMI
    标签: 0(低风险), 1(中风险), 2(高危)
    """
    np.random.seed(42)
    
    # 随机生成基础特征
    age = np.random.randint(20, 90, n_samples)
    systolic = np.random.normal(120, 20, n_samples)  # 收缩压 (高压)
    diastolic = np.random.normal(80, 15, n_samples)  # 舒张压 (低压)
    heart_rate = np.random.normal(75, 15, n_samples) # 心率
    spo2 = np.random.normal(97, 2, n_samples)        # 血氧 (大部分人是正常的)
    bmi = np.random.normal(24, 4, n_samples)         # BMI

    # === 3. 基于医学规则打标签 (Ground Truth) ===
    # 规则参考《国家基本公共卫生服务规范》
    labels = []
    for i in range(n_samples):
        risk_score = 0
        
        # 血压评分
        if systolic[i] > 180 or diastolic[i] > 110: risk_score += 5 # 极高危
        elif systolic[i] > 140 or diastolic[i] > 90: risk_score += 2
        
        # 血氧评分 (低血氧很危险)
        if spo2[i] < 90: risk_score += 5
        elif spo2[i] < 95: risk_score += 2
        
        # 心率评分
        if heart_rate[i] > 120 or heart_rate[i] < 50: risk_score += 3
        
        # 年龄与BMI加成
        if age[i] > 70: risk_score += 1
        if bmi[i] > 30: risk_score += 1

        # 判定等级
        if risk_score >= 5:
            labels.append(2) # 高危 (High Risk)
        elif risk_score >= 2:
            labels.append(1) # 中风险 (Medium Risk)
        else:
            labels.append(0) # 低风险 (Low Risk)

    # 创建 DataFrame
    df = pd.DataFrame({
        'age': age,
        'systolic': systolic,
        'diastolic': diastolic,
        'heart_rate': heart_rate,
        'spo2': spo2,
        'bmi': bmi,
        'label': labels
    })
    
    return df

# === 4. 训练 XGBoost 模型 ===
def train():
    print("正在生成仿真数据...")
    df = generate_mock_data()
    
    X = df.drop('label', axis=1)
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"开始训练模型 (样本数: {len(X_train)})...")
    
    # 初始化 XGBoost 分类器
    model = xgb.XGBClassifier(
        objective='multi:softprob', # 多分类概率
        num_class=3,                # 3个类别：低、中、高
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5
    )
    
    model.fit(X_train, y_train)
    
    # 验证精度
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"模型训练完成！测试集准确率: {acc*100:.2f}%")
    
    # === 5. 保存模型 ===
    # 注意：保存为 JSON 格式，通用性好，不需要 pickle
    model.save_model(MODEL_PATH)
    print(f"模型已保存至: {MODEL_PATH}")

if __name__ == "__main__":
    train()