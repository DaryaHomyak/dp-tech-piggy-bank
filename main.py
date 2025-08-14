from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

wallets = [{"id": 0, "name": "w1", "currency": "RUB", "amount": 100}]
wallets_len = 1
transactions = []
transactions_len = 0


def make_json_response(data=None, error=None, status=200):
    return jsonify({"data": data, "error": error}), status


@app.route("/")
def index():
    return make_json_response({"status": "ok"})


@app.route("/api/wallets", methods=["GET"])
def get_wallets():
    return make_json_response(wallets)


@app.route("/api/wallets/<int:wallet_id>", methods=["GET"])
def get_wallet_by_id(wallet_id):
    wallet = next((w for w in wallets if w["id"] == wallet_id), None)
    if not wallet:
        return make_json_response(error="Wallet not found", status=404)
    return make_json_response(wallet)


@app.route("/api/wallets", methods=["POST"])
def create_wallet():
    global wallets_len
    body = request.get_json()
    name = body.get("name")
    currency = body.get("currency", "RUB")
    amount = body.get("amount", 0)

    if not name:
        return make_json_response(error="Name is required", status=400)

    wallet = {
        "id": wallets_len,
        "name": name,
        "currency": currency,
        "amount": amount
    }
    wallets.append(wallet)
    wallets_len += 1

    return jsonify({"data": wallet, "error": None}), 201, {"Location": f"/api/wallets/{wallet['id']}"}


@app.route("/api/wallets/<int:wallet_id>", methods=["PUT"])
def update_wallet(wallet_id):
    body = request.get_json()
    name = body.get("name")

    wallet = next((w for w in wallets if w["id"] == wallet_id), None)
    if not wallet:
        return make_json_response(error="Wallet not found", status=404)

    if not name:
        return make_json_response(error="Name is required", status=400)

    wallet["name"] = name
    return make_json_response(wallet)


@app.route("/api/wallets/<int:wallet_id>", methods=["DELETE"])
def delete_wallet(wallet_id):
    global wallets
    wallet = next((w for w in wallets if w["id"] == wallet_id), None)

    if not wallet:
        return make_json_response(error="Wallet not found", status=404)

    if wallet["amount"] != 0:
        return make_json_response(error="Wallet must be empty", status=409)

    wallets = [w for w in wallets if w["id"] != wallet_id]
    return "", 204


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    wallet_id = request.args.get("walletId", type=int)
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    result = transactions

    if wallet_id is not None:
        result = [t for t in result if t["walletId"] == wallet_id]

    if date_from:
        result = [t for t in result if t["occurredAt"] >= date_from]

    if date_to:
        result = [t for t in result if t["occurredAt"] <= date_to]

    return make_json_response(result)


@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    global transactions_len
    body = request.get_json()

    wallet_id = body.get("walletId")
    amount = body.get("amount")
    direction = body.get("direction")  # Income / Expense
    comment = body.get("comment", "")

    wallet = next((w for w in wallets if w["id"] == wallet_id), None)
    if not wallet:
        return make_json_response(error="Wallet not found", status=404)

    if direction not in ("Income", "Expense"):
        return make_json_response(error="Invalid direction", status=400)

    if direction == "Expense" and wallet["amount"] < amount:
        return make_json_response(error="Not enough balance", status=409)

    # Update balance
    if direction == "Income":
        wallet["amount"] += amount
    else:
        wallet["amount"] -= amount

    transaction = {
        "id": transactions_len,
        "walletId": wallet_id,
        "amount": amount,
        "direction": direction,
        "occurredAt": datetime.utcnow().isoformat(),
        "comment": comment
    }
    transactions.append(transaction)
    transactions_len += 1

    return jsonify({"data": transaction, "error": None}), 201, {"Location": f"/api/transactions/{transaction['id']}"}


@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    global transactions
    transaction = next((t for t in transactions if t["id"] == transaction_id), None)

    if not transaction:
        return make_json_response(error="Transaction not found", status=404)

    wallet = next((w for w in wallets if w["id"] == transaction["walletId"]), None)
    if not wallet:
        return make_json_response(error="Wallet not found", status=404)

    if transaction["direction"] == "Income":
        wallet["amount"] -= transaction["amount"]
    else:
        wallet["amount"] += transaction["amount"]

    transactions = [t for t in transactions if t["id"] != transaction_id]
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
