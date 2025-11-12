from datetime import datetime


def build_tracking_code(year: int, seq: int) -> str:
    # Example: PRC-2025-000123
    return f"PRC-{year}-{seq:06d}"


def generate_tracking_code(next_id: int) -> str:
    # Simple and deterministic: use DB auto-increment id as sequence
    year = datetime.utcnow().year
    return build_tracking_code(year, next_id)
