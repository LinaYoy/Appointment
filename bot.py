import json
import os
from telebot import TeleBot, types
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Получаем токен бота и ID пользователя из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

bot = TeleBot(BOT_TOKEN)

def load_doctors():
    with open('data/doctors.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_appointment(appointment):
    with open('data/appointments.txt', 'a', encoding='utf-8') as f:
        f.write(appointment + '\n')

def remove_time_from_availability(doctor_name, time):
    doctors = load_doctors()
    if doctor_name in doctors:
        if time in doctors[doctor_name]["availability"]:
            doctors[doctor_name]["availability"].remove(time)
            with open('data/doctors.json', 'w', encoding='utf-8') as f:
                json.dump(doctors, f, ensure_ascii=False, indent=4)

doctors = load_doctors()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Записаться к стоматологу")
    item2 = types.KeyboardButton("Показать мои записи")
    markup.add(item1, item2)
    bot.reply_to(message, "Привет! Как я могу помочь?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Записаться к стоматологу")
def appointment(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    today = datetime.now(timezone.utc).date()
    for i in range(7):
        future_date = today + timedelta(days=i)
        markup.add(future_date.strftime('%Y-%m-%d'))
    
    markup.add("Назад")
    bot.reply_to(message, "Выберите дату:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in [(datetime.now(timezone.utc).date() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)])
def choose_date(message):
    selected_date = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    for doctor in doctors:
        markup.add(doctor)
        
    markup.add("Назад")
    bot.reply_to(message, f"Выберите стоматолога для {selected_date}:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in doctors)
def choose_doctor(message):
    selected_doctor = message.text
    doctor_data = doctors[selected_doctor]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    available_times = [time for time in doctor_data["availability"] if time not in get_booked_times(selected_doctor)]
    for time in available_times:
        markup.add(time)
        
    markup.add("Назад")
    bot.reply_to(message, f"Доступное время для {selected_doctor}:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    send_welcome(message)

def get_booked_times(doctor_name):
    booked_times = []
    with open('data/appointments.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if doctor_name in line:  
                booked_times.append(line.split()[-1])  
    return booked_times

@bot.message_handler(func=lambda message: message.text in [time for doctor in doctors.values() for time in doctor["availability"]])
def choose_time(message):
    selected_time = message.text
    selected_doctor = next(doctor for doctor in doctors if message.text in doctors[doctor]["availability"])

    appointment_info = f'{message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} {selected_doctor} {selected_time}'
    save_appointment(appointment_info)

    remove_time_from_availability(selected_doctor, selected_time)
    
    bot.reply_to(message, f"Вы успешно записаны к {selected_doctor} на {selected_time}!")

@bot.message_handler(func=lambda message: message.text == "Показать мои записи")
def show_appointments(message):
    user_id = message.from_user.id
    appointments = []
    
    with open('data/appointments.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if str(user_id) in line:
                appointments.append(line.strip())
    
    if appointments:
        reply = "Ваши записи:\n" + "\n".join(appointments)
    else:
        reply = "У вас пока нет записей."
    
    bot.reply_to(message, reply)

bot.polling(none_stop=True)