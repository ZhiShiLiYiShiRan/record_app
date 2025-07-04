from flask import Flask, request, render_template, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"  # 用于启用 session

# === MongoDB 设置 ===
client = MongoClient("mongodb+srv://rrriotacc:B0SdDj36GLxIkHuZ@lizard.fyju0pz.mongodb.net/")
db = client["chillmartTemp"]
qa_collection = db["qa_bot"]
done_collection = db["check_done"]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        admin_name = request.form.get("admin")
        if admin_name:
            session["admin"] = admin_name
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def index():
    if "admin" not in session:
        return redirect(url_for("login"))

    skipped_count = qa_collection.count_documents({"skipped": True})
    doc = qa_collection.find_one_and_update(
        {"record_status": False, "lock": {"$ne": True}, "skipped": {"$ne": True}},
        {"$set": {"lock": True}},
        sort=[("_id", 1)]
    )
    return render_template("index.html", doc=doc, skipped_count=skipped_count, admin=session["admin"])

@app.route("/submit", methods=["POST"])
def submit():
    if "admin" not in session:
        return redirect(url_for("login"))

    doc_id = request.form["doc_id"]
    base_title = request.form["title"]
    new_description = request.form["description"]
    admin_user = session["admin"]

    doc = qa_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc or doc.get("lock") != True or doc.get("record_status") != False:
        return redirect("/")

    label = doc.get("label", "")
    number = doc.get("number", "")
    title = f"{base_title} {label} {number}".strip()

    done_doc = {
        "_id": doc["_id"],
        "Label": label,
        "Number": number,
        "Title": title,
        "Note": doc.get("description", ""),
        "Description": new_description,
        "Product_image": doc.get("url", ""),
        "Image_count": doc.get("image_count", 0),
        "Bach_code": doc.get("Bach Code", ""),
        "QA": doc.get("user", ""),
        "QA_time": doc.get("timestamp", ""),
        "admin": admin_user,
        "admin_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "record_status": True,
        "jump_url": doc.get("jump_url", "")
    }

    done_collection.insert_one(done_doc)
    qa_collection.delete_one({"_id": ObjectId(doc_id)})

    return redirect("/")

@app.route("/skip", methods=["POST"])
def skip():
    if "admin" not in session:
        return redirect(url_for("login"))

    doc_id = request.form["doc_id"]
    qa_collection.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"lock": False, "skipped": True}}
    )
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)