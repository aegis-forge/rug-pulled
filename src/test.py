# %%
from pandas import DataFrame, read_csv

# %% 
df = read_csv("../data/dataset.csv")

# %%
s = df[["dependency", "dependency_v", "dependency_t"]].dropna()
d = s[s["dependency_t"] == "indirect"]
(d["dependency"] + d["dependency_v"]).nunique()
