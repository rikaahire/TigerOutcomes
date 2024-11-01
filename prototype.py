import database as db

def get_values(major_in):
    print(major_in)
    # x = db.get_rows("demographics", 16000)
    # legal_sex = x[:,1]
    # first_gen = x[:,2]
    # income = x[:,3]
    # major = x[:,5]
    major = "demographics.AcadPlanDescr = 'Computer Science'"
    # out = db.get_rows("demographics", major)
    out = db.get_first_rows("demographics", 10)
    # out = [0, 1, "Yes", 30000, "Female"]
    return out[1]
