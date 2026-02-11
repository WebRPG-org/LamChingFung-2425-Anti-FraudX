import json
import sys

# 讀取 JSON 文件
with open('data/scraped_alerts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"總案例數: {len(data)}")
print(f"\n案例結構: {list(data[0].keys())}")

# 統計來源
sources = {}
for d in data:
    source = d.get('source', 'Unknown')
    sources[source] = sources.get(source, 0) + 1

print("\n來源分布:")
for k, v in sources.items():
    print(f"  {k}: {v}")

# 顯示前 5 個案例標題
print("\n前 5 個案例:")
for i, d in enumerate(data[:5], 1):
    print(f"{i}. {d['title'][:60]}")
    print(f"   日期: {d['date']}, 來源: {d['source']}")
    print(f"   內容長度: {len(d['content'])} 字")
    print()
