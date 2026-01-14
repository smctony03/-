import sys
import io
import json
import pymysql
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. 시스템 인코딩을 UTF-8로 강제 설정 (한글 깨짐 방지)
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# 2. OpenAI API 설정 (유효한 API 키를 입력하세요)
client = OpenAI(api_key="sk-proj-...")

# 3. MySQL 연결 설정
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Jeyong3002~',
        db='food_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 4. GPT를 이용한 음식 특성 추출 (DB에 없는 새로운 음식일 경우 실행)
def ask_gpt_for_tags(food_name):
    prompt = f"""
    '{food_name}'이라는 음식에 대한 정보를 분석해줘.
    다음 5가지 항목에 대해 가장 적절한 단어를 하나씩만 선택해서 JSON 형식으로 답해줘.
    1. country: (한식, 중식, 일식, 양식, 아시안) 중 1
    2. taste: (자극적인맛, 담백한맛) 중 1
    3. main_ingredient: (육고기, 채소, 해산물, 빵, 밥, 면, 물고기) 중 1
    4. temperature: (따뜻한것, 차가운것) 중 1
    5. cooking_type: (구운것, 볶은것, 국물, 찐것, 날것) 중 1
    응답 예시: {{"country": "한식", "taste": "자극적인맛", "main_ingredient": "육고기", "temperature": "따뜻한것", "cooking_type": "볶은것"}}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[Debug] GPT API Error: {e}")
        return {"country": "한식", "taste": "담백한맛", "main_ingredient": "밥", "temperature": "따뜻한것", "cooking_type": "볶은것"}

# 5. 음식의 태그 문자열 생성 로직
def get_food_tags(food_name, conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM foods WHERE name = %s", (food_name,))
        result = cursor.fetchone()
        if result:
            return f"{result['country']} {result['taste']} {result['main_ingredient']} {result['temperature']} {result['cooking_type']}"
        else:
            # DB에 없으면 GPT로 분석 후 DB에 저장
            ai_data = ask_gpt_for_tags(food_name)
            cursor.execute("INSERT INTO foods (name, country, taste, main_ingredient, temperature, cooking_type) VALUES (%s, %s, %s, %s, %s, %s)",
                           (food_name, ai_data['country'], ai_data['taste'], ai_data['main_ingredient'], ai_data['temperature'], ai_data['cooking_type']))
            conn.commit()
            return f"{ai_data['country']} {ai_data['taste']} {ai_data['main_ingredient']} {ai_data['temperature']} {ai_data['cooking_type']}"

# --- 메인 실행부 ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("입력오류|전달된 음식 데이터가 없습니다.")
        sys.exit()

    # 입력받은 히스토리 정리 (중복 제거 및 공백 제거)
    raw_history = sys.argv[1].replace("|", ",")
    user_selected_names = list(set([name.strip() for name in raw_history.split(",") if name.strip()]))

    connection = get_db_connection()
    try:
        # 1. DB에 있는 모든 음식 데이터 로드
        all_foods = []
        with connection.cursor() as cursor:
            cursor.execute("SELECT name, country, taste, main_ingredient, temperature, cooking_type FROM foods")
            rows = cursor.fetchall()
            for row in rows:
                tag_str = f"{row['country']} {row['taste']} {row['main_ingredient']} {row['temperature']} {row['cooking_type']}"
                all_foods.append({"name": row['name'], "tags": tag_str})

        if not all_foods:
            print("데이터부족|DB에 비교할 음식 데이터가 없습니다.")
            sys.exit()

        # 2. 사용자 취향 프로필 생성 (선택한 모든 음식의 태그 결합)
        user_tags_list = [get_food_tags(name, connection) for name in user_selected_names]
        user_profile = " ".join(user_tags_list)

        # 3. TF-IDF를 이용한 텍스트 유사도(Cosine Similarity) 계산
        food_names = [f['name'] for f in all_foods]
        corpus = [f['tags'] for f in all_foods]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus + [user_profile])

        # 마지막 행(user_profile)과 나머지 행들(DB 음식들) 비교
        similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]

        # 유사도 높은 순으로 인덱스 정렬
        sorted_indices = similarity_scores.argsort()[::-1]

        # 4. 추천 음식 결정 (사용자가 현재 게임에서 고르지 않은 것 중 가장 유사한 것)
        recommended_food = "비빔밥" # 기본값
        for idx in sorted_indices:
            candidate = food_names[idx]
            if candidate not in user_selected_names:
                recommended_food = candidate
                break

        # 5. 최종 결과 출력 (자바가 읽을 수 있도록 | 구분자 사용)
        print(f"{recommended_food}|AI가 분석한 당신의 취향 저격 메뉴입니다.")

    except Exception as e:
        print(f"오류발생|파이썬 코드 에러: {str(e)}")
    finally:
        connection.close()