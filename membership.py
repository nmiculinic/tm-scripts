from datetime import date
import pandas as pd
import matplotlib as mpl
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from graphviz import Digraph
import numpy as np
import edlib
import tm


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
        if candidate_val > 4:
            sol[sa] = None
        print(sa, candidate, candidate_val)

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

print("Mapping DEBUG!")
for k, v in mapping.items():
    print(k, v)

norm = mpl.colors.Normalize()
age = [(pd.to_datetime(date.today()) - df[df.user == mapping[user]]["date"].min()) for user in users]
age = [x.days if hasattr(x, 'days') else 0 for x in age]
age_df = pd.DataFrame.from_dict({"user": users, "age": age})

print("age_df")
print(age_df)

print("Num_speeches")
num_speeches = pd.DataFrame(
    {'count':
     df[df.role.str.contains(r"(Speaker)|(Speech)")].groupby(["user"]).size()
     }
).reset_index()
print(num_speeches)

norm.autoscale(age_df["age"])
cm = mpl.cm.get_cmap('OrRd')

dot = Digraph(name="Mentorship", engine='neato', graph_attr={'fontname': "hack", "bgcolor": "#EAEAF2"})
dot.body.extend(['overlap=false', 'node [fontname = "hack"]', 'edge [fontname = "hack"]'])

def hhh(x):
    return str(hash(frozenset(map(str.strip, x.split()))))

for user, mentor in zip(users, mentors):
    if user.strip() == "":
        continue
    current_user_age = np.array(age_df[age_df.user == user]["age"]).ravel().item()
    r, b, g, _ = list(map(int, 255.9 * np.array(cm(norm(current_user_age)))))

    num_speeches_user = num_speeches[num_speeches.user == mapping[user]]["count"].as_matrix().ravel()
    if len(num_speeches_user) == 0:
        num_speeches_user = 0
    else:
        num_speeches_user = num_speeches_user.item()
    print(user, num_speeches_user)
    dot.node(hhh(user), user + "[%d]" % num_speeches_user, color="#%02x%02x%02x" % (r, b, g), style="filled")
    dot.edge(hhh(user), hhh(mentor))

dot.render("mentorship.dot")
