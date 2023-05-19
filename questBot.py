import telebot
import configparser
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup #States
from geopy.distance import geodesic as GD
import os
import logger
log = logger.log
logCB = logger.logCB
try:
    os.mkdir('log')
except Exception as err:
    print(err)

from telebot.storage import StateMemoryStorage

state_storage = StateMemoryStorage()

config = configparser.ConfigParser()
config.read('info.ini')
statCfg = configparser.ConfigParser()
statCfg.read('stat.ini')
try:
    config.add_section("commands")
except Exception as err:
    print(err)
try:
    config.add_section("users")
except Exception as err:
    print(err)
try:
    config.add_section("uLevel")
except Exception as err:
    print(err)
try:
    statCfg.add_section("members")
except Exception as err:
    print(err)
with open('info.ini', 'w') as config_file:
        config.write(config_file)
with open('stat.ini', 'w') as config_file:
        statCfg.write(config_file)

bot = telebot.TeleBot('', state_storage=state_storage)

class MyStates(StatesGroup):
    # Just name variables differently
    setPoints = State()
    setPosAdm = State()
    inGameLoc = State()
    inGameQ = State()
    inGameA = State()
    setQ = State()
    setA = State()
    setCmd = State()

class Loc:
    def __init__(self, cNum, pNum):
        self.cNum = cNum
        self.pNum = pNum

point_dict = {}
user_level_dict = {}

class IsAdmin(telebot.custom_filters.SimpleCustomFilter):
    key='is_admin'
    @staticmethod
    def check(message: telebot.types.Message):
        admins = []
        try:
            admins = statCfg.options('admins')
        except Exception as err:
            print(err)
        try: 
            if str(message.chat.id) in admins:
                return True
            else:
                return False
        except Exception:
            if str(message.from_user.id) in admins:
                return True
            else:
                return False

class IsGE(telebot.custom_filters.SimpleCustomFilter):
    key='is_ge'
    @staticmethod
    def check(message: telebot.types.Message):
        if (config.get('settings', 'enable') == 'True'):
            return True
        else:
            return False

@bot.message_handler(commands=['start'])
def start(m):
    log(m)
    if (config.get('settings', 'enable')=='False'):
        bot.send_message(m.chat.id, 'Игра ещё не началась')
        return
    try:
        statCfg.set('members', str(m.chat.id), f'{m.from_user.first_name} {m.from_user.last_name} ({m.from_user.username})')
    except Exception as err:
        print(err)
    with open('stat.ini', 'w') as config_file:
        statCfg.write(config_file)
    if (config.has_option('users', str(m.chat.id))):
        bot.send_message(m.chat.id, f'Ты уже выбрал(а) команду! Твоя команда - {config.get("users", str(m.chat.id))}\nДля помощи - /help', reply_markup=types.ReplyKeyboardRemove())
        sendLocToUser(m, False)
        return
    opt = config.options('commands')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in range(len(opt)):
         optRes = config.getboolean("commands", f'c_{i+1}')
         if (optRes):
            markup.add(types.InlineKeyboardButton(f'Команда {i+1}', callback_data=f'c_{i+1}'))
    bot.send_message(m.chat.id, 'Добро пожаловать! Выбире команду.\nДля помощи - /help', reply_markup=markup)

@bot.message_handler(content_types=['location'], state=MyStates.setPosAdm)
def setPosAdmLoc(m):
    lat = 0
    lon = 0
    # print(m)
    bot.delete_message(m.chat.id, m.message_id)
    try:
        cNum = point_dict[m.chat.id].cNum
        pNum = point_dict[m.chat.id].pNum
        lat = m.location.latitude
        lon = m .location.longitude
        config.set(f'c_{cNum}', f'pLat_{pNum}', str(lat))
        config.set(f'c_{cNum}', f'pLon_{pNum}', str(lon))
        with open('info.ini', "w") as config_file:
            config.write(config_file)
        bot.send_message(m.chat.id, f'Точка №{pNum} успешно установлена для команды №{cNum}')
        bot.delete_state(m.from_user.id, m.chat.id)
    except Exception as err:
        print(err)
    
@bot.message_handler(content_types=['text'], state=MyStates.setQ)
def setQ(m):
    log(m)
    cNum = point_dict[m.chat.id].cNum
    pNum = point_dict[m.chat.id].pNum
    config.set(f'c_{cNum}', f'q_{pNum}', m.text)
    with open('info.ini', "w") as config_file:
            config.write(config_file)
    bot.set_state(m.chat.id, MyStates.setA, m.from_user.id)
    bot.send_message(m.chat.id, 'Вопрос принят. Напиши ответ.')

