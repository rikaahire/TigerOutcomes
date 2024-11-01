import database as db

def get_values(major_in):
    # x = db.get_rows("demographics", 16000)
    # legal_sex = x[:,1]
    # first_gen = x[:,2]
    # income = x[:,3]
    # major = x[:,5]
    out = [0, 1, "Yes", 30000, "Female"]
    print(major_in)
    return out
