import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Get user's owned stocks
    stocks = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        session["user_id"],
    )

    # Get user cash
    user = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = user[0]["cash"]

    total_value = 0
    for stock in stocks:
        quote = lookup(stock["symbol"])
        if quote:
            stock["name"] = quote["name"]
            stock["price"] = quote["price"]
            stock["value"] = stock["price"] * stock["total_shares"]
        else:
            stock["name"] = "N/A"
            stock["price"] = 0
            stock["value"] = 0
        total_value += stock["value"]

    grand_total = cash + total_value

    return render_template(
        "index.html",
        stocks=stocks,
        cash=usd(cash),
        total_value=usd(total_value),
        grand_total=usd(grand_total),
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol", "").upper().strip()
        shares_str = request.form.get("shares", "").strip()

        if not symbol:
            return apology("must provide symbol")
        if not shares_str.isdigit():
            return apology("shares must be positive integer")

        shares = int(shares_str)
        if shares <= 0:
            return apology("shares must be positive integer")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol")

        price = quote["price"]
        total_cost = price * shares

        user = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = user[0]["cash"]

        if cash < total_cost:
            return apology("not enough cash")

        # Record transaction and update cash
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session["user_id"],
            symbol,
            shares,
            price,
        )

        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            total_cost,
            session["user_id"],
        )

        flash(f"Bought {shares} shares of {symbol} for {usd(total_cost)}!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol", "").upper().strip()
        if not symbol:
            return apology("must provide symbol")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol")

        return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not username:
            return apology("must provide username")
        if not password:
            return apology("must provide password")
        if password != confirmation:
            return apology("passwords don't match")

        # Check if username already exists
        existing = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing:
            return apology("username already exists")

        # Try to insert user safely
        try:
            hash_ = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_)
        except Exception:
            # In case of DB constraint error (duplicate username)
            return apology("username already exists")

        # Log in new user
        user = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = user[0]["id"]

        flash("Registered successfully!")
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stocks = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        session["user_id"],
    )

    if request.method == "POST":
        symbol = request.form.get("symbol", "").upper().strip()
        shares_str = request.form.get("shares", "").strip()

        if not symbol:
            return apology("must provide symbol")
        if not shares_str.isdigit():
            return apology("shares must be positive integer")

        shares = int(shares_str)
        if shares <= 0:
            return apology("shares must be positive integer")

        owned = db.execute(
            "SELECT SUM(shares) AS total_shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol",
            session["user_id"],
            symbol,
        )

        if not owned or owned[0]["total_shares"] < shares:
            return apology("not enough shares")

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol")

        price = quote["price"]
        total_sale = shares * price

        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session["user_id"],
            symbol,
            -shares,
            price,
        )

        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            total_sale,
            session["user_id"],
        )

        flash(f"Sold {shares} shares of {symbol} for {usd(total_sale)}!")
        return redirect("/")
    else:
        # Add company names for dropdown
        for stock in stocks:
            quote = lookup(stock["symbol"])
            stock["name"] = quote["name"] if quote else stock["symbol"]
        return render_template("sell.html", stocks=stocks)
