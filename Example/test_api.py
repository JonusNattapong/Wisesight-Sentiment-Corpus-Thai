import json

with open('เผยภาพเสียหายโรงงานนิวเคลียร์อิหร่านหลังสหรัฐฯ โจมตี ｜ วันใหม่ ไทยพีบีเอส ｜ 23 มิ.ย. 68 [NCikfkG49uY].info.json', encoding='utf-8') as f:
    data = json.load(f)

comments = data.get('comments', [])
for c in comments:
    author = c.get('author')
    text = c.get('text')
    print(f"{author}: {text}")

    replies = c.get('replies', [])
    for reply in replies:
        print(f"    ↳ {reply.get('author')}: {reply.get('text')}")

