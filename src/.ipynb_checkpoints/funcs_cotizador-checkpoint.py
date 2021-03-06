import pandas as pd
import numpy as np
import seaborn as sns
import os,json
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn import metrics
import itertools as it
import pandas as pd
import numpy as np
import seaborn as sns
import os,json
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn import metrics
import itertools as it
from datetime import date, datetime, timedelta

######################################################################################################################

def data_cleaning_valset(df):
    '''Esta funcion se usa para las simulaciones.'''
    # parametros
    path_save = '../datos/'
    dolar_blue = 206  # actualizado al 1/03 
    dolar_oficial = 114.18
    
    old_shape = df.shape[0]
    ### 0) Nulos ###
    df = df.dropna()
    print(f'Hey! {old_shape - df.shape[0]} were removed due to null values')
    old_shape = df.shape[0]
    
    old_shape = df.shape[0]
    ### 1) Duplicados ###
    # tratamiento de la feautre "runtime"
    df['runtime'] = pd.to_datetime(df.runtime.apply(lambda x: str(x)[:19]))
    df = df.sort_values(['runtime'])
    # teniendo el df ordenado, eliminamos los duplicados, quedandonos con el registro más reciente (la última ocurrencia)
    df.drop_duplicates(subset=['car_id'], keep='last', inplace=True)
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due to duplicate values')
    old_shape = df.shape[0]
    
    ### 2) 11111 & 99999 ###
    # llevamos a int para detectar más facilmente los 1111 o 9999
    df['price_amount'] = df.price_amount.astype('int')
    # mascaras para los 1111 de price
    m1 = df.price_amount == 1111
    m2 = df.price_amount == 11111
    m3 = df.price_amount == 111111
    m4 = df.price_amount == 1111111
    m5 = df.price_amount == 11111111
    m6 = df.price_amount == 111111111
    # dropeamos los 11111 de price
    df = df[~(m1 | m2 | m3 | m4 | m5 | m6)]
    # mascaras para los 9999 de price
    m1 = df.price_amount == 9999
    m2 = df.price_amount == 99999
    m3 = df.price_amount == 999999
    m4 = df.price_amount == 9999999
    m5 = df.price_amount == 99999999
    # dropeamos los 9999 de price
    df = df[~(m1 | m2 | m3 | m4 | m5)]
    # ahora lo mismo pero para kms
    # llevamos a int para detectar más facilmente los 1111 o 9999
    df['car_kms'] = df.car_kms.astype('int')
    # mascaras para los 1111 de kms
    m1 = df.car_kms == 1
    m2 = df.car_kms == 11
    m3 = df.car_kms == 111
    m4 = df.car_kms == 1111
    m5 = df.car_kms == 11111
    m6 = df.car_kms == 111111
    m7 = df.car_kms == 1111111
    m8 = df.car_kms == 11111111
    # dropeamos los 1111 de kms
    df = df[~(m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8)]
    # mascaras para los 9999 de kms
    m1 = df.car_kms == 999
    m2 = df.car_kms == 9999
    m3 = df.car_kms == 99999
    m4 = df.car_kms == 999999
    m5 = df.car_kms == 9999999
    # dropeamos los 999 de kms
    df = df[~(m1 | m2 | m3 | m4 | m5)]
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due those 11111 or 9999 strange values')
    old_shape = df.shape[0]
    
    ### 3) Construccion final del target ###
    # Construcción del precio final
    blue= dolar_blue
    oficial= dolar_oficial
    col1 = 'price_symbol'
    col2 = 'car_kms'
    conditions = [df[col1]!='U$S', (df[col1]=='U$S') & (df[col2]==0), (df[col1]=='U$S') & (df[col2]!=0)]
    choices = [df.price_amount, df['price_amount']*oficial, df['price_amount']*blue]
    df['price_meli_ok'] = np.select(conditions, choices, default=np.nan)
    
    ### 4) Dropeamos 0kms y concesionarias
    df['dealer'] = np.where(df['dealer']==True,1,0)
    mask_not_0km = df.car_kms > 90
    mask_not_conces = df.dealer == 0
    df = df[(mask_not_0km) & (mask_not_conces)]
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due to 0km or concesioarias')
    old_shape = df.shape[0]
    
    ### 5) Dropeamos match_scores por debajo a 80% ###
    lst = ['score_marca_a','score_modelo_a','score_v1_c']
    for col in lst:
        df = df[df[col]>=80]
        
    print(f'Hey! {old_shape - df.shape[0]} were removed due to match scores under 50%')
    old_shape = df.shape[0]
        
    ### 6) Ultimos 15 días ###
    df['runtime'] = df['runtime'].apply(pd.to_datetime)
    max_date = df.runtime.max()
    mask_last15d = (df.runtime <= max_date) & ((df.runtime >= max_date - timedelta(days=15)))
    df = df[mask_last15d]
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due to last 15d filter')
    old_shape = df.shape[0]
    
    ### 7) Outliers globales ###
    f = open(os.path.join(path_save,'thresh_outliers_1.json'))
    thresh_outliers_1 = json.load(f)
    # dropeamos outliers globales en price
    mask = df.price_meli_ok <= thresh_outliers_1['price_p995']
    df = df[mask]
    # dropeamos outliers globales en kms
    mask = df.car_kms > thresh_outliers_1['kms_p995']
    df = df[~mask]
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due to outliers globales')
    old_shape = df.shape[0]
    
    ### 8) Categorías que no nos interesa cotizar ###
    marcas_ok = pd.read_csv('{}marcas_ok.csv'.format(path_save), index_col=[0])
    modelos_ok = pd.read_csv('{}modelos_ok.csv'.format(path_save), index_col=[0])
    versiones_ok = pd.read_csv('{}versiones_ok.csv'.format(path_save), index_col=[0])
    marcas_ok = list(marcas_ok.iloc[:,0])
    modelos_ok = list(modelos_ok.iloc[:,0])
    versiones_ok = list(versiones_ok.iloc[:,0])
    mask1 = df.match_marca_a.apply(lambda x: x in marcas_ok)
    mask2 = df.match_modelo_a.apply(lambda x: x in modelos_ok)
    mask3 = df.match_v1_a.apply(lambda x: x in versiones_ok)
    df = df[mask1 & mask2 & mask3]
    
    print(f'Hey! {old_shape - df.shape[0]} were removed due to categories in which we are not interested in score')
    old_shape = df.shape[0]
    
    # cuando hice el tratamiento de 1111 y 99999 había pasado la feature de kms a int. Volvemos a pasar a float por el catboost
    #df['car_kms'] = df['car_kms'].astype('float') # lo hacemos en la prox func de procesamiento
    
    id_features = ['runtime','car_id']
    model_features = ['car_year','car_kms','match_marca_a','match_modelo_a','match_v1_a','Subseg_a', 'Seg_a', 'price_meli_ok']
    others = ['car_location_1', 'match_v1_c']
    df = df[id_features + model_features + others]
    
    return df
    

