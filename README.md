# 📈 CS50x Finance: Full-Stack Trading Simulator

A dynamic web application that simulates a real-time stock trading environment. This platform allows users to register secure accounts, quote live stock prices, and manage a virtual financial portfolio.

## 🚀 Key Impact
- **Live Data Integration:** Integrated an external financial API to fetch real-time market data, ensuring users see accurate, up-to-the-second stock valuations and portfolio tracking.
- **Data Persistence:** Designed a relational SQL database structure to efficiently track user balances, manage stock ownership, and maintain a comprehensive, timestamped history of all buy/sell transactions.
- **Secure Architecture:** Implemented secure user authentication and session management to protect user portfolios and simulated financial data from unauthorized access.

## 🛠️ Technologies Used
- **Backend:** Python, Flask
- **Database:** SQLite3, SQL
- **Frontend:** HTML5, CSS3, Jinja2

## 📋 Core Features
- **Quote:** Look up live stock prices instantly.
- **Buy/Sell:** Execute virtual trades that dynamically calculate total costs and automatically update the user's cash balance and portfolio holdings.
- **Transaction Ledger:** View a complete, chronological history of all past account activity.

## 📖 How to Run Locally
1. Clone this repository to your local machine.
2. Ensure you have Python and Flask installed (`pip install flask cs50`).
3. Set your API key environment variable (if using a live IEX Cloud key).
4. Run `flask run` in your terminal.
5. Open the provided `localhost` link in your browser to start trading!
