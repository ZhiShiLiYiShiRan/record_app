from flask import Flask, request, render_template, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

app = Flask(__name__)
# 从环境变量读取 Flask 会话密钥，未设置则抛出错误
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable not set")
app.secret_key = secret_key

# === MongoDB 设置 ===
# 连接字符串从环境变量读取，避免在代码中暴露凭据
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError("MONGO_URI environment variable not set")
client = MongoClient(mongo_uri)
db = client["chillmartTemp"]
qa_collection = db["qa_bot"]
done_collection = db["check_done"]
problem_collection = db["problem"]

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

    source = request.args.get("source", "qa")
    collection = qa_collection if source == "qa" else problem_collection

    skipped_count = collection.count_documents({"skipped": True})
    doc = collection.find_one_and_update(
        {"record_status": False, "lock": {"$ne": True}, "skipped": {"$ne": True}},
        {"$set": {"lock": True}},
        sort=[("_id", 1)]
    )

    return render_template(
        "index.html",
        doc=doc,
        skipped_count=skipped_count,
        admin=session["admin"],
        source=source,
    )

@app.route("/submit", methods=["POST"])
def submit():
    if "admin" not in session:
        return redirect(url_for("login"))

    doc_id = request.form["doc_id"]
    source = request.form.get("source", "qa")
    base_title = request.form["title"]
    new_description = request.form["description"]
    admin_user = session["admin"]

    collection = qa_collection if source == "qa" else problem_collection

    doc = collection.find_one({"_id": ObjectId(doc_id)})
    if not doc or doc.get("lock") != True or doc.get("record_status") != False:
        return redirect(url_for("index", source=source))

    label = doc.get("label", "")
    number = doc.get("number", "")
    title = f"{base_title} {label} {number}".strip()

    done_doc = {
        "_id": doc["_id"],
        "Label": label,
        "Number": number,
        "Title": title,
        "Note": doc.get("note", ""),
        "Description": new_description,
        "Product_image": doc.get("url", ""),
        "Image_count": doc.get("image_count", 0),
        "Location": doc.get("location", ""),
        "Bach_code": doc.get("Bach Code", ""),
        "QA": doc.get("user", ""),
        "QA_time": doc.get("timestamp", ""),
        "admin": admin_user,
        "admin_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "record_status": True,
        "jump_url": doc.get("jump_url", "")
    }

    done_collection.insert_one(done_doc)
    collection.delete_one({"_id": ObjectId(doc_id)})

    return redirect(url_for("index", source=source))

@app.route("/skip", methods=["POST"])
def skip():
    if "admin" not in session:
        return redirect(url_for("login"))

    doc_id = request.form["doc_id"]
    source = request.form.get("source", "qa")

    if source == "qa":
        doc = qa_collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            problem_collection.insert_one(doc)
            qa_collection.delete_one({"_id": ObjectId(doc_id)})
    else:
        problem_collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"lock": False, "skipped": True}},
        )

    return redirect(url_for("index", source=source))


@app.route("/records", methods=["GET"])
def records():
    if "admin" not in session:
        return redirect(url_for("login"))

    q = request.args.get("q", "").strip()
    query = {}
    if q:
        query = {
            "$or": [
                {"Title": {"$regex": q, "$options": "i"}},
                {"Number": {"$regex": q, "$options": "i"}},
            ]
        }

    docs = list(done_collection.find(query).sort("Number", 1))
    return render_template(
        "records.html",
        docs=docs,
        q=q,
        admin=session["admin"],
    )


@app.route("/edit/<doc_id>", methods=["GET", "POST"])
def edit(doc_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    doc = done_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        return redirect(url_for("records"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        done_collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"Title": title, "Description": description}},
        )
        return redirect(url_for("records"))

    return render_template("edit.html", doc=doc, admin=session["admin"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
