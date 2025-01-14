import pubchempy as pcp
import pandas as pd
import numpy as np
import sqlite3

from prefect import flow, task
from os import path
from rdkit import Chem
from rdkit.Chem import Descriptors
from cleaning import null, Quantile, disp
from graphs import graphs

#Добавляем дескрипторы из PCP, которых нет в RDkit, они константы
properties = ['XLogP',                # Коэффициент распределения октанол-вода (логарифмическое значение)
    'ExactMass',            # Точная масса
    'MonoisotopicMass',     # Моноизотопная масса
    'TPSA',                 # Полярная площадь поверхности
    'Complexity',           # Сложность структуры
    'Charge',               # Заряд молекулы
    'HBondDonorCount',      # Количество доноров водородных связей
    'HBondAcceptorCount',   # Количество акцепторов водородных связей
    'RotatableBondCount',   # Количество вращаемых связей
    'HeavyAtomCount',       # Количество тяжелых атомо
    'IsotopeAtomCount',     # Количество атомов изотопов
    'AtomStereoCount',      # Общее количество стереоатомов
    'DefinedAtomStereoCount',   # Определенное количество стереоатомов
    'UndefinedAtomStereoCount', # Неопределенное количество стереоатомов
    'BondStereoCount',          # Общее количество стереосвязей
    'DefinedBondStereoCount',   # Определенное количество стереосвязей
    'UndefinedBondStereoCount', # Неопределенное количество стереосвязей
    'CovalentUnitCount'        # Количество ковалентных единиц
]



# Преобразуем нужные столбцы в строковый формат, на всякий случай
@task
def coll_string(df):
    for col in df.iloc[:, 0:2]:
        df[col] = df[col].astype(str)
    return df


#Добавляем дескрипторы
@task
def desc(df_1):
    i=0 #для подсчета, сколько дескрипторво было добавлено

    #Дескрипторы из библиотеки RDkit
    for descriptor in Descriptors.descList:
        df_1[descriptor[0]] = df_1["smiles"].apply(lambda x: descriptor[1](Chem.MolFromSmiles(x)))  #Запись всех
        # дескрипторов из РДкита
        print(descriptor[0])  #Чтоб быть увереным в процессе
        i += 1
    i =  i + len(properties)
    df_1.to_csv(path.join("dist", "РезультатRDkit"), index=False)

    #Дескрипторы из библиотеки PCP
    pp = pd.DataFrame()  #Пустой ДФ для записи туда дескрипторов
    for j in df_1['smiles']:
        find = pcp.get_properties(properties,j, 'smiles', as_dataframe=True)  #Получаем уникальные дескрипторы из PCP (кроме дескрипторов по 3д структуре)
        pp = pd.concat([pp, find.iloc[[0]]], ignore_index=True)
        print(len(pp),j)  #Чтобы быть уверенным в процессе
        if len(pp)%100 == 0:
            pp.to_csv(path.join("dist", "Результатbroke"), index=False) #на всякий случай сохраняем каждые 100стр, если программа зависнет или пропадет связь с сервером.
    pd.concat([df_1, pp], axis=1).to_csv(path.join("dist", "Результат"), index=False)
    print(f'Добавлено {i} дескрипторов в датасет.')
    return df_1


#Провоеряем, чтоб все полученные значения, были в float
@task
def coll_float(df):
    for col in df.iloc[:, 2:len(df.columns)]:
        df[col] = np.where(df[col] == 'no', 0, df[col])  # меняем no на 0 если есть
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


#Сейв с полученными дескрипторами. Добавляет новое вещество в DB
@task
def save_desc(df):
    conn = sqlite3.connect(path.join("data", "Chem.db"))
    df.to_sql("Descriptors", conn, if_exists="append", index=False)
    conn.close()
    return


#Обрабатываем и очищаем ДатаСет после добавление нового вещества, так как это будет влиять на выбросы и прочие
# показатели
@task
def cleaning():
    conn = sqlite3.connect(path.join("data", "Chem.db"))
    #получение уже нового ДФ
    df = pd.read_sql("SELECT * FROM Descriptors", conn)
    null(df)
    Quantile(df)
    disp(df)
    # Cейв после очистки
    df.to_sql("Results", conn, if_exists="replace", index=False)
    conn.close()
    return df




@flow
def collecting(df):
    print(df)
    #Преобразуем нужные столбцы в строковый формат, на всякий случай
    string = coll_string(df)
    print(df)
    #Добавляем дескрипторы
    descriptors = desc(string)

    # Провоеряем, чтоб все полученные значения, были во float
    float = coll_float(descriptors)

    #Сохраняем в БД промежуточный результат
    save_desc(float)

    #Очистка данных
    cleaning()

    graphs()

    return
