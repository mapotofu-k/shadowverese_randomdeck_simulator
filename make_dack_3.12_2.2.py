import os
import json
import random
import hashlib

# ===== 設定 =====
card_list = [
    "basic.json",
    "legends_rise.json",
    "infinity_evolved.json",
    "heirs_of_the_omen.json"
]

leaders = ["エルフ", "ロイヤル", "ウィッチ", "ドラゴン", "ナイトメア", "ビショップ", "ネメシス"]

rarity_counts = {
    "bronze": 5,
    "silver": 4,
    "gold": 3,
    "legend": 2
}

# リーダーカード優先度（0〜1）
leader_card_weight = 0.9

# ===== カード読み込み =====
def load_all_cards():
    all_cards = []
    for file in card_list:
        file = os.path.join("./card_list",file)
        if os.path.exists(file):
            with open(file, encoding='utf-8') as f:
                data = json.load(f)
                all_cards.append((file, data))
        else:
            print(f"⚠ ファイルが見つかりません: {file}")
    return all_cards

# ===== デッキ生成 =====
def generate_deck(seed_word, all_cards):
    # 乱数固定
    seed = int(hashlib.sha256(seed_word.encode()).hexdigest(), 16)
    random.seed(seed)

    # リーダー選択
    leader = random.choice(leaders)

    # 使用可能カードを抽出
    filtered_cards = []
    for file_name, data in all_cards:
        for cls in [leader, "ニュートラル"]:
            if cls not in data:
                continue
            for rarity, card_list_data in data[cls].items():
                for card in card_list_data:
                    filtered_cards.append({
                        "file": file_name,
                        "leader": cls,
                        "rarity": rarity,
                        "cost": card["cost"],
                        "name": card["name"],
                        "type": card.get("type", "F")
                    })

    # レアリティごとにデッキ構築
    deck = []
    for rarity, count in rarity_counts.items():
        leader_cards = [c for c in filtered_cards if c["rarity"] == rarity and c["leader"] == leader]
        neutral_cards = [c for c in filtered_cards if c["rarity"] == rarity and c["leader"] == "ニュートラル"]
        selected = []
        while len(selected) < count:
            if leader_cards and (not neutral_cards or random.random() < leader_card_weight):
                selected.append(leader_cards.pop(random.randrange(len(leader_cards))))
            elif neutral_cards:
                selected.append(neutral_cards.pop(random.randrange(len(neutral_cards))))
            else:
                break
        deck.extend(selected)

    # ソート：コスト → ニュートラル優先 → type F<S<A → ファイル順
    deck.sort(key=lambda x: (
        int(x["cost"]),
        0 if x["leader"] == "ニュートラル" else 1,
        {"F": 0, "S": 1, "A": 2}.get(x["type"], 3),
        card_list.index(x["file"]) if x["file"] in card_list else 9999
    ))

    return leader, deck

# ===== デッキ出力 =====
def print_deck(leader, deck):
    print(leader)
    for card in deck:
        count = 3 if card["rarity"] != "legend" else 2
        print(f'{card["cost"]}：{card["name"]}：{count}')

# ===== メイン =====
if __name__ == "__main__":
    all_cards = load_all_cards()
    seed_word = input("適当な単語を入力してください：").strip()
    leader, deck = generate_deck(seed_word, all_cards)
    print_deck(leader, deck)