@bot.message_handler(content_types=['text'], state=MyStates.setA)
def setA(m):
    log(m)
    cNum = point_dict[m.chat.id].cNum
    pNum = point_dict[m.chat.id].pNum
    config.set(f'c_{cNum}', f'a_{pNum}', m.text)
    with open('info.ini', "w") as config_file:
            config.write(config_file)
    bot.delete_state(m.chat.id, m.from_user.id)
    bot.send_message(m.chat.id, 'Ответ принят. Процесс добавления вопроса завершён.')

@bot.message_handler(content_types=['location'], state=MyStates.inGameLoc, is_ge=True)
def checkLoc(m):
    bot.delete_message(m.chat.id, m.message_id)
    if (m.location.live_period is None):
        bot.send_message(m.chat.id, "Не удалось подтвердить подлинность локации. Отправь трансляцию геолокации.")
        return
    uLevel = 0
    uCom = 0
    try:
        uLevel = config.get('uLevel', str(m.chat.id))
    except Exception:
        uLevel = 1
    try:
        uCom = config.get('users', str(m.chat.id))
    except Exception as err:
        print(err)
    lat = config.get(f'c_{uCom}', f'pLat_{uLevel}')
    lon = config.get(f'c_{uCom}', f'pLon_{uLevel}')
    point = (lat, lon)
    user_xy = (m.location.latitude, m.location.longitude)
    if getDist(point=point, user_xy=user_xy) < 50:
        print('GOOD')
        bot.set_state(m.chat.id, MyStates.inGameQ, m.from_user.id)
        sendQ(m)
    else:
        bot.send_message(m.chat.id, 'Ты ещё не находишься в точке.')

@bot.message_handler(content_types=['location'], state=MyStates.inGameLoc, is_ge=False)
def checkLoc(m):
    log(m)
    bot.send_message(m.chat.id, 'Игра уже завершена.')
    bot.delete_state(m.from_user.id, m.chat.id)

def sendQ(m):
    log(m)
    uLevel = 0
    uCom = 0
    try:
        uLevel = config.get('uLevel', str(m.chat.id))
    except Exception as err:
        print(err)
        uLevel = 1
    try:
        uCom = config.get('users', str(m.chat.id))
    except Exception as err:
        print(err)
    q = config.get(f'c_{uCom}', f'q_{uLevel}')
    bot.send_message(m.chat.id, q)
    bot.set_state(m.chat.id, MyStates.inGameA, m.from_user.id)

def sendLocToUser(m, flag):
    uLevel = 0
    uCom = 0
    try:
        uLevel = config.get('uLevel', str(m.chat.id))
    except Exception as err:
        print(err)
        uLevel = 1
    try:
        uCom = config.get('users', str(m.chat.id))
    except Exception as err:
        print(err)
    bot.set_state(m.chat.id, MyStates.inGameLoc, m.from_user.id)
    points = int(config.get('settings', 'points'))
    if (int(uLevel) > points):
        bot.send_message(m.chat.id, 'Поздравляю! Игра завершена, ты прибыл на последнюю точку.')
        return
    else:
        if (flag):
            bot.send_message(m.chat.id, 'Ответ верный. Сейчас тебе будет отправлена геолокация следующей точки.')
    lat = config.get(f'c_{uCom}', f'pLat_{uLevel}')
    lon = config.get(f'c_{uCom}', f'pLon_{uLevel}')
    bot.send_location(m.chat.id, latitude=lat, longitude=lon)

@bot.message_handler(content_types=['text'], state=MyStates.inGameA, is_ge=True)
def checkA(m):
    log(m)
    uLevel = 0
    uCom = 0
    try:
        uLevel = config.get('uLevel', str(m.chat.id))
    except Exception as err:
        print(err)
        uLevel = 1
    try:
        uCom = config.get('users', str(m.chat.id))
    except Exception as err:
        print(err)
    a = config.get(f'c_{uCom}', f'a_{uLevel}')
    if (a.lower() == m.text.lower()):
        uLevel = int(uLevel)+1
        uLevel = str(uLevel)
        config.set('uLevel', str(m.chat.id), uLevel)
        with open('info.ini', 'w') as config_file:
            config.write(config_file)
        sendLocToUser(m, True)
    else:
        bot.send_message(m.chat.id, 'Ответ неверный! Попробуй ещё.')

@bot.message_handler(content_types=['text'], state=MyStates.inGameA, is_ge=False)
def checkA(m):
    log(m)
    bot.send_message(m.chat.id, 'Игра уже завершена.')
    bot.delete_state(m.from_user.id, m.chat.id)

