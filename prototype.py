import database as db

def get_values(major_in):
    major = "demographics.AcadPlanDescr = 'Computer Science'"
    # out = db.get_rows("demographics", major)
    out = db.get_first_rows("demographics", 1000)
    return out[70]
