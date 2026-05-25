import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "business.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(seed: bool = True) -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reimbursements (
                id TEXT PRIMARY KEY,
                uid TEXT NOT NULL,
                item_name TEXT NOT NULL,
                amount REAL NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                has_approval INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                reimbursement_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        if not seed:
            return

        connection.executemany(
            """
            INSERT OR IGNORE INTO employees (uid, name, department, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("1001", "张三", "研发部", "算法工程师", "active"),
                ("1002", "李四", "财务部", "财务专员", "active"),
                ("1003", "王五", "销售部", "客户经理", "active"),
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO reimbursements
                (id, uid, item_name, amount, platform, status, has_approval, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("R1001", "1001", "人体工学椅", 300.0, "淘宝", "submitted", 0, "2026-05-20"),
                ("R1002", "1003", "客户拜访打车", 230.0, "滴滴", "submitted", 1, "2026-05-21"),
                ("R1003", "1001", "一线城市住宿", 700.0, "携程", "submitted", 0, "2026-05-22"),
            ],
        )
