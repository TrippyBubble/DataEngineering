import pandas as pd



# Поиск отсутствующих значений и удаление дубликатов
def null(df):
    nan = len(df) * (0.7)  # 70% пропусков довольно высоко для статистических методов, нам придется их удалить.
    df = df.dropna(axis=1, thresh=nan)
    df.drop_duplicates()


    #если остались другие значения, где пустые поля
    missing_values = df.isnull().sum().sort_values(ascending=False) #Метод isnull() создаёт новый DataFrame того же размера, что и df, но с булевыми значениями: метод sum() применяется к результату isnull(), чтобы посчитать количество True (то есть пропущенных значений) в каждом столбце. Он работает по умолчанию по столбцам (оси 0) и суммирует количество True для каждого столбца.
    columns = missing_values[missing_values > 0].index.tolist()
    if columns:
        print("Количество пропущенных значений в каждом столбце:")
        for col, count in missing_values.items():
            if count > 0:
                print(f"{col}: {count} отсутствующих значений. Были заполенены средним")
            for column_name in columns:
                # Находим среднее столбца
                mean_value = df[column_name].mean()
                # Заполняем пустые значения средним значением
                df[column_name].fillna(mean_value, inplace=True)
    return df


# ищет выбросы по всем столбцам и удаляет строки с выбросами, хотя бы по одному параметру
def Quantile(df):
    for column_name in df.columns[2:len(df.columns)]:
        # Обнаруживаем выбросы
        Q1 = df[column_name].quantile(0.25)
        Q3 = df[column_name].quantile(0.75)
        IQR = Q3 - Q1
        # Удаление выбросов из основного DataFrame
        df2 = df[(df[column_name] >= Q1 - 1.5 * IQR) & (df[column_name] <= Q3 + 1.5 * IQR)]
    df = df2
    return df

# дисперсия
def disp(df):
    # Отделяем столбецы, которые не будем использовать для отбора
    first_column = df.iloc[:, 0: 2]
    gap = df['gap']
    df.drop(['gap'], axis=1, inplace=True)
    df.drop(first_column, axis=1, inplace=True)

    disp = df.var()

    #Устанавливаем порог
    FILTER_THRESHOLD = 0.1
    to_drop = [column for column in disp.index if disp[column] < FILTER_THRESHOLD]
    df = df.drop(to_drop, axis=1)

    # Соединяем первые столбцы с отобранными признаками
    df = pd.concat([first_column, gap, df], axis=1)

    return df