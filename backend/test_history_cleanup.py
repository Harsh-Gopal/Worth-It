from datetime import datetime, timezone, timedelta

def test_cleanup(tz_offset_mins=-330, days=7):
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc - timedelta(minutes=tz_offset_mins)
    cutoff_local = (now_local - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    cutoff_utc = cutoff_local + timedelta(minutes=tz_offset_mins)
    cutoff = cutoff_utc.isoformat()
    print("Now UTC:", now_utc.isoformat())
    print("Now Local:", now_local.isoformat())
    print("Cutoff Local:", cutoff_local.isoformat())
    print("Cutoff UTC:", cutoff)

test_cleanup()
