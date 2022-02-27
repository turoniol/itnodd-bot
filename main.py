from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from config import TOKEN
from gamer import *
from game_state import GameState

answers = list()
gamers = dict()
LEADER = Gamer()
ANSWER = Answer()
WORD = str()

CHAT_ID = 0

state = GameState()


def start(update: Update, context: CallbackContext) -> None:
    global state, CHAT_ID
    if state.start():
        update.message.reply_text('Гру вже розпочато.')
        return
    if len(context.args) == 0:
        update.message.reply_text('Введіть слово після команди: /start *ваше слово*')
        return

    user = update.message.from_user
    CHAT_ID = update.message.chat_id

    state.state = GameState.START

    uid = user['id']
    gamers[uid] = Gamer(uid=uid, user=user, role=Role.LEADER)
    global LEADER
    LEADER = gamers[uid]

    word = ' '.join(context.args)
    global WORD
    WORD = word

    update.message.reply_text(f'Слово: {word}')
    context.bot.send_message(chat_id=uid,
                             text='Ви ведучий. Додайте правильну відповідь через: /answer *правильна відповідь*')


def answer(update: Update, context: CallbackContext) -> None:
    global state
    if state.stop():
        update.message.reply_text('Гру не розпочато.')
        return
    user = update.message.from_user
    global gamers
    gamer = gamers[user['id']]
    if not gamer.is_leader():
        update.message.reply_text('Ви не ведучий.')
        return
    if len(context.args) == 0:
        update.message.reply_text('Введіть відповідь після команди: /answer *ваше слово*')
        return

    global ANSWER, answers
    ans = ' '.join(context.args)
    ANSWER = Answer(aid=-1, text=ans)
    answers.append(ANSWER)
    update.message.reply_text(f'Відповідь: {ANSWER.text}')


def text(update: Update, context: CallbackContext) -> None:
    global state
    if state.stop():
        update.message.reply_text('Гру не розпочато.')
        return

    text_received = update.message.text
    user = update.message.from_user
    uid = user['id']
    global gamers
    if uid not in gamers.keys():
        gamers[uid] = Gamer(uid=uid, user=user)
    gamer = gamers[uid]

    if state.start():
        text_answering(update, text_received, gamer, context)
    elif state.voting():
        if gamer.is_leader():
            update.message.reply_text('Ведучий не може голосувати.')
            return
        text_voting(update, text_received, gamer, context)


def text_answering(update: Update, text_received, gamer, context) -> None:
    prepared = prepare_text(text_received)
    gamer.answer = Answer(aid=gamer.id, text=prepared)
    update.message.reply_text(f'Ваш варіант: "{prepared}".')
    global LEADER
    context.bot.send_message(chat_id=LEADER.id,
                             text=f'Гравець {gamer.username()} ввів свій варіант відповіді.')


def prepare_text(text_received: str) -> str:
    s = text_received[0].upper() + text_received[1:]
    last = '.' if text_received[-1] != '.' else ' '
    return s + last


def text_voting(update: Update, text_received, gamer, context) -> None:
    try:
        vid = int(text_received) - 1
        answers[vid].votes.add(gamer.id)
        context.bot.send_message(chat_id=LEADER.id,
                                 text=f'Гравець {gamer.username()} проголосував.')
    except:
        error(update, context)


def show(update: Update, context: CallbackContext) -> None:
    global state, ANSWER
    if state.stop():
        update.message.reply_text('Гру не розпочато.')
        return
    user = update.message.from_user
    global gamers
    gamer = gamers[user['id']]
    if not gamer.is_leader():
        update.message.reply_text('Ви не ведучий.')
        return
    if len(ANSWER.text) == 0:
        update.message.reply_text('Не введено відповідь.')
        return

    global answers, gamers
    for g in gamers:
        if g.answer.empty():
            continue
        answers.append(g.answer)
    answers.sort(key=lambda x: x.text)

    msg = prepare_msg()
    button_list = [KeyboardButton(str(i + 1)) for i in range(len(answers))]

    global WORD
    state.state = GameState.VOTING
    for gs in gamers.values():
        if gs.is_leader():
            continue
        context.bot.send_message(chat_id=gs.id, text=f'Слово: {WORD}')
        context.bot.send_message(chat_id=gs.id, text=msg, reply_markup=ReplyKeyboardMarkup([button_list]))


def prepare_msg() -> str:
    global answers
    counter = 1
    msg = str()
    for a in answers:
        msg += f'{counter}. {a.text}\n'
        counter += 1
    return msg


def end(update: Update, context: CallbackContext) -> None:
    global state
    if state.stop():
        update.message.reply_text('Гру не розпочато.')
        return
    global ANSWER
    context.bot.send_message(chat_id=CHAT_ID, text=f'Правильна відповідь: "{ANSWER.text}".')

    global answers
    answers_sorted = list(answers)
    answers_sorted.sort(key=lambda x: x.votes,
                        reverse=True)

    global gamers
    msg = str()
    for ans in answers_sorted:
        author = 'Ведучий' if ans.is_right() else gamers[ans.authorID].username()
        msg += f'{author}: {ans.text}: {ans.votes_count()}\n'
    answers = list()
    gamers = dict()
    state.state = GameState.STOP
    context.bot.send_message(chat_id=CHAT_ID, text=msg)


def error(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Щось мені не добре :(')


def main():
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('show', show))
    dispatcher.add_handler(CommandHandler('end', end))
    dispatcher.add_handler(CommandHandler('answer', answer))
    dispatcher.add_handler(MessageHandler(Filters.text, text))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
