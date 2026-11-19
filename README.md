# FinanceManager 💰

A personal finance management desktop application built with Python.

FinanceManager provides an intuitive interface to manage income, expenses, accounts, and categories, while offering financial insights through interactive dashboards and charts.

## ✨ Features

### 📊 Dashboard
- Overview of total account balance.
- Income and expense summaries.
- Daily and monthly financial charts.
- Expense breakdown by category.
- Recent transaction overview.
- Customizable analysis periods.

### 💳 Transaction Management
- Add, edit, and delete transactions.
- Organize transactions into income and expenses.
- Assign categories and accounts.
- Add descriptions and additional notes.
- Search and filter transactions.

### 🏦 Account Management
- Create, edit, and delete accounts.
- Support for checking accounts, savings, cash, and digital wallets.
- Initial balance configuration.
- Automatic balance calculation based on transactions.

### 🗂️ Category Management
- Create custom income and expense categories.
- Edit and delete categories.
- Organize transactions by category.

### 📈 Financial Reports
- Visual comparison of income and expenses.
- Expense distribution by category.
- Financial analysis by selected period.
- Percentage breakdown of expenses.

## 🛠️ Technologies

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| CustomTkinter | Modern graphical user interface |
| SQLite | Local database management |
| Matplotlib | Financial charts and data visualization |
| Decimal | Accurate monetary calculations |

## 📁 Project Structure

```text
FinanceManager/
│
├── assets/
│
├── database/
│   └── finance.db
│
├── app.py
├── database.py
├── test_database.py
├── iconefinancemanager.ico
│
├── .gitignore
└── README.md

## ⚙️ Installation

### 1. Clone the repository

git clone https://github.com/amrcjos/FinanceManager.git

### 2. Navigate to the project folder

cd FinanceManager

### 3. Create a virtual environment

python -m venv .venv

### 4. Activate the environment

**Windows:**

.venv\Scripts\activate

### 5. Install dependencies

pip install customtkinter matplotlib

### 6. Run the application

python app.py

## 🗄️ Database

FinanceManager uses SQLite to store financial information locally.

The database is automatically initialized when the application starts.

It contains three main tables:

- `accounts` — Stores financial accounts and initial balances.
- `categories` — Stores income and expense categories.
- `transactions` — Stores financial transactions and their associated information.

Financial amounts are stored as integer cents to avoid floating-point precision issues.

## 🎨 Interface

The application features a dark-themed interface with a sidebar navigation system, organized dashboard cards, and interactive financial charts.

## 🎯 Project Purpose

FinanceManager was developed as a personal software development project to practice and apply concepts such as:

- Python application development.
- GUI development.
- Relational database design.
- SQL queries and CRUD operations.
- Data visualization.
- Financial data processing.
- Code organization and modularity.

## 👨‍💻 Author

José Américo

Developed as a personal programming project.
