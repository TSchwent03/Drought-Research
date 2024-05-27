import numpy as np
from standard_precip.spi import SPI
import pandas as pd
import datetime as datetime
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from scipy.stats import norm

prcp_01_RefFileName = 'C:/Users/leasor.4/Documents/DocumentsOSU/NSF/NASA_Drought_Data/nClimGridAsClimDiv/ClimDiv_prcp_01_18950205To20210727.npz'
prcp_01_RefObject = np.load(prcp_01_RefFileName)
prcp_01_YYYYMMDD_Of_RefArray = prcp_01_RefObject['prcp_01_YYYYMMDD_Of_RefArray']
prcp_01_RefArray = prcp_01_RefObject['prcp_01_RefArray']
del(prcp_01_RefFileName,prcp_01_RefObject)

NewArrayDate = []
for i in range(0,len(prcp_01_YYYYMMDD_Of_RefArray)):
    mydate = datetime.datetime.strptime(str(prcp_01_YYYYMMDD_Of_RefArray[i][0]), '%Y%m%d')
    NewArrayDate.append(mydate.strftime('%Y-%m-%d'))

del i,mydate
spi1=[]
droughtdata_as_dataframe=pd.DataFrame(data=NewArrayDate,columns=['date'])
for i in range(0,1):#len(prcp_01_RefArray[0])):
    droughtdata_as_dataframe=droughtdata_as_dataframe.assign(data=prcp_01_RefArray[:,i]) 
    df_spi = SPI().calculate(droughtdata_as_dataframe,'date','data',freq="W",scale=1,fit_type="lmom",dist_type="gam")
    spi1.append(np.array(df_spi['data_calculated_index']))
    del df_spi
    print(i)