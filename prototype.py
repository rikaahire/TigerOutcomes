import database as db

def get_values():
    x = db.get_rows("demographics", 16000)
    legal_sex = x[:,1]
    first_gen = x[:,2]
    income = x[:,3]
    major = x[:,5]
    return major
