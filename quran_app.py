from flask import Flask, render_template
import requests
import subprocess
import json
import time
import re

app = Flask(__name__)

API_BASE_URL = "https://api.quran.com/api/v4"
TURKISH_TRANSLATION_IDS = [52, 112, 124, 210, 77]

def clean_html_tags(text):
    clean_text = re.sub(r'<sup.*?</sup>', '', text)
    return clean_text.strip()

def get_all_surahs():
    url = f"{API_BASE_URL}/chapters"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()["chapters"], None
    except requests.exceptions.RequestException as e:
        return [], f"خطأ في الشبكة أثناء جلب قائمة السور: {e}"

def call_ai_model_batch(verses_data):
    """
    تستدعي نموذج Ollama المحلي مرة واحدة لمجموعة من الآيات.
    """
    prompt_header = (
        "You are an expert in Quranic Arabic and Turkish linguistics. "
        "Your task is to generate an improved, clear, and accurate hybrid Turkish translation for each Quranic verse provided. "
        "Analyze the original Arabic text and the five different Turkish translations, then synthesize a final, high-quality translation. "
        "Respond ONLY with a valid JSON array where each object contains 'verse_number' and 'hybrid_translation'.\n\n"
        "Here is the data:\n"
    )
    prompt_data = json.dumps(verses_data, indent=2, ensure_ascii=False)
    full_prompt = prompt_header + prompt_data

    try:
        print(f"🚀 يتم إرسال الطلب إلى نموذج Ollama المحلي (llama3) لـ {len(verses_data)} آية...")
        start_time = time.time()
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=full_prompt.encode("utf-8"),
            capture_output=True,
            check=True,
            timeout=600 # مهلة 10 دقائق للسماح للنموذج بالعمل
        )
        end_time = time.time()
        print(f"✅ استجاب نموذج Ollama خلال {end_time - start_time:.2f} ثانية.")

        response_text = result.stdout.decode("utf-8").strip()
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1

        if json_start == -1 or json_end == 0:
            print("❌ خطأ: لم يتم العثور على مصفوفة JSON في استجابة النموذج.")
            print(f"--- الاستجابة الخام ---\n{response_text}\n--------------------")
            return None

        clean_json_str = response_text[json_start:json_end]
        ai_translations = json.loads(clean_json_str)
        return {item['verse_number']: item['hybrid_translation'] for item in ai_translations}

    except subprocess.TimeoutExpired:
        print(f" خطأ: استغرق النموذج وقتًا أطول من المهلة المحددة (600 ثانية).")
        return None
    except FileNotFoundError:
        print(" خطأ: الأمر 'ollama' غير موجود. تأكد من تثبيته بشكل صحيح وإضافته إلى PATH.")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f" خطأ في تحليل استجابة النموذج: {e}")
        print(f"--- الاستجابة الخام ---\n{response_text}\n--------------------")
        return None
    except Exception as e:
        print(f" حدث خطأ غير متوقع أثناء استدعاء Ollama: {e}")
        return None

def get_full_surah_data(chapter_number):
    translations_str = ",".join(map(str, TURKISH_TRANSLATION_IDS))
    url = (
        f"{API_BASE_URL}/verses/by_chapter/{chapter_number}"
        f"?language=ar&words=false&translations={translations_str}&fields=text_uthmani"
    )
    try:
        info_res = requests.get(f"{API_BASE_URL}/chapters/{chapter_number}", timeout=10)
        info_res.raise_for_status()
        surah_info = info_res.json()["chapter"]
        verses_res = requests.get(url, timeout=30)
        verses_res.raise_for_status()
        verses = verses_res.json()["verses"]
        combined_data, verses_for_ai = [], []
        for verse in verses:
            verse_num, arabic_text = verse["verse_number"], verse["text_uthmani"]
            translations_map = {t['resource_id']: t['text'] for t in verse['translations']}
            turkish_versions = [clean_html_tags(translations_map.get(tid, "غير متوفرة")) for tid in TURKISH_TRANSLATION_IDS]
            verses_for_ai.append({"verse_number": verse_num, "arabic_text": arabic_text, "turkish_translations": turkish_versions})
            combined_data.append({"number": verse_num, "arabic_text": arabic_text, "turkish_versions": turkish_versions, "hybrid": "جاري التوليد..."})

        hybrid_translations_map = call_ai_model_batch(verses_for_ai)
        if hybrid_translations_map:
            for item in combined_data:
                item["hybrid"] = hybrid_translations_map.get(item["number"], " فشل التوليد")
        else:
            for item in combined_data:
                item["hybrid"] = " حدث خطأ أثناء الاتصال بالذكاء الاصطناعي"

        return surah_info, combined_data, None
    except Exception as e:
        return None, None, f"حدث خطأ أثناء جلب البيانات: {e}"

@app.route("/")
def index():
    surahs, error = get_all_surahs()
    return render_template("index.html", surahs=surahs, error=error)

@app.route("/surah/<int:chapter_id>")
def surah_view(chapter_id):
    # ابدأ بسور قصيرة للاختبار (مثل 112, 113, 114)
    surah_info, items, error = get_full_surah_data(chapter_id)
    return render_template("surah.html", surah_info=surah_info, items=items, error=error)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
