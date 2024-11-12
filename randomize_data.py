import pandas as pd
import random

# Load Excel file
df = pd.read_excel('/Users/suria./Documents/COLLEGE/3rd Year/cos333/COS333_Demographics.xlsx')

# Randomize values in columns except StudyID
for column in df.columns:
    if column != 'StudyID':
        df[column] = random.sample(df[column].tolist(), len(df[column]))

# Save to new Excel file
df.to_excel('COS333_Demographics.xlsx', index=False)


# Load Excel file
df = pd.read_excel('/Users/suria./Documents/COLLEGE/3rd Year/cos333/COS333_AcA_Student_Outcomes.xlsx')

# Randomize values in Position column
df['Position'] = random.sample(df['Position'].tolist(), len(df['Position']))

# Save to new Excel file
df.to_excel('COS333_AcA_Student_Outcomes.xlsx', index=False)