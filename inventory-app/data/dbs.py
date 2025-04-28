import pandas as pd

rmsg = {"id": '1234', "timestamp": 91532870, "mass": 54.5, "count": 10}

dbs = pd.read_csv('database.csv', header=None, names=['id','mass','price','total','count','timestamp'])
dbs.set_index('id')

idx = dbs.index.get_loc(rmsg['id'], drop=False, inplace=True)

dbs.loc[rmsg['id'], 'total'] = rmsg['mass']
dbs.loc[rmsg['id'], 'count'] = rmsg['count']
dbs.loc[rmsg['id'], 'timestamp'] = rmsg['timestamp']


print(dbs)

dbs.to_csv('database.csv', header=False, index=False)