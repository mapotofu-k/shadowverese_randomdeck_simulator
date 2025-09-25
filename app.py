import streamlit as st
import os
import json
import random
import hashlib

# === UI: タイトル ===
st.title("シャドバ デッキジェネレーター")

# === 詳細設定 ===
with st.expander("🔧 詳細設定", expanded=False):
    # ニュートラルカード出現率（＝リーダーカード出現重みの逆）
    neutral_rate_percent = st.slider("ニュートラルカード出現率（%）", min_value=0, max_value=100, value=10, step=1)
    neutral_card_weight = neutral_rate_percent / 100

    # レアリティごとの上限枚数
    st.markdown("**各レアリティの上限枚数**")
    rarity_bronze = st.number_input("ブロンズ", min_value=0, value=20, step=1)
    rarity_silver = st.number_input("シルバー", min_value=0, value=10, step=1)
    rarity_gold   = st.number_input("ゴールド", min_value=0, value=6, step=1)
    rarity_legend = st.number_input("レジェンド", min_value=0, value=4, step=1)

    rarity_max_counts = {
        "bronze": rarity_bronze,
        "silver": rarity_silver,
        "gold": rarity_gold,
        "legend": rarity_legend,
    }

    total_allowed_cards = sum(rarity_max_counts.values())
    if total_allowed_cards < 40:
        st.error("※ 各レアリティの合計が40枚未満です。合計で40枚以上になるように設定してください。")

    # 使用カードパックの選択（UI表示名とファイル名の対応）
    pack_name_map = {
        "ベーシック": "basic.json",
        "伝説の幕開け": "legends_rise.json",
        "インフィニティ・エボルヴ": "infinity_evolved.json",
        "絶傑の継承者": "heirs_of_the_omen.json",
    }

    selected_packs_ui = st.multiselect("使用カードパックを選択", options=list(pack_name_map.keys()), default=list(pack_name_map.keys()))
    card_list = [pack_name_map[name] for name in selected_packs_ui]

# === 定数 ===
leaders = ["エルフ", "ロイヤル", "ウィッチ", "ドラゴン", "ナイトメア", "ビショップ", "ネメシス"]
deck_total = 40

# === カード読み込み ===
@st.cache_data
def load_all_cards(card_list):
    all_cards = []
    for file in card_list:
        file_path = os.path.join("card_list", file)
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                all_cards.append((file, data))
    return all_cards

# === カード読み込み ===
@st.cache_data
def load_all_cards(card_list):
    all_cards = []
    for file in card_list:
        file_path = os.path.join("card_list", file)
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                all_cards.append((file, data))
    return all_cards

# === デッキ生成 ===
def generate_deck(seed_word, all_cards):
    seed = int(hashlib.sha256(seed_word.encode()).hexdigest(), 16)
    random.seed(seed)
    leader = random.choice(leaders)

    leader_cards = []
    neutral_cards = []

    for file_name, data in all_cards:
        if leader in data:
            for rarity, cards in data[leader].items():
                for card in cards:
                    leader_cards.append({
                        "file": file_name,
                        "leader": leader,
                        "rarity": rarity,
                        "cost": card["cost"],
                        "name": card["name"],
                        "type": card.get("tyoe", "F")  # typo対応
                    })

        if "ニュートラル" in data:
            for rarity, cards in data["ニュートラル"].items():
                for card in cards:
                    neutral_cards.append({
                        "file": file_name,
                        "leader": "ニュートラル",
                        "rarity": rarity,
                        "cost": card["cost"],
                        "name": card["name"],
                        "type": card.get("tyoe", "F")  # typo対応
                    })

    deck = []
    total_cards = 0
    rarity_counts = {k: 0 for k in rarity_max_counts}

    while total_cards < deck_total:
        source_type = random.choices(
            ["leader", "neutral"],
            weights=[1 - neutral_card_weight, neutral_card_weight],
            k=1
        )[0]

        source_cards = leader_cards if source_type == "leader" else neutral_cards
        available = [c for c in source_cards if rarity_counts[c["rarity"]] < rarity_max_counts[c["rarity"]]]

        if not available:
            # もう一方から取れるならそちらに切り替える
            source_type = "neutral" if source_type == "leader" else "leader"
            source_cards = leader_cards if source_type == "leader" else neutral_cards
            available = [c for c in source_cards if rarity_counts[c["rarity"]] < rarity_max_counts[c["rarity"]]]

        if not available:
            break  # 両方とも空なら終了

        card = random.choice(available)
        remaining = min(deck_total - total_cards, rarity_max_counts[card["rarity"]] - rarity_counts[card["rarity"]])
        count = min(random.randint(1, 3), remaining)

        deck.append({**card, "count": count})
        total_cards += count
        rarity_counts[card["rarity"]] += count

        # 抽選元から削除（重複防止）
        source_cards.remove(card)

    deck.sort(key=lambda x: (
        int(x["cost"]),
        0 if x["leader"] == "ニュートラル" else 1,
        {"F": 0, "S": 1, "A": 2}.get(x["type"], 3),
        card_list.index(x["file"]) if x["file"] in card_list else 9999
    ))

    return leader, deck


# === デッキ生成 UI ===
seed_word = st.text_input("デッキを生成するためのキーワードを入力", "example")

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("デッキを作成"):
        if total_allowed_cards < 40:
            st.warning("各レアリティの枚数上限の合計が40未満です。")
        else:
            all_cards = load_all_cards(card_list)
            leader, deck = generate_deck(seed_word, all_cards)

            st.subheader(f"リーダー：{leader}")
            lines = ["コスト：カード名（枚数）"]
            for card in deck:
                line = f'{card["cost"]}：{card["name"]}（{card["count"]}）'
                lines.append(line)
            st.code("\n".join(lines), language="")

with col2:
    st.markdown("")

