from pulp import LpVariable, LpProblem, lpSum, LpMaximize
from helpers import Config, tot_give
import pandas as pd


def best_giving_pulp(c: Config) -> pd.DataFrame:

    """ LP approach not working yet, problem with recursive objective function! """

    df = c.df.copy()

    prob = LpProblem('MaximizeGiving', LpMaximize)
    age_index = list(df.index)
    disp = df['disposable_salary'].to_dict()
    give_share_dict = LpVariable.dicts('give_share', age_index, lowBound=0, upBound=1, cat='Continuous')
    r = c.net_return_mult

    # Define Objective
    prob = lpSum(tot_give(disp, give_share_dict, r))

    # Solve problem and return dict with coefs
    prob.solve()
    res = dict(zip(list(age_index), [give_share_dict[i].varValue for i in age_index]))
    res_df = pd.DataFrame(data=res.values(), index=list(res.keys()), columns=['give_share'])
    res_df.index.name = 'age'
    return res_df