@bot.callback_query_handler(func=lambda call: True, is_ge=True)
def callback_query(call):
    logCB(call)
    bot.delete_message(call.from_user.id, call.message.id)
    try:
        if (call.data.split('_')[0] == 'c'):
            if (config.get('commands', call.data) == 'False'):
                bot.send_message(call.from_user.id, 'Невозможно выбрать эту команду, потому что её выбрал уже кто-то другой.')
                return
            config.set('users', str(call.from_user.id), call.data.split('_')[1])
            config.set('commands', call.data, 'False')
            config.set('uLevel', str(call.from_user.id), '1')
            with open('info.ini', "w") as config_file:
                config.write(config_file)
            bot.send_message(call.from_user.id, 'Команда выбрана. Сейчас тебе будет отправлена геопозиция первой точки. Когда придёшь на неё, отправь свою локацию, чтобы получить вопрос')
            uLevel = 0
            uCom = 0
            try:
                uLevel = config.get('uLevel', str(call.from_user.id))
            except Exception:
                uLevel = 1
            try:
                uCom = config.get('users', str(call.from_user.id))
            except Exception:
                pass
            lat = config.get(f'c_{uCom}', f'pLat_{uLevel}')
            lon = config.get(f'c_{uCom}', f'pLon_{uLevel}')
            bot.send_location(call.from_user.id, latitude=lat, longitude=lon)
            bot.set_state(call.from_user.id, MyStates.inGameLoc, call.from_user.id)
        if(call.data == 'dis_yes'):
            config.set('settings', 'enable', 'False')
            with open('info.ini', 'w') as config_file:
                config.write(config_file)
            bot.send_message(call.from_user.id, 'Игра завершена')
        if(call.data == 'dis_no'):
            bot.send_message(call.from_user.id, 'Игра продолжается')
    except Exception as err:
        print(err)

@bot.callback_query_handler(func=lambda call: True, is_admin=True, is_ge=False)
def callback_query(call):
    logCB(call)
    try:
        if (call.data.split('_')[0] == 'v'):
            markup = types.InlineKeyboardMarkup(row_width=1)
            uCom = call.data.split('_')[1]
            markup.add(types.InlineKeyboardButton('Точки', callback_data=f's_{uCom}'), types.InlineKeyboardButton('Вопросы/ответы', callback_data=f'qa_{uCom}'))
            bot.send_message(call.from_user.id, 'Выберите', reply_markup=markup)
        if (call.data.split('_')[0] == 's'):
            points = int(config.get('settings', 'points'))
            markup = types.InlineKeyboardMarkup(row_width=1)
            cNum = call.data.split('_')[1]
            for i in range(points):
                markup.add(types.InlineKeyboardButton(f'Точка {i+1}', callback_data=f'g_{str(cNum)}_{i+1}'))
            bot.delete_message(call.from_user.id, call.message.id)
            bot.send_message(call.from_user.id, 'Выберите точку', reply_markup=markup)
        if (call.data.split('_')[0] == 'g'):
            cNum = 0
            pNum = 0
            try:
                cNum = str(call.data.split('_')[1])
                pNum = str(call.data.split('_')[2])
                loc = Loc(cNum, pNum)
                point_dict[call.from_user.id] = loc
                config.add_section(f'c_{cNum}')
            except Exception as err:
                pass
            bot.delete_message(call.from_user.id, call.message.id)
            bot.send_message(call.from_user.id, 'Отправь геолокацию точки')
            bot.set_state(call.from_user.id, MyStates.setPosAdm, call.from_user.id)
        if (call.data.split('_')[0] == 'qa'):
            points = int(config.get('settings', 'points'))
            markup = types.InlineKeyboardMarkup(row_width=1)
            cNum = call.data.split('_')[1]
            for i in range(points):
                markup.add(types.InlineKeyboardButton(f'Вопрос {i+1}', callback_data=f'q_{str(cNum)}_{i+1}'))
            bot.delete_message(call.from_user.id, call.message.id)
            bot.send_message(call.from_user.id, 'Выберите вопрос', reply_markup=markup)
        if (call.data.split('_')[0] == 'q'):
            bot.set_state(call.from_user.id, MyStates.setQ, call.from_user.id)
            cNum = str(call.data.split('_')[1])
            pNum = str(call.data.split('_')[2])
            loc = Loc(cNum, pNum)
            point_dict[call.from_user.id] = loc
            bot.send_message(call.from_user.id, 'Напиши вопрос')
        if (call.data == 'points'):
            mesg = bot.send_message(call.from_user.id, 'Введите количество точек')
            bot.set_state(call.from_user.id, MyStates.setPoints, call.from_user.id)
            bot.delete_message(call.from_user.id, call.message.id)
        if (call.data == 'cfg'):
            f = open('info.ini', 'r')
            bot.send_message(call.from_user.id, f.read())
        if (call.data == 'cmd'):
            bot.send_message(call.from_user.id, 'Введите количество команд')
            bot.set_state(call.from_user.id, MyStates.setCmd, call.from_user.id)
            bot.delete_message(call.from_user.id, call.message.id)
    except Exception as err:
        print(err)
        
