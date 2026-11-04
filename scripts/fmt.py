"""Форматирование чисел по правилам OSNOVA Finance (RU)."""
NB = " "  # неразрывный пробел


def _num(x, dec):
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s.replace(" ", NB)


def _scaled(v):
    """Три значащих цифры: 84,9 / 845 / 1,23 -> 1,2."""
    a = abs(v)
    if a >= 100:
        return _num(v, 0)
    s = _num(v, 1)
    return s[:-2] if s.endswith(",0") else s


def fmt_value(v, unit):
    if unit == "num1":
        return _scaled(v)
    if unit == "pct0":
        return f"{_num(v, 0)}%"
    if unit == "pct":
        return f"{_num(v, 1)}%"
    if unit == "usd_pc":
        return f"${_num(v, 0)}"
    if unit == "usd":
        a = abs(v)
        if a >= 1e12:
            return f"${_scaled(v / 1e12)}{NB}трлн"
        if a >= 1e9:
            return f"${_scaled(v / 1e9)}{NB}млрд"
        if a >= 1e6:
            return f"${_scaled(v / 1e6)}{NB}млн"
        return f"${_scaled(v / 1e3)}{NB}тыс."
    if unit == "t":
        a = abs(v)
        if a >= 1e9:
            return f"{_scaled(v / 1e9)}{NB}млрд{NB}т"
        if a >= 1e6:
            return f"{_scaled(v / 1e6)}{NB}млн{NB}т"
        if a >= 1e3:
            return f"{_scaled(v / 1e3)}{NB}тыс.{NB}т"
        return f"{_num(v, 0)}{NB}т"
    return _num(v, 1)


def flag(iso2):
    if not iso2 or len(iso2) != 2 or not iso2.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in iso2.upper())
