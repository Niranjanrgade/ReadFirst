
def get_dummy_clauses():
    safe = [
        "You may use the service for personal use.",
        "Your data is stored securely."
    ]
    risky = [
        "We reserve the right to modify your content without notice.",
        "You agree to mandatory binding arbitration.",
        "We may share your information with third-party partners."
    ]
    return safe, risky
