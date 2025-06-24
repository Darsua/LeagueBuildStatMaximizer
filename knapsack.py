def knapsack(weights, values, capacity, max_items):
    n = len(weights)
    dp = [[[0 for _ in range(max_items + 1)] for _ in range(capacity + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        print(f"Processing item {i}/{n} ({(i/n)*100:.1f}%)")
        for w in range(capacity + 1):
            for k in range(1, max_items + 1):
                if weights[i - 1] <= w:
                    dp[i][w][k] = max(
                        dp[i - 1][w][k],
                        dp[i - 1][w - weights[i - 1]][k - 1] + values[i - 1]
                    )
                else:
                    dp[i][w][k] = dp[i - 1][w][k]

    # Backtrack to find which items were taken
    res = []
    w, k = capacity, max_items
    for i in range(n, 0, -1):
        if k > 0 and dp[i][w][k] != dp[i - 1][w][k]:
            res.append(i - 1)
            w -= weights[i - 1]
            k -= 1

    res.reverse()  # To print in input order
    return dp[n][capacity][max_items], res

def unbounded_knapsack(weights, values, capacity, max_items):
    n = len(weights)
    dp = [[0 for _ in range(max_items + 1)] for _ in range(capacity + 1)]
    item_choice = [[[] for _ in range(max_items + 1)] for _ in range(capacity + 1)]

    for w in range(capacity + 1):
        print(f"Progress: {w}/{capacity} ({(w / capacity) * 100:.1f}%)")
        for k in range(1, max_items + 1):
            for i in range(n):
                if weights[i] <= w:
                    if dp[w - weights[i]][k - 1] + values[i] > dp[w][k]:
                        dp[w][k] = dp[w - weights[i]][k - 1] + values[i]
                        item_choice[w][k] = item_choice[w - weights[i]][k - 1] + [i]
    # noinspection DuplicatedCode
    print(f"Progress: {capacity}/{capacity} (100.0%)")

    # Find the best result
    max_value = 0
    best_items = []
    for k in range(1, max_items + 1):
        if dp[capacity][k] > max_value:
            max_value = dp[capacity][k]
            best_items = item_choice[capacity][k]
    return max_value, best_items

def unbounded_conditional_knapsack(weights, values, capacity, max_items, forbidden_pairs=None):
    n = len(weights)
    dp = [[0 for _ in range(max_items + 1)] for _ in range(capacity + 1)]
    item_choice = [[[] for _ in range(max_items + 1)] for _ in range(capacity + 1)]
    forbidden_pairs = set(forbidden_pairs or [])

    for w in range(capacity + 1):
        print(f"Progress: {w}/{capacity} ({(w / capacity) * 100:.1f}%)", end='\r', flush=True)
        for k in range(1, max_items + 1):
            for i in range(n):
                if weights[i] <= w:
                    prev_items = item_choice[w - weights[i]][k - 1]
                    # Check for forbidden pairs
                    if any((i, j) in forbidden_pairs or (j, i) in forbidden_pairs for j in prev_items):
                        continue
                    if dp[w - weights[i]][k - 1] + values[i] > dp[w][k]:
                        dp[w][k] = dp[w - weights[i]][k - 1] + values[i]
                        item_choice[w][k] = prev_items + [i]
    # noinspection DuplicatedCode
    print(f"Progress: {capacity}/{capacity} (100.0%)")

    # Find the best result
    max_value = 0
    best_items = []
    for k in range(1, max_items + 1):
        if dp[capacity][k] > max_value:
            max_value = dp[capacity][k]
            best_items = item_choice[capacity][k]
    return max_value, best_items

def forbidden_pair_generator(data):
    from itertools import combinations

    forbidden_pairs = set()
    # Only consider items with real limits (not [None])
    itemlimited = data[data['itemlimit'].apply(lambda x: x != [None])]

    # Map each limit to the indices of items that have it
    limit_to_indices = {}
    for idx, limits in itemlimited['itemlimit'].items():
        for limit in limits:
            limit_to_indices.setdefault(limit, []).append(idx)

    # For each limit, forbid all pairs of items sharing that limit
    for indices in limit_to_indices.values():
        for i in indices:
            forbidden_pairs.add((i, i))  # Add self-pair
        for i, j in combinations(indices, 2):
            forbidden_pairs.add((i, j))
            forbidden_pairs.add((j, i))  # If order matters

    # Add self-pairs for legendary items
    legendary_items = data[data['type'] == 'Legendary'].index
    for i in legendary_items:
        forbidden_pairs.add((i, i))

    # Add pairs of boots items
    boots_items = data[data['type'] == 'Boots'].index
    for i, j in combinations(boots_items, 2):
        forbidden_pairs.add((i, j))
        forbidden_pairs.add((j, i))
    for i in boots_items:
        forbidden_pairs.add((i, i))

    return forbidden_pairs

def solve(stat: str, gold: int):
    import pandas as pd
    import ast

    data = pd.read_csv('itemData.csv')
    data['itemlimit'] = data['itemlimit'].apply(ast.literal_eval)
    print(f"\nLoaded {len(data)} items.")

    # Filter out items with 0 value for the chosen stat
    data = data[data[stat] != 0]
    data = data.reset_index(drop=True)
    print(f"Filtered to {len(data)} items with nonzero {stat.upper()}.")

    weights = data['cost'].tolist()
    values = data[stat].tolist()
    capacity = gold
    max_items = 6
    forbidden_pairs = forbidden_pair_generator(data)

    print("\nStarting knapsack problem...")
    max_value, items = unbounded_conditional_knapsack(weights, values, capacity, max_items, forbidden_pairs)
    print("Knapsack problem completed.\n")

    print(f"Maximum {stat.upper()} in knapsack: {max_value}")
    print("Items included:")
    for i in items:
        item_name = data.iloc[i]['name']
        item_cost = data.iloc[i]['cost']
        print(f"- {item_name} (Cost: {item_cost}G, {stat.upper()}: {data.iloc[i][stat]})")
    print(f"Total cost: {sum(weights[i] for i in items)}G / {capacity}G")

def main():
    stats = {
        "ah": "Ability Haste",
        "hp": "Health",
        "mr": "Magic Resist",
        "armor": "Armor",
        "ap": "Ability Power",
        "ms": "Movement Speed",
        "mana": "Mana",
        "hsp": "Heal and Shield Power",
        "mp5": "Mana Regeneration",
        "msflat": "Flat Movement Speed",
        "crit": "Critical Strike Chance",
        "ad": "Attack Damage",
        "lethality": "Lethality",
        "as": "Attack Speed",
        "lifesteal": "Lifesteal",
        "mpen": "Magic Penetration",
        "hp5": "Health Regeneration",
        "gp10": "Gold per 10 seconds",
        "tenacity": "Tenacity",
        "hp5flat": "Flat Health Regeneration",
        "omnivamp": "Omnivamp",
        "critdamage": "Critical Strike Damage",
        "armpen": "Armor Penetration",
        "mpenflat": "Flat Magic Penetration"
    }

    import os
    os.system('cls' if os.name == 'nt' else 'clear')

    print(r"""                       _           _ _                     _           _              
  /\/\   __ _ _ __ ___| |__   __ _| | |   /\/\   __ ___  _(_)_ __ ___ (_)_______ _ __ 
 /    \ / _` | '__/ __| '_ \ / _` | | |  /    \ / _` \ \/ / | '_ ` _ \| |_  / _ \ '__|
/ /\/\ \ (_| | |  \__ \ | | | (_| | | | / /\/\ \ (_| |>  <| | | | | | | |/ /  __/ |   
\/    \/\__,_|_|  |___/_| |_|\__,_|_|_| \/    \/\__,_/_/\_\_|_| |_| |_|_/___\___|_|                                                
    """)
    print("Your very own League of Legends item stat build maximizer!")
    print("\nAvailable stats:")
    for key, value in stats.items():
        print(f"{key.upper()}: {value}")
    print("\nThis program will help you maximize a specific stat in League of Legends items within a given gold budget.")

    stat = input("Enter the stat you want to maximize (e.g., 'AD', 'AP', etc.): ").strip().lower()
    if stat not in stats:
        print(f"\nInvalid stat '{stat}'. Please run the program again and choose a valid stat.\n")
        return

    gold = int(input("Enter the amount of gold available: "))

    solve(stat, gold)
    print("\nGood luck trying out your new build! :3\n")

if __name__ == "__main__":
    main()
