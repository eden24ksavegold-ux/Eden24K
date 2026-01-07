import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image
import io
import csv
import os
from datetime import datetime

# --- 1. ตั้งค่า App และแก้ปัญหา CORS ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ตั้งค่า Gemini AI ⚠️ ใส่ API Key ---
import google.generativeai as genai

# 🔑 ใส่คีย์หลายๆ ตัวไว้ตรงนี้ครับ ตัวไหนโดนแบน ระบบจะข้ามไปตัวถัดไปเอง
GEMINI_KEYS = [
    "AIzaSyBtqbspDzMcYuKxE58NnkATTOAdoO40-h8", # คีย์หลัก
    "AIzaSyAvZvbG4-3IIO21H8RB6wT49WtAjiu0bWw", # คีย์สำรอง 1
    "AIzaSyCjY9vgYA4pvQGtKuLTw3s5gBtraNpKlzI", # คีย์สำรอง 2
]

# ✅ วางในไฟล์ main.py เท่านั้น!
def analyze_chart(image_data, model_name):
    error_log = []
    
    for i, key in enumerate(GEMINI_KEYS):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name) # ใช้ชื่อรุ่นที่ส่งมาจากหน้าเว็บ
            
            response = model.generate_content(["วิเคราะห์กราฟนี้ให้หน่อย", image_data])
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"คีย์ตัวที่ {i+1} มีปัญหา: {error_msg}")
            error_log.append(error_msg)
            continue 

    return f"❌ คีย์ทั้งหมดใช้งานไม่ได้: {', '.join(error_log)}"
    error_log = []
    
    # วนลูปสลับคีย์หาตัวที่ใช้ได้
    for i, key in enumerate(GEMINI_KEYS):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            
            # โค้ดส่วนวิเคราะห์ภาพของบอส
            response = model.generate_content(["วิเคราะห์กราฟนี้ให้หน่อย", image_data])
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"คีย์ตัวที่ {i+1} มีปัญหา: {error_msg}")
            error_log.append(error_msg)
            continue # ลองคีย์ตัวถัดไป
            
    return f"❌ คีย์ทั้งหมดใช้งานไม่ได้: {', '.join(error_log)}"

# ใช้รุ่นใหม่ล่าสุด
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# --- 3. ฟังก์ชันช่วยบันทึกประวัติ ---
def save_to_csv(data):
    file_path = 'trade_history.csv'
    file_exists = os.path.isfile(file_path)
    try:
        with open(file_path, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"❌ บันทึก CSV ไม่ได้: {e}")

# ✅ ฟังก์ชันวิเคราะห์กราฟ (อัปเดตคำสั่ง 5 หัวข้อตามใจบอส)
@app.post("/api/analyze")
async def analyze_chart(file: UploadFile = File(...), type: str = Form(...), tf: str = Form(...)):
    print(f"🔍 กำลังวิเคราะห์กราฟ {type} Timeframe: {tf} ...")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # ⚡️ คำสั่งใหม่: เพิ่ม 5 หัวข้อวิเคราะห์เจาะลึก ⚡️
        prompt = f"""
        บทบาทของคุณ: คุณคือเซียนกราฟเทคนิคชาวไทย (Thai Trading Expert)
        โจทย์: วิเคราะห์กราฟ {type} Timeframe {tf}
        
        กฎเหล็ก: **ต้องตอบเป็น "ภาษาไทย" เท่านั้น ห้ามตอบภาษาอื่นเด็ดขาด**
        
        ขอ Output เป็น JSON Format เท่านั้น (ห้ามมี Markdown) ตามโครงสร้างนี้:
        {{
            "SIGNAL": "BUY หรือ SELL หรือ WAIT (ระบุคู่เงิน)",
            "CONFIDENCE": "ตัวเลข 0-100",
            "TP1": "ราคา",
            "TP2": "ราคา",
            "TP_HIGH": "ราคา",
            "SL": "ราคา",
            "ADVICE": [
                "เหตุผลข้อที่ 1 (อธิบายเป็นภาษาไทยเท่านั้น)",
                "เหตุผลข้อที่ 2 (อธิบายเป็นภาษาไทยเท่านั้น)",
                "ประมวลผล ซื้อ หรือ ขาย (อธิบายเป็นภาษาไทยเท่านั้น)",
                "กลยุทธ์การเข้าทำ (อธิบายเป็นภาษาไทยเท่านั้น)",
                "ข้อเสียการเข้าและออก ออเดอร์ (อธิบายเป็นภาษาไทยเท่านั้น)"
            ]
        }}
        """

        response = model.generate_content([prompt, image])
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        
        # บันทึกประวัติ
        save_to_csv({
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': type, 'Timeframe': tf, 'Signal': "Processed", 
            'Confidence': "100", 'Advice_Summary': "Gemini V.5 Analysis"
        })

        return { "signal": "Done", "confidence": 100, "advice": text_response }

    except Exception as e:
        print(f"❌ Error: {e}")
        return { "signal": "Error", "confidence": 0, "advice": f'{{"SIGNAL": "ERROR", "ADVICE": ["เกิดข้อผิดพลาด: {str(e)}"]}}' }

        response = model.generate_content([prompt, image])
        
        # แกะกล่อง JSON
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        
        # บันทึกประวัติ (คร่าวๆ)
        history_entry = {
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': type,
            'Timeframe': tf,
            'Signal': "Check Details", 
            'Confidence': "High",
            'Advice_Summary': "วิเคราะห์โดย Gemini 2.5"
        }
        save_to_csv(history_entry)

        # ส่งกลับไปหน้าเว็บ
        return {
            "signal": "Analyzed",
            "confidence": 100,
            "advice": text_response
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "signal": "Error",
            "confidence": 0,
            "advice": f'{{"SIGNAL": "ERROR", "ADVICE": ["เกิดข้อผิดพลาด: {str(e)}"]}}'
        }

# --- 5. API ดึงประวัติการเทรด ---
@app.get("/api/history")
async def get_history():
    file_path = 'trade_history.csv'
    if not os.path.isfile(file_path):
        return {"history": []}
    
    history = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in list(reader)[-20:]:
                history.append(row)
    except Exception as e:
        return {"history": []}
    
    return {"history": history[::-1]}

# --- 6. ส่วนรัน Server (ที่บอสทวงถาม) ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)