import sys
import io
import json
import pymysql
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# 2. OpenAI API 설정 (본인의 API KEY 입력 필수)
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

# 4. GPT에게 태그 분석 요청
def ask_gpt_for_tags(food_name):
    prompt = f"""
    '{food_name}'이라는 음식에 대한 정보를 분석해줘.
    다음 5가지 항목에 대해 가장 적절한 단어를 하나씩만 선택해서 JSON 형식으로 답해줘.
    
    1. country: (한식, 중식, 일식, 양식, 아시안) 중 1
    2. taste: (자극적인맛, 담백한맛) 중 1
    3. main_ingredient: (육고기, 채소, 해산물, 빵, 밥, 면, 물고기) 중 1
    4. temperature: (따뜻한것, 차가운것) 중 1
    5. cooking_type: (구운것, 볶은것, 국물, 찐것, 날것) 중 1
    
    응답 예시:
    {{"country": "한식", "taste": "자극적인맛", "main_ingredient": "육고기", "temperature": "따뜻한것", "cooking_type": "볶은것"}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception:
        return {"country": "한식", "taste": "담백한맛", "main_ingredient": "밥", "temperature": "따뜻한것", "cooking_type": "볶은것"}

# 5. DB에서 음식 정보 가져오기 (없으면 이미지 없이 저장)
def get_food_tags(food_name, conn):
    with conn.cursor() as cursor:
        sql = "SELECT * FROM foods WHERE name = %s"
        cursor.execute(sql, (food_name,))
        result = cursor.fetchone()

        if result:
            return f"{result['country']} {result['taste']} {result['main_ingredient']} {result['temperature']} {result['cooking_type']}"

        else:
            ai_data = ask_gpt_for_tags(food_name)
            insert_sql = """
                         INSERT INTO foods (name, image_url, country, taste, main_ingredient, temperature, cooking_type)
                         VALUES (%s, %s, %s, %s, %s, %s, %s) \
                         """
            # 이미지를 생성하지 않고 NULL(None)로 저장
            image_url = None

            cursor.execute(insert_sql, (
                food_name, image_url,
                ai_data['country'], ai_data['taste'], ai_data['main_ingredient'],
                ai_data['temperature'], ai_data['cooking_type']
            ))
            conn.commit()
            return f"{ai_data['country']} {ai_data['taste']} {ai_data['main_ingredient']} {ai_data['temperature']} {ai_data['cooking_type']}"

# --- 메인 로직 ---
if len(sys.argv) < 2:
    print("비빔밥|데이터가 전달되지 않았습니다.")
    sys.exit()

raw_history = sys.argv[1].replace("|", ",")
user_selected_names = [name.strip() for name in raw_history.split(",") if name.strip()]

connection = get_db_connection()

try:
    all_foods = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, country, taste, main_ingredient, temperature, cooking_type FROM foods")
        rows = cursor.fetchall()
        for row in rows:
            tag_str = f"{row['country']} {row['taste']} {row['main_ingredient']} {row['temperature']} {row['cooking_type']}"
            all_foods.append({"name": row['name'], "tags": tag_str})

    user_tags_list = [get_food_tags(name, connection) for name in user_selected_names]

    if not user_tags_list:
        print("라면|데이터 부족으로 라면을 추천합니다.")
        sys.exit()

    user_profile = " ".join(user_tags_list)
    food_names = [f['name'] for f in all_foods]
    corpus = [f['tags'] for f in all_foods]

    vectorizer = TfidfVectorizer()
    total_corpus = corpus + [user_profile]
    tfidf_matrix = vectorizer.fit_transform(total_corpus)

    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    sim_scores = sorted(list(enumerate(similarity_scores[0])), key=lambda x: x[1], reverse=True)

    # 중복 제외 추천
    recommended_food = next((food_names[idx] for idx, score in sim_scores if food_names[idx] not in user_selected_names), food_names[sim_scores[0][0]])

    print(f"{recommended_food}|GPT가 분석한 당신의 취향을 저격하는 메뉴입니다.")

except Exception as e:
    print(f"비빔밥|오류 발생: {str(e)}")
finally:
    connection.close()