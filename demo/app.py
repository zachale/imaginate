from flask import Flask, render_template, redirect, make_response, request
from dotenv import load_dotenv
from pymongo import MongoClient
import gridfs
import os
import base64

# Initialize clients
app = Flask(__name__)
load_dotenv()
db = MongoClient(os.getenv("MONGO_TOKEN"))["imaginate"]
fs = gridfs.GridFS(db)

# C - Implemented on /create endpoint
# R - Implemented on /read endpoint
# U - TODO
# D - TODO
# TODO: Limit upload to specific file types

# Allows testing of creation
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def upload():
    file = request.files["file"]
    if file.filename:
        if not next(fs.find({"filename": file.filename}), None):
            print("File not found: adding...")
            fs.put(file.stream.read(), filename=file.filename, type=file.content_type)
        else:
            print("File found: skipping...")
    return redirect("/read/" + file.filename)

@app.route("/read")
def read_all():
    content = ""
    for res in fs.find():
        content += f'<li><a href="/read/{res.filename}">{res.filename}</a></li>\n'
    return f"<ul>\n{content}</ul>"

@app.route("/read/<filename>")
def read(filename):
    res = next(fs.find({"filename": filename}), None)
    if res:
        response = make_response(res.read())
        response.headers.set("Content-Type", res.type)
        response.headers.set("Content-Length", f"{res.length}")
        return response
    return "Not found"


@app.route("/image/verification-portal", methods=["GET"])
def verification_portal():
    obj = list(db['fs.files'].aggregate([{ '$sample': { 'size': 1 } }]))[0] #TODO: MAKE IT BASED ON STATUS
    print(obj)
    if obj:
        grid_out = fs.find_one({"_id":obj['_id']})
        data = grid_out.read()
        base64_data = base64.b64encode(data).decode('ascii');
        return render_template('verification_portal.html', id=obj['_id'], img_found=True, img_src=base64_data, obj_data=obj)
    return render_template('verification_portal.html', img_found=False)

@app.route("/image/update-status", methods=["POST"])
def update_status():
    status = request.form['status']
    if status:
        query_filter = { '_id':request.form['id'] }
        update_operation = { "$set" : { "status" : status } }
        db['fs.files'].find_one_and_update(query_filter, update_operation)
    else:
        return "new status not recieved",400  
    return "status updated",200

@app.route("/image/delete_rejected", methods=["DELETE"])
def delete_rejected():
    filter = {"status":"rejected"}
    results = db["fs.files"].delete_many(filter)
    return results, 200

if __name__ == "__main__":
    app.run()