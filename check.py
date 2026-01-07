import google.generativeai as genai

# ==============================
# 🔑 ใส่กุญแจเดิมของคุณตรงนี้
MY_API_KEY = "AIzaSyCpyKcpli54w8RUi0LSFqy2j8kx1hk50Qk" 
# ==============================

genai.configure(api_key=MY_API_KEY)

print("กำลังเช็กรายชื่อโมเดล... รอแป๊บนะครับ...")

try:
    # สั่งให้ลิสต์รายชื่อโมเดลทั้งหมดออกมา
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")