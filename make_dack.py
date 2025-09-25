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

deck_total = 40
leader_card_weight = 0.7

# レアリティごとの最大枚数（ここで制限可能）
rarity_max_counts = {
    "bronze": 20,
    "silver": 10,
    "gold": 6,
    "legend": 4
}

# ===== カード読み込み =====
def load_all_cards():
    all_cards = []
    for file in card_list:
        file_path = os.path.join("./card_list", file)
        if os.path.exists(file_path):
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                all_cards.append((file, data))
        else:
            print(f"⚠ ファイルが見つかりません: {file_path}")
    return all_cards

# ===== デッキ生成 =====
def generate_deck(seed_word, all_cards, deck_total=40):
    seed = int(hashlib.sha256(seed_word.encode()).hexdigest(), 16)
    random.seed(seed)
    leader = random.choice(leaders)

    # 使用可能カード
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

    deck = []
    total_cards = 0
    rarity_counts = {k: 0 for k in rarity_max_counts.keys()}

    while total_cards < deck_total and filtered_cards:
        # 選択可能なカードをレアリティ上限に従って絞る
        available_cards = [c for c in filtered_cards if rarity_counts[c["rarity"]] < rarity_max_counts[c["rarity"]]]
        if not available_cards:
            break
        # 重み付け選択
        card = random.choices(
            available_cards,
            weights=[leader_card_weight if c["leader"] == leader else 1 for c in available_cards],
            k=1
        )[0]
        remaining_deck = deck_total - total_cards
        remaining_rarity = rarity_max_counts[card["rarity"]] - rarity_counts[card["rarity"]]
        # 枚数を1～3でランダム、残り枚数・レアリティ制限に合わせる
        count = min(random.randint(1,3), remaining_deck, remaining_rarity)
        deck.append({**card, "count": count})
        total_cards += count
        rarity_counts[card["rarity"]] += count
        filtered_cards.remove(card)

    # ソート
    deck.sort(key=lambda x: (
        int(x["cost"]),
        0 if x["leader"] == "ニュートラル" else 1,
        {"F":0, "S":1, "A":2}.get(x["type"],3),
        card_list.index(x["file"]) if x["file"] in card_list else 9999
    ))

    return leader, deck

# ===== デッキ出力 =====
def print_deck(leader, deck):
    print(leader)
    for card in deck:
        print(f'{card["cost"]}：{card["name"]}：{card["count"]}')

# ===== メイン =====
if __name__ == "__main__":
    all_cards = load_all_cards()
    seed_word = input("適当な単語を入力してください：").strip()
    leader, deck = generate_deck(seed_word, all_cards, deck_total)
    print_deck(leader, deck)