######################################################################################################################


def data_processing_1(df, path_data):
    '''This function is to perform the data cleaning on a test or validation set'''
    # upload the dictionary with the information (learned with the train set!) about the thresholds to cap outliers
    f = open(os.path.join(path_data,'price_thresh_outliers.json'))
    price_thresh_outliers = json.load(f)
    f = open(os.path.join(path_data,'kms_thresh_outliers.json'))
    kms_thresh_outliers = json.load(f)
    
    modelos = sorted(list(df.match_modelo_a.unique()))
    años = sorted(list(df.car_year.unique()))
    old_shape = df.shape[0]
    for m in modelos:
        for a in años:
            # print(f'{m} of {a}') --> solo para chequear que el loop este iterando correctamente (esta OK :)
            
            modelo_año = m + '_' + str(a)
            
            if str(price_thresh_outliers[modelo_año][0]) == 'nan':
                pass
            else:
                # kms
                mask1 = df.match_modelo_a == m
                mask2 = df.car_year == a
                data = df[mask1 & mask2].copy()

                filt_mask_sup = data.car_kms>kms_thresh_outliers[modelo_año][1]
                filt_mask_inf = data.car_kms<kms_thresh_outliers[modelo_año][0]
                data = data[~(filt_mask_sup | filt_mask_inf)]
                df = df.loc[~(mask1 & mask2),:]
                df = pd.concat([df,data],0)

                # price
                mask1 = df.match_modelo_a == m
                mask2 = df.car_year == a
                data = df[mask1 & mask2].copy()

                filt_mask_sup = data.price_meli_ok>price_thresh_outliers[modelo_año][1]
                filt_mask_inf = data.price_meli_ok<price_thresh_outliers[modelo_año][0]
                data = data[~(filt_mask_sup | filt_mask_inf)]
                df = df.loc[~(mask1 & mask2),:]
                df = pd.concat([df,data],0)
    
    # probamos tanto usando year como int y como float y la perfo del modelo dio apenas mejor con year en float
    df['car_year'] = df['car_year'].astype('float')
    
    print(f'Hey! {old_shape - df.shape[0]} were removed from df due to outliers under context')  
    
    return df

######################################################################################################################

def print_evaluate(true, predicted):
    
    def mape(actual, pred):
        actual, pred = np.array(actual), np.array(pred)
        mape = np.mean(np.abs((actual-pred)/actual)) * 100
        return mape
    def medape(actual, pred):
        actual, pred = np.array(actual), np.array(pred)
        medape = np.median(np.abs((actual-pred)/actual)) * 100
        return medape
    
    mae = metrics.mean_absolute_error(true, predicted)
    mape = mape(true, predicted)
    medape = medape(true, predicted)
    mse = metrics.mean_squared_error(true, predicted)
    rmse = np.sqrt(metrics.mean_squared_error(true, predicted))
    r2_square = metrics.r2_score(true, predicted)
    print('MAE:', mae)
    print('MAPE:', mape)
    print('MEDAPE:', medape)
    print('MSE:', mse)
    print('RMSE:', rmse)
    print('R2 Square', r2_square)
    print('__________________________________')
    
def evaluate(true, predicted):
    mae = metrics.mean_absolute_error(true, predicted)
    mse = metrics.mean_squared_error(true, predicted)
    rmse = np.sqrt(metrics.mean_squared_error(true, predicted))
    r2_square = metrics.r2_score(true, predicted)
    return mae, mse, rmse, r2_square