import csv

csv_path = r"C:\animal\runs\shelter_monitoring\train_rtdetr_x_150e_rtx5080\results.csv"
with open(csv_path, "r", encoding="utf-8") as f:
    rows = [{k.strip(): float(v.strip()) for k, v in r.items()} for r in csv.DictReader(f)]

map_key = [k for k in rows[0].keys() if "mAP50(" in k][0]
map95_key = [k for k in rows[0].keys() if "mAP50-95" in k][0]
p_key = [k for k in rows[0].keys() if "precision" in k][0]
r_key = [k for k in rows[0].keys() if "recall" in k][0]

best_map = max(rows, key=lambda x: x[map_key])
best_map95 = max(rows, key=lambda x: x[map95_key])
best_r = max(rows, key=lambda x: x[r_key])
best_p = max(rows, key=lambda x: x[p_key])

print(f"Total Epochs Completed: {len(rows)}")
print(f"Peak mAP50:      {best_map[map_key]*100:.2f}% (Epoch {int(best_map['epoch'])})")
print(f"Peak mAP50-95:   {best_map95[map95_key]*100:.2f}% (Epoch {int(best_map95['epoch'])})")
print(f"Peak Recall:     {best_r[r_key]*100:.2f}% (Epoch {int(best_r['epoch'])})")
print(f"Peak Precision:  {best_p[p_key]*100:.2f}% (Epoch {int(best_p['epoch'])})")

print("\n--- Milestone Progression ---")
for target_ep in [1, 10, 25, 50, 69, 85, 100, 110, len(rows)]:
    match = [r for r in rows if int(r["epoch"]) == target_ep]
    if match:
        m = match[0]
        print(f"Epoch {target_ep:3d} | mAP50: {m[map_key]*100:.2f}% | mAP50-95: {m[map95_key]*100:.2f}% | Recall: {m[r_key]*100:.2f}% | Precision: {m[p_key]*100:.2f}% | Cls Loss: {m['train/cls_loss']:.4f} | Val Cls: {m['val/cls_loss']:.4f}")

print("\n--- Last 5 Epochs ---")
for m in rows[-5:]:
    ep = int(m["epoch"])
    print(f"Epoch {ep:3d} | mAP50: {m[map_key]*100:.2f}% | mAP50-95: {m[map95_key]*100:.2f}% | Recall: {m[r_key]*100:.2f}% | Precision: {m[p_key]*100:.2f}% | Cls: {m['train/cls_loss']:.4f} | Val Cls: {m['val/cls_loss']:.4f}")
