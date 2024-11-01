import database as db

def get_values(major_in):
    out = db.get_rows("demographics", major_in)
    return out
