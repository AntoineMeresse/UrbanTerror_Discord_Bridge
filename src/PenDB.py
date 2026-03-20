from datetime import date, timedelta

import psycopg2

POTD_LIMIT = 40
HOF_HOS_LIMIT = 15

_CONNECT_OPTS = "-c default_transaction_read_only=on"


def _pen_symbol(rank: int, hos: bool) -> str:
    if hos:
        symbols = {1: "8=D", 2: "8==D", 3: "8===D"}
        return symbols.get(rank, "8====D")
    else:
        symbols = {1: "8====D", 2: "8===D", 3: "8==D"}
        return symbols.get(rank, "8=D")


def _connect(uri: str):
    return psycopg2.connect(uri, connect_timeout=5, options=_CONNECT_OPTS)


def pen_of_the_day(uri: str, target_date: date):
    conn = _connect(uri)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pen.id, pen.guid, pen.date, pen.size, player.name
                FROM pen
                JOIN player ON pen.guid = player.guid
                WHERE date = %s
                ORDER BY size DESC
                LIMIT %s
                """,
                (target_date, POTD_LIMIT),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    # rows: (id, guid, date, size, name)
    lines = [f"=========== Pen of the day ({target_date}) ==========="]
    if not rows:
        lines.append("Connect to a server and use !pen, there is no values yet :(")
    else:
        for i, (_, _, _, size, name) in enumerate(rows):
            pen = _pen_symbol(i + 1, hos=False)
            lines.append(f"{pen} {name} : {size:.3f} cm.")
    return lines


def pen_of_today(uri: str):
    return pen_of_the_day(uri, date.today())


def pen_of_yesterday(uri: str):
    return pen_of_the_day(uri, date.today() - timedelta(days=1))


def pen_hall_of_fame(uri: str):
    today = date.today()
    conn = _connect(uri)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pen.id, pen.guid, pen.date, pen.size, player.name
                FROM pen
                JOIN player ON pen.guid = player.guid
                WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM %s::date)
                ORDER BY size DESC
                LIMIT %s
                """,
                (today, HOF_HOS_LIMIT),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    lines = [f"=========== Pen Hall Of Fame ({today.year}) ==========="]
    if not rows:
        lines.append("Use !pen, there is no pen values yet :(")
    else:
        for i, (_, _, pen_date, size, name) in enumerate(rows):
            pen = _pen_symbol(i + 1, hos=False)
            lines.append(f"{pen} {name} : {size:.3f} cm. ({pen_date})")
    return lines


def pen_hall_of_shame(uri: str):
    today = date.today()
    conn = _connect(uri)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pen.id, pen.guid, pen.date, pen.size, player.name
                FROM pen
                JOIN player ON pen.guid = player.guid
                WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM %s::date)
                ORDER BY size ASC
                LIMIT %s
                """,
                (today, HOF_HOS_LIMIT),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    lines = [f"=========== Pen Hall Of Shame ({today.year}) ==========="]
    if not rows:
        lines.append("Use !pen, there is no pen values yet :(")
    else:
        for i, (_, _, pen_date, size, name) in enumerate(rows):
            pen = _pen_symbol(i + 1, hos=True)
            lines.append(f"{pen} {name} : {size:.3f} cm. ({pen_date})")
    return lines
