from flask import Flask, render_template, request, redirect, url_for, flash, Response
import json
from datetime import datetime
import uuid
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "demo_secret_key"

# --------------------------
# Load billers
# --------------------------
with open("billers.json", "r") as f:
    BILLERS = json.load(f)

# --------------------------
# Demo In-Memory Data
# --------------------------
bills = [
    {
        "id": "TXN1001",
        "biller": "Bangalore Electricity Supply Company Ltd (BESCOM) - Karnataka (LT)",
        "consumer_number": "CN12345",
        "branch": "Bangalore",
        "amount": "2500",
        "due_date": "2025-11-05",
        "status": "Pending",
        "stage": "Maker",
        "created_at": "2025-10-25 10:15:00"
    },
    {
        "id": "TXN1002",
        "biller": "Maharashtra State Electricity Distribution Company Ltd (MSEDCL) - Maharashtra (HT)",
        "consumer_number": "CN98541",
        "branch": "Mumbai",
        "amount": "8700",
        "due_date": "2025-11-10",
        "status": "Pending",
        "stage": "Checker",
        "created_at": "2025-10-24 14:22:00"
    },
    {
        "id": "TXN1003",
        "biller": "BSES Rajdhani Power Ltd (BRPL) - Delhi (LT)",
        "consumer_number": "CN45678",
        "branch": "Delhi",
        "amount": "4600",
        "due_date": "2025-11-03",
        "status": "Pending",
        "stage": "Approver",
        "created_at": "2025-10-23 12:05:00"
    }
]

audit_log = [
    {"id": "A001", "action": "System initialized with sample data", "role": "System", "timestamp": "2025-10-25 09:00:00"}
]

# --------------------------
# Helpers
# --------------------------
def add_audit(action, user_role):
    audit_log.append({
        "id": str(uuid.uuid4())[:8],
        "action": action,
        "role": user_role,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        role = "Maker"
        add_audit(f"{username} logged in as Maker", role)
        return redirect(url_for("dashboard", role=role))
    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    role = request.args.get("role", "Maker")

    if request.method == "POST":
        branch = request.form["branch"]
        biller = request.form["biller"]
        consumer_number = request.form["consumer_number"]
        amount = request.form["amount"]
        due_date = request.form["due_date"]
        bill = {
            "id": str(uuid.uuid4())[:8],
            "branch": branch,
            "biller": biller,
            "consumer_number": consumer_number,
            "amount": amount,
            "due_date": due_date,
            "status": "Pending",
            "stage": "Maker",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        bills.append(bill)
        add_audit(f"Added bill for {biller}", role)
        flash("Bill added successfully!", "success")
        return redirect(url_for("dashboard", role=role))

    if role == "Maker":
        filtered = [b for b in bills if b["stage"] == "Maker"]
    elif role == "Checker":
        filtered = [b for b in bills if b["stage"] == "Checker"]
    elif role == "Approver":
        filtered = [b for b in bills if b["stage"] == "Approver"]
    else:
        filtered = bills

    branch_filter = request.args.get("branch_filter")
    if branch_filter:
        filtered = [b for b in filtered if b.get("branch") == branch_filter]

    branch_summary = {}
    for b in bills:
        branch = b.get("branch", "Unknown")
        branch_summary[branch] = branch_summary.get(branch, 0) + float(b["amount"])
    branch_summary = [{"branch": k, "total": v} for k, v in branch_summary.items()]

    return render_template("dashboard.html", bills=filtered, role=role, billers=BILLERS, branch_summary=branch_summary)


@app.route("/update_status/<bill_id>/<new_stage>")
def update_status(bill_id, new_stage):
    for bill in bills:
        if bill["id"] == bill_id:
            bill["stage"] = new_stage
            add_audit(f"Bill {bill_id} moved to {new_stage}", new_stage)
            flash(f"Bill moved to {new_stage} stage", "info")
            break
    return redirect(url_for("dashboard", role=new_stage))


@app.route("/reports")
def reports():
    return render_template("reports.html", bills=bills)


@app.route("/audit")
def audit():
    return render_template("audit.html", audit=audit_log)


@app.route("/download_csv")
def download_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Branch", "Biller", "Consumer Number", "Amount", "Due Date", "Status", "Stage", "Created At"])
    for b in bills:
        cw.writerow([
            b["id"], b["branch"], b["biller"], b["consumer_number"],
            b["amount"], b["due_date"], b["status"],
            b["stage"], b["created_at"]
        ])
    output = si.getvalue()
    si.close()

    response = Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=bill_reports.csv"}
    )
    return response
