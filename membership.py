from datetime import date
import pandas as pd
import matplotlib as mpl
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from graphviz import Digraph
import numpy as np
import edlib

def createMapping(set_a, set_b):
    sol = {}
    for sa in set_a:
        a = sa.split()
        candidate = None
        candidate_val = 1e4
        for sb in set_b:
            b = sb.split()
            assert len(a) == 2
            assert len(b) == 2

            v1 = edlib.align(a[0], b[0])['editDistance'] + edlib.align(a[1], b[1])['editDistance']
            v2 = edlib.align(a[0], b[1])['editDistance'] + edlib.align(a[1], b[0])['editDistance']
            d = min(v1, v2)
            if d < candidate_val:
                candidate = sb
                candidate_val = d
        sol[sa] = candidate

    return sol

# Get members spreadsheet

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('./tm-scripts-gdrive.json', scope)
gc = gspread.authorize(credentials)
sh = gc.open_by_key("1lsAf0e5XICHpMq7ud9uHhwElFGTjoGfs2HDn-8JCmmo")
users = list(filter(lambda x: len(x.strip()) > 0, sh.sheet1.col_values(2)[1:]))
mentors = list(filter(lambda x: len(x.strip()) > 0, sh.sheet1.col_values(3)[1:]))

# Role report (for joining date as first time taking role)
df = tm.read_role_report('./RoleHistory.html')
mapping = createMapping(users, np.unique(df.user))


norm = mpl.colors.Normalize()
age = [(pd.to_datetime(date.today()) - df[df.user == mapping[user]]["date"].min()).days for user in users]
age_df = pd.DataFrame.from_dict({"user": users, "age":age})

norm.autoscale(age_df["age"])
cm = mpl.cm.get_cmap('OrRd')

dot = Digraph(name="Mentorship", engine='neato')
dot.body.extend(['overlap=false'])
def hhh(x):
    return str(hash(frozenset(map(str.strip, x.split()))))

for user, mentor in zip(users, mentors):
    if user.strip() == "":
        continue
    current_user_age = np.array(age_df[age_df.user == user]["age"]).ravel().item()
    r, b, g, _ = list(map(int, 255.9 * np.array(cm(norm(current_user_age)))))

    dot.node(hhh(user), user, color="#%02x%02x%02x" % (r, b, g), style="filled")
    dot.edge(hhh(user), hhh(mentor))

dot.render("mentorship.svg")
