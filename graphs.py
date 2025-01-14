import sqlite3
import os.path as path
import ssl
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


from scipy.stats import ttest_ind
from os import path
from scipy import stats


try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

import warnings

warnings.filterwarnings('ignore')
warnings.filterwarnings("ignore", category=DeprecationWarning)

def graphs():
    conn = sqlite3.connect(path.join("data", "Chem.db"))


    query = "SELECT alpha FROM Results"
    gap_data = pd.read_sql(query, conn)
    df = pd.read_sql("SELECT * FROM Results", conn)

    # Построение гистограммы
    sns.set_palette("dark")  # Установка стиля
    sns.histplot(gap_data['alpha'], kde=True)
    plt.title("Гистограмма для alpha - Изотропная поляризуемость")
    plt.xlabel("Изотропная поляризуемость")
    plt.ylabel("Частота")

    # Сохранение графика в PNG
    output_path = path.join("graphs", "alpha_histogram.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")  # DPI задает качество, bbox_inches для обрезки лишнег


    #Нормализация данных (MinMaxScaler)(маштабирование (переводит значения в каждом числовом столбце в диапазон от 0 до 1))
    for col in df.columns:
        if df[col].dtype != 'object':
            min_val = df[col].min()
            max_val = df[col].max()
            df[col] = (df[col] - min_val) / (max_val - min_val)

    # Выполняем независимый t-тест между 'mu' У которых 'alpha' меньше и больше 0
    amidelow = df.loc[df['alpha'] < 0.5, ['mu']]
    amidehigh = df.loc[df['alpha'] > 0.5, ['mu']]
    t_stat, p_value = ttest_ind(amidelow['mu'], amidehigh['mu'], equal_var=False)
    # 3. ANOVA (для сравнения нескольких групп)
    anova_result = stats.f_oneway(amidelow['mu'], amidehigh['mu'])
    # Построение гистограмм
    plt.figure(figsize=(15, 10))  # Установка размеров графика
    sns.histplot(amidelow['mu'], color='blue', kde=True, label='mu, при alpha < 0.5', bins=20)
    sns.histplot(amidehigh['mu'], color='red', kde=True, label='mu, при alpha > 0.5', bins=20)
    # Настройка графика
    plt.title("Сравнение распределений alpha", fontsize=16)
    plt.xlabel(f"mu\nt-test: {t_stat:.2f}, p-значение = {p_value}\nANOVA: {anova_result}", fontsize=14)
    plt.ylabel("Частота", fontsize=14)
    plt.legend(title="Группы", fontsize=12)
    plt.grid(visible=True, linestyle='--', alpha=0.5)  # Сетка для удобства


    output_path = path.join("graphs", "mu_histogram.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")  # DPI задает качество, bbox_inches для обрезки лишнег



    corr = df.iloc[:, :20].corr()

    # Построение тепловой карты корреляции
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, cmap='coolwarm', annot=False, fmt=".2f", cbar=True)
    plt.title("График корреляции для первых 20 столбцов")
    plt.tight_layout()
    output_path = path.join("graphs", "heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")  # DPI задает качество, bbox_inches для обрезки лишнег



    # Построение графика корреляции
    sns.set_palette("dark")
    plt.figure(figsize=(8, 6))
    sns.regplot(x='mu', y='MaxAbsEStateIndex', data=df, scatter_kws={'alpha': 0.7}, line_kws={'color': 'red'})
    plt.title("График корреляции mu от Electrotopological State (EState) индекса")
    plt.xlabel("mu")
    plt.ylabel("EState индекс")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    output_path = path.join("graphs", "corr.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")  # DPI задает качество, bbox_inches для обрезки лишнег


    conn.close()