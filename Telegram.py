import asyncio
import logging
import pandas as pd
import time

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from os import path


TOKEN = 'YourAPI'
needs = FSInputFile(path.join('data', 'Screenshot 2025-01-14 at 02.11.09.png'))


needs_list = ['mol_id', 'smiles', 'A', 'B', 'C', 'mu', 'alpha', 'homo', 'lumo', 'gap', 'r2', 'zpve', 'u0', 'u298', 'h298', 'g298', 'cv', 'u0_atom', 'u298_atom', 'h298_atom', 'g298_atom']
# Глобальная переменная для хранения final_df
final_df_global = None
bot = Bot(token=TOKEN)
dp = Dispatcher()
# Пути к изображениям
graphs = [
    FSInputFile(path.join('graphs', 'alpha_histogram.png')),
    FSInputFile(path.join('graphs', 'corr.png')),
    FSInputFile(path.join('graphs', 'heatmap.png')),
    FSInputFile(path.join('graphs', 'mu_histogram.png'))
]

mainb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Начать ввод данных')],
    [KeyboardButton(text='Посмотреть графики')]
])



@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('Я бот, который добавляет новые экспериментальные данные в БД и выводит актуальную информацию.', reply_markup=mainb)



# Определяем состояния
class DataInput(StatesGroup):
    waiting_for_data = State()


# Обработчик для начала ввода данных
@dp.message(F.text == 'Начать ввод данных')
async def into(message: types.Message, state: FSMContext):
    await message.answer("Введите все необходимые данные по очереди, отдельными сообщениями")
    await message.answer("Список требуемых характеристик, данные вводятся без указания единиц измерения, "
                         "но в размерности, соответсвующей таблице:")
    await message.answer_photo( photo=needs)
    global df  # Объявляем переменную df как глобальную, если это необходимо
    df = [0]
    await state.update_data(data_index=1)  # Начинаем со второго элемента списка
    await message.answer(f'Введите {needs_list[0]}')  # Сообщаем, что нужно ввести
    await state.set_state(DataInput.waiting_for_data)



@dp.message(F.text == 'Посмотреть графики')
async def send_graphs(message: types.Message):
    for i in (graphs):
        await message.answer_photo(photo=i)


@dp.message(DataInput.waiting_for_data)
async def handle_input(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    data_index = user_data["data_index"]

    # Сохраняем данные в список
    df.append(message.text)

    # Проверяем, есть ли еще элементы в needs_list
    if data_index < len(needs_list) - 1:  # Оставляем -1, чтобы исключить ввод для первого столбца
        next_index = data_index + 1
        await state.update_data(data_index=next_index)
        await message.answer(f'Введите {needs_list[next_index]}')  # Сообщаем следующий запрос
    else:
        # Все данные введены
        await state.clear()
        # Конвертируем список в DataFrame
        new_df = pd.DataFrame([df], columns=needs_list)
        # Сохранение DataFrame в файл (или в базу данных)
        new_df.to_csv(path.join('data', 'new'), index=False)
        await message.answer(f"Данные успешно введены. Графики обновятся через 10-20 секунд.")
        df.clear()



async def main():
    await dp.start_polling(bot)

def start_bot():
    logging.basicConfig(level=logging.INFO)
    # чисто для теста и дебагинга, потом удалять строку ту что выше
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Выход')

if __name__ == '__main__':
    start_bot()
