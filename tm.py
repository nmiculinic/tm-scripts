from bs4 import BeautifulSoup
import pandas as pd
import sys
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def read_role_report(fname):
    with open(fname, 'r') as f:
        soup = BeautifulSoup(f.read(), "html5lib")

    current_user = None
    awards = None

    sol = []

    for el in soup.find_all("tr"):
        tds = el.find_all('td')
        if len(tds) != 3:
            continue
        if tds[0].string is not None:
            current_user, *awards = map(str.strip, tds[0].string.split(','))

        sol.append((
            current_user,
            awards,
            pd.to_datetime(tds[1].string.strip()),
            tds[2].string.strip()
        ))
    return pd.DataFrame.from_records(sol, columns=["user", "awards", "date", "role"])


def read_speech_history(fname):
    with open(fname, 'r') as f:
        soup = BeautifulSoup(f.read(), "html5lib")

    current_user = None
    awards = None

    sol = []

    for el in soup.find_all("tr"):
        try:
            tds = el.find_all('td')
            if len(tds) != 6:
                continue
            if tds[0].string is not None:
                current_user, *awards = map(str.strip, tds[0].string.split(','))

            if len(tds[4].contents) == 3:
                manual, project = tds[4].contents[0].strip()[:-1], tds[4].contents[2]
            else:
                manual, project = "CUSTOM", "".join(tds[4].contents)

            sol.append((
                current_user,
                awards,
                pd.to_datetime(tds[1].string.strip()),
                tds[2].string,
                tds[3].string,
                manual,
                project,
                tds[5].string,
            ))
        except Exception as ex:
            print(ex, file=sys.stderr)
            print("Error in parsing\n%s" % str(el), file=sys.stderr)
            print(tds[4].contents, file=sys.stderr)
            raise

    return pd.DataFrame.from_records(sol, columns=["user", "awards", "date", "duration", "title", "manual", "project", "introduction"])


def user_diff(df, name, filterval=None):
    mdates = pd.Series(np.unique(df.date))
    user = df[df.user == name]
    if len(user) == 0:
        raise ValueError("%s not found", name)

    sol = []

    for s1, s2 in zip(user.date, user.date[1:]):
        sol.append(mdates[np.logical_and(s1 < mdates, mdates < s2)].shape[0])
    sol = np.array(sol)
    sol[sol > filterval] = filterval
    return sol


def gen_time_fig_diff(df, title="", datefmt=r"%d.%m.%Y"):
    users = np.unique(df.user)
    n = len(users)
    fig, axes = plt.subplots(n // 4, 4, sharex=False, sharey=True)
    fig.set_size_inches(12, 4 * (n // 4))
    for user, ax in zip(users, axes.ravel()):
        data = user_diff(df, user, filterval=1000)
        # data = np.clip(data, 0, 10)
        ax.plot(data)
        ax.set_xlabel(user + "[%d]" % np.sum(df.user == user))
        ax.set_ylim([0, 10])
    fig.tight_layout()
    fig.suptitle(title + " from %s to %s" % (np.min(df.date).strftime(datefmt), np.max(df.date).strftime(datefmt),))
    return fig


def gen_fig_diff(df, title="", filterval=10, datefmt=r"%d.%m.%Y"):
    users = np.unique(df.user)
    n = len(users)
    fig, axes = plt.subplots(n // 4, 4, sharex=True, sharey=True)
    fig.set_size_inches(12, 4 * (n // 4))
    for user, ax in zip(users, axes.ravel()):
        data = user_diff(df, user, filterval)
        ax.hist(data, label=user, bins=np.linspace(-.5, filterval+0.5, int(filterval)), normed=1)
        try:
            sns.kdeplot(data, ax=ax, legend=False)
        except Exception as ex:
            # print(ex, file=sys.stderr)
            pass
        ax.set_xlabel(user + "[%d]" % np.sum(df.user == user))
        ax.set_ylim([0, 1])
        ax.set_xlim([-0.5, filterval + 0.5])
    fig.tight_layout()
    fig.suptitle(title + " from %s to %s" % (np.min(df.date).strftime(datefmt), np.max(df.date).strftime(datefmt),))
    return fig
