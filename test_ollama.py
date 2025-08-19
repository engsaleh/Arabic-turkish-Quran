import subprocess
import json

# بيانات آية واحدة فقط للاختبار السريع
test_data = [{
    "verse_number": 1,
    "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    "turkish_translations": ["Rahman ve Rahim olan Allah'ın adıyla."]
}]

# نفس الـ Prompt الذي سنستخدمه في التطبيق
prompt_header = (
    "You are an expert in Quranic Arabic and Turkish linguistics. "
    "Respond ONLY with a valid JSON array where each object contains 'verse_number' and 'hybrid_translation'.\n\n"
    "Here is the data:\n"
)
prompt_data = json.dumps(test_data, indent=2, ensure_ascii=False)
full_prompt = prompt_header + prompt_data

print("---  يتم إرسال الطلب للاختبار ---")
print(full_prompt)
print("---------------------------------")

try:
    # تنفيذ الأمر مباشرةً كما سيفعل التطبيق
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=full_prompt.encode("utf-8"),
        capture_output=True,
        check=True,
        timeout=120 # مهلة دقيقتين للاختبار
    )

    # إذا نجح الأمر، اطبع الاستجابة
    response_text = result.stdout.decode("utf-8").strip()
    print("\n--- نجاح! الاستجابة الخام من النموذج ---")
    print(response_text)
    print("-------------------------------------------")

except FileNotFoundError:
    print("\n--- فشل! خطأ: 'ollama' is not recognized ---")
    print(" تأكد من أن Ollama مثبت وأنك أعدت تشغيل الكمبيوتر أو الترمينال.")
except subprocess.CalledProcessError as e:
    print(f"\n---  فشل! النموذج أرجع خطأ ---")
    print(e.stderr.decode("utf-8"))
except Exception as e:
    print(f"\n---  فشل! حدث خطأ غير متوقع ---")
    print(e)