@bot.message_handler(content_types=['text'], state=MyStates.setPoints, is_digit=True)
def setPoint(m):
    log(m)
    config.set('settings', 'points', m.text)
    with open('info.ini', 'w') as config_file:
        config.write(config_file)
    bot.delete_state(m.from_user.id, m.chat.id)
    bot.send_message(m.chat.id, 'Количество точек настроено.')
@bot.message_handler(content_types=['text'], state=MyStates.setPoints, is_digit=False)
def setPoint(m):
    bot.send_message(m.chat.id, 'Укажите целое значение')
    bot.delete_state(m.from_user.id, m.chat.id)

@bot.message_handler(content_types=['text'], state=MyStates.setCmd, is_digit=True)
def run(m):
    log(m)
    try:
        config.add_section('commands')
    except Exception as err:
        print(err)
    count = int(m.text)
    for i in range(count):
        config.set('commands', f'c_{i+1}', "True")
    with open('info.ini', "w") as config_file:
        config.write(config_file)
    bot.delete_state(m.chat.id, m.from_user.id)
    bot.send_message(m.chat.id, 'Количество команд настроено.')

@bot.message_handler(commands=['clear'], is_admin=True, is_ge=False)
def clearCfg(m):
    log(m)
    arg = ''
    try:
        arg = m.text.split(' ')
    except Exception as err:
        print(err)
    try:
        if ("cmd" in arg[1]):
            try:
                if (arg[2]):
                    config.set('commands', f'c_{arg[2]}', 'True')
                    uOpt = config.options('users')
                    for uO in uOpt:
                        if (config.get('users', uO) == arg[2]):
                            config.remove_option('users', uO)
                            config.remove_option('uLevel', uO)
                    with open('info.ini', 'w') as config_file:
                        config.write(config_file)
                    bot.send_message(m.chat.id, f'Команда №{arg[2]} обнулена')
                    return
            except Exception as err:
                print(err)
            opt = config.options('commands')
            for o in opt:
                config.remove_section(o)
            config.remove_section('commands')
            config.add_section("commands")   
            config.remove_section('users')
            config.add_section("users")
            config.remove_section('uLevel')
            config.add_section("uLevel")
            with open('info.ini', 'w') as config_file:
                config.write(config_file)
            members = statCfg.options('members')
            for id in members:
                bot.delete_state(int(id), int(id))
            bot.send_message(m.chat.id, f'Команды обнулены')
            return
    except Exception as err:
        print(err)
        opt = config.options('commands')
        for o in opt:
            config.remove_section(o)
        config.remove_section('commands')
        config.add_section("commands")
        config.remove_section('users')
        config.add_section("users")
        config.remove_section('uLevel')
        config.add_section("uLevel")
        config.remove_option('settings', 'points')
        members = statCfg.options('members')
        for id in members:
            bot.delete_state(int(id), int(id))
        with open('info.ini', 'w') as config_file:
            config.write(config_file)
    bot.send_message(m.chat.id, 'Очистка игры выполнена!')

@bot.message_handler(commands=['clear'], is_admin=True, is_ge=True)
def clearCfg(m):
    log(m)
    arg = ''
    try:
        arg = m.text.split(' ')
    except Exception as err:
        print(err)
    try:
        if ("cmd" in arg[1]):
            try:
                if (arg[2]):
                    config.set('commands', f'c_{arg[2]}', 'True')
                    uOpt = config.options('users')
                    for uO in uOpt:
                        if (config.get('users', uO) == arg[2]):
                            config.remove_option('users', uO)
                            config.remove_option('uLevel', uO)
                    with open('info.ini', 'w') as config_file:
                        config.write(config_file)
                    bot.send_message(m.chat.id, f'Команда №{arg[2]} обнулена')
                    return
            except Exception as err:
                print(err)
            bot.send_message(m.chat.id, 'Сначала выключите игру.')
            return
    except Exception as err:
        print(err)
    bot.send_message(m.chat.id, 'Сначала выключите игру.')

