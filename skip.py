from pymongo import MongoClient

# ===== MongoDB 连接设置 =====
client = MongoClient("mongodb+srv://rrriotacc:B0SdDj36GLxIkHuZ@lizard.fyju0pz.mongodb.net/")
db = client["chillmartTemp"]
qa_collection = db["qa_bot"]

# ===== 要更新的编号列表 =====
numbers_to_update = [
    "18", "36", "51", "3", "30", "21", "6", "53", "31", "49",
    "39", "9", "2", "56", "4", "57", "37", "13", "8",
    "838", "840", "841", "842", "844", "846"
]

# ===== 执行更新操作 =====
result = qa_collection.update_many(
    {
        "number": {"$in": numbers_to_update}
    },
    {
        "$set": {
            "record_status": False,
            "skipped": True,
            "lock": False
        }
    }
)

print(f"✅ 已更新 {result.modified_count} 条记录。")
