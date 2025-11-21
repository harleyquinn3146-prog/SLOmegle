import database as db
import os
import logging

# Setup
if os.path.exists("bot.db"):
    os.remove("bot.db")

logging.basicConfig(level=logging.INFO)
db.init_db()

def test_blocking():
    print("Testing Blocking Logic...")
    user1 = 1001
    user2 = 1002
    user3 = 1003

    # 1. Add users to queue
    db.add_to_queue(user2, "Tech")
    db.add_to_queue(user3, "Tech")

    # 2. User 1 blocks User 2
    db.block_user(user1, user2)

    # 3. User 1 searches for match (Tech)
    # Should match with User 3, NOT User 2
    partner = db.get_from_queue(user1, "Tech")
    
    if partner == user3:
        print("✅ PASS: User 1 matched with User 3 (User 2 was blocked)")
    elif partner == user2:
        print("❌ FAIL: User 1 matched with User 2 (Blocked user!)")
    else:
        print(f"❌ FAIL: User 1 matched with {partner} (Expected 1003)")

def test_reporting():
    print("\nTesting Reporting Logic...")
    reporter = 1001
    reported = 1002
    reason = "Spam"

    db.report_user(reporter, reported, reason)
    
    # Verify in DB
    conn = db._connect()
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE reporter_id=? AND reported_id=?", (reporter, reported))
    row = c.fetchone()
    conn.close()

    if row:
        print(f"✅ PASS: Report found: {row}")
    else:
        print("❌ FAIL: Report not found in DB")

if __name__ == "__main__":
    test_blocking()
    test_reporting()