@bot.message_handler(commands=['set'], is_admin=True, is_ge=False)
def set(m):
    log(m)
    opt = config.options('commands')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in range(len(opt)):
        markup.add(types.InlineKeyboardButton(f'Команда {i+1}', callback_data=f'v_{i+1}'))
    markup.add(types.InlineKeyboardButton('Количество точек', callback_data='points'))
    markup.add(types.InlineKeyboardButton('Количество команд', callback_data='cmd'))
    markup.add(types.InlineKeyboardButton('Конфиг-ФАЙЛ', callback_data='cfg'))
    game_status = ''
    if (config.get('settings', 'enable') == 'True'):
        game_status = 'ВКЛЮЧЕНА'
    else:
        game_status = 'ВЫКЛЮЧЕНА'
    bot.send_message(m.chat.id, f'*!!!Стаус игры - {game_status}*\nВыбире команду для настройки', reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['set'], is_admin=True, is_ge=True)
def set(m):
    log(m)
    bot.send_message(m.chat.id, 'Сначала выключите игру.')

def getDist(point, user_xy):
    dist = GD(point, user_xy).m
    return dist

@bot.message_handler(commands=['help'], is_admin=True)
def help(m):
    log(m)
    bot.send_message(m.chat.id, 'Команды:\n/start - выбрать команду\n/set - настройки игры\n/clear - очистить игру(очистить конфиг-файл)\n/clear cmd - очистить данные игровых команд\n/clear cmd 1 - очистить данные команды №1\n/en - запустить игру\n/dis - завершить игру')

@bot.message_handler(commands=['help'], is_admin=False)
def help(m):
    log(m)
    bot.send_message(m.chat.id, 'Команды:\n/start - выбрать команду')

@bot.message_handler(commands=['en'], is_admin=True, is_ge=False)
def en(m):
    log(m)
    points = config.has_option('settings', 'points')
    commands = config.options('commands')
    isHasComSec = True
    yesPoints = True
    yesQ = True
    for c in commands:
        isHasComSec = config.has_section(c)
        try:
            pc = int(config.get('settings', 'points'))
            for i in range(pc):
                if config.has_option(c, f'pLat_{i+1}') is False or config.has_option(c, f'pLon_{i+1}') is False:
                    yesPoints = False
                if config.has_option(c, f'q_{i+1}') is False or config.has_option(c, f'a_{i+1}') is False:
                    yesQ = False
        except Exception as err:
            print(err)
    if (points is False):
        bot.send_message(m.chat.id, 'Игра не до конца настроена. Не установлено количество точек')
        return
    if (len(commands) == 0):
        bot.send_message(m.chat.id, 'Игра не до конца настроена. Не установлено количество команд.')
        return
    if (isHasComSec is False):
        bot.send_message(m.chat.id, 'Игра не до конца настроена. Не настроена одна из команд')
        return
    if (yesQ is False):
        bot.send_message(m.chat.id, 'Игра не до конца настроена. Не все вопросы настроены. Посмотреть какие можно в конфиг-файле.')
        return
    if (yesPoints is False):
        bot.send_message(m.chat.id, 'Игра не до конца настроена. Не все точки настроены. Посмотреть какие можно в конфиг-файле.')
        return
    config.set('settings', 'enable', 'True')
    with open('info.ini', 'w') as config_file:
        config.write(config_file)
    bot.send_message(m.chat.id, 'Игра началась')

@bot.message_handler(commands=['en'], is_admin=True, is_ge=True)
def en(m):
    bot.send_message(m.chat.id, 'Игра уже идёт')

@bot.message_handler(commands=['dis'], is_admin=True, is_ge=True)
def en(m):
    log(m)
    users = config.options('users')
    points = int(config.get('settings', 'points'))
    allEnds = True
    for u in users:
        if (int(config.get('uLevel', u))<points+1):
            allEnds = False
    if (allEnds is False):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton('Да', callback_data='dis_yes'), types.InlineKeyboardButton('Нет', callback_data='dis_no'))
        bot.send_message(m.chat.id, 'Не все игроки завершили игру. Вы уверены, что хотите завершить игру?', reply_markup=markup)
        return
    config.set('settings', 'enable', 'False')
    with open('info.ini', 'w') as config_file:
        config.write(config_file)
    bot.send_message(m.chat.id, 'Игра завершена')

@bot.message_handler(commands=['dis'], is_admin=True, is_ge=False)
def dis(m):
    bot.send_message(m.chat.id, 'Игра уже завершена')

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.add_custom_filter(IsAdmin())
bot.add_custom_filter(IsGE())
bot.enable_saving_states()
bot.infinity_polling(skip_pending=True)