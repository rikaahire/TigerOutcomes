import database as db

def get_values(major_in):
    major = "demographics.AcadPlanDescr = 'Computer Science'"
    # out = db.get_rows("demographics", major)
    out = db.get_first_rows("demographics", 10)
    # out = [0, 1, "Yes", 30000, "Female"]
    return out[1]
