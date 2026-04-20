import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Sales Analyzer", layout="wide")

st.title("📊 تحليل المبيعات الفعلية")

YOUR_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7Il9pZCI6IjY5Y2VlY2Y1MTk3Zjg0NWZjOWZlZGU1YyJ9LCJpYXQiOjE3NzUxNjg3NTcsImV4cCI6MTc3Nzc2MDc1N30.nIKi8ohQAYsAVXQL9_rlRUr93TDg-G-DVOCQOrRdOtY"

# اختيار نوع العنصر
item_type = st.selectbox("اختر نوع العنصر:", [
    "jet", "tank", "boots5", "boots6", "chest5", "chest6",
    "gloves5", "gloves6", "pants5", "pants6", "helmet5", "helmet6"
])

def fetch_transactions(item_code, limit=50):
    API_URL = "https://api4.warera.io/trpc/transaction.getPaginatedTransactions?batch=1"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"jwt={YOUR_JWT}",
        "User-Agent": "Mozilla/5.0"
    }
    
    payload = {"0": {"itemCode": item_code, "limit": limit, "direction": "forward"}}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data[0].get('result', {}).get('data', {}).get('items', [])
            return items
    except:
        pass
    return []

if st.button("جلب المبيعات"):
    with st.spinner("جاري جلب البيانات..."):
        transactions = fetch_transactions(item_type, limit=100)
    
    if transactions:
        sales_data = []
        for tx in transactions:
            item_info = tx.get('item', {})
            skills = item_info.get('skills', {})
            
            sales_data.append({
                'السعر': tx.get('money'),
                'الوقت': tx.get('createdAt'),
                'الهجوم': skills.get('attack', 0),
                'الكريتيكال': skills.get('criticalChance', 0),
                'الدفاع': skills.get('armor', 0),
                'المراوغة': skills.get('dodge', 0),
                'الدقة': skills.get('precision', 0)
            })
        
        df = pd.DataFrame(sales_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("عدد المبيعات", len(df))
        with col2:
            st.metric("متوسط السعر", f"${df['السعر'].mean():.2f}")
        with col3:
            st.metric("أقل/أعلى سعر", f"${df['السعر'].min():.2f} / ${df['السعر'].max():.2f}")
        
        st.subheader("آخر المبيعات")
        st.dataframe(df.head(20), use_container_width=True)
        
        df['الوقت'] = pd.to_datetime(df['الوقت'])
        fig = px.line(df.sort_values('الوقت'), x='الوقت', y='السعر', 
                      title=f'تطور أسعار {item_type}', markers=True)
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("لا توجد مبيعات مسجلة")

            # بعد ما تجيب البيانات، احفظها في cache
    if transactions:
        cache = {}
        for tx in transactions:
            item_info = tx.get('item', {})
            skills = item_info.get('skills', {})
            item_code = tx.get('itemCode')
            
            if item_code not in cache:
                cache[item_code] = []
            
            # استخراج القيمة الرئيسية
            if item_code in ['jet', 'tank']:
                main_value = skills.get('attack', 0)
            else:
                main_value = skills.get('armor', 0) or skills.get('dodge', 0) or skills.get('precision', 0) or skills.get('criticalDamages', 0)
            
            cache[item_code].append({
                'price': tx.get('money'),
                'time': tx.get('createdAt'),
                'main_value': main_value
            })
        
        # حفظ في ملف
        import json
        import os
        os.makedirs("data", exist_ok=True)
        with open("data/sales_cache.json", "w") as f:
            json.dump(cache, f, indent=2)
        st.success("✅ تم حفظ بيانات المبيعات للتطبيق الرئيسي!")