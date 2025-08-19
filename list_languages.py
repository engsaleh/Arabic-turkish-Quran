import requests

API_URL = "https://api.quran.com/api/v4/resources/translations"

def get_unique_languages():
    """
    يجلب جميع الترجمات المتاحة ويستخلص منها قائمة فريدة بأسماء اللغات.
    """
    try:
        print("جاري الاتصال بالواجهة البرمجية لجلب بيانات الترجمات...")
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()  # التأكد من أن الطلب ناجح

        all_translations = response.json()['translations']

        # استخدام "set" لضمان عدم وجود تكرار للغات
        language_set = set()

        for translation in all_translations:
            # نتأكد من وجود المفتاح قبل إضافته لتجنب الأخطاء
            if 'language_name' in translation:
                language_set.add(translation['language_name'])

        # تحويل المجموعة إلى قائمة مرتبة لسهولة القراءة
        sorted_languages = sorted(list(language_set))
        return sorted_languages, None

    except requests.exceptions.RequestException as e:
        return None, f"حدث خطأ في الشبكة: {e}"
    except KeyError:
        return None, "حدث خطأ: هيكل البيانات المستلمة من الـ API غير متوقع."

if __name__ == "__main__":
    available_languages, error = get_unique_languages()

    if error:
        print(f"\nخطأ: {error}")
    elif available_languages:
        print("\n--- قائمة اللغات المتاحة للترجمة في Quran.com API ---")
        for lang in available_languages:
            print(f"- {lang.capitalize()}") # .capitalize() لجعل الحرف الأول كبيرًا
        print("-" * 50)
        print(f"إجمالي عدد اللغات الفريدة: {len(available_languages)}")
    else:
        print("لم يتم العثور على لغات.")
