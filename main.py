import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from function import search_users, get_photo, sort_likes, json_create
from app_func import engine, Session, write_msg, register_user, add_user, add_user_photos, add_to_black_list, \
    check_db_user, check_db_black, check_db_favorites, check_db_master, delete_db_blacklist, delete_db_favorites
from config import comm_token
from sqlalchemy.exc import IntegrityError, InvalidRequestError

vk = vk_api.VkApi(token=comm_token)
longpoll = VkLongPoll(vk)
session = Session()
connection = engine.connect()


def loop_bot():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text, this_event.user_id


def menu_bot(id_num):
    write_msg(id_num,
              f"Привет, я бот - VKinder\n"
              f"\nЕсли вы тут впервые, необходимо пройти регистрацию ;)\n"
              f"Для регистрации введите - Зарегистрироваться\n"
              f"Если вы уже зарегистрированы - начинайте поиск.\n"
              f"\nДля поиска - девушка 18-35 В.Новгород\n"
              f"Для перехода в избранное нажмите - 2\n"
              f"Для перехода в черный список нажмите - 0\n")


def show_info():
    write_msg(user_id, f'Анкет больше нет'
                       f'Перейти в избранное - 2'
                       f'Перейти в черный список - 0'
                       f'Поиск - девушка 18-35 В.Новгород'
                       f'Меню бота - VKinder')


def reg_new_user(id_num):
    write_msg(id_num, 'Регистрация завершена')
    write_msg(id_num,
              f"VKinder - для активации бота\n")
    register_user(id_num)


def go_to_favorites(ids):
    alls_users = check_db_favorites(ids)
    write_msg(ids, f'Избранное:')
    for nums, users in enumerate(alls_users):
        write_msg(ids, f'{users.first_name}, {users.second_name}, {users.link}')
        write_msg(ids, '1 - Удалить из избранного, 0 - Далее \nq - Выход')
        msg_texts, user_ids = loop_bot()
        if msg_texts == '0':
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, f'Анкет больше нет\n'
                                    f'VKinder - меню\n')
        # для удаления избр.
        elif msg_texts == '1':
            delete_db_favorites(users.vk_id)
            write_msg(user_ids, f'Анкета удалена.')
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, f'Анкет больше нет\n'
                                    f'VKinder - меню\n')
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'VKinder - для активации бота.')
            break


def go_to_blacklist(ids):
    all_users = check_db_black(ids)
    write_msg(ids, f'Черный список:')
    for num, user in enumerate(all_users):
        write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
        write_msg(ids, '1 - Удалить из черного списка, 0 - Далее \nq - Выход')
        msg_texts, user_ids = loop_bot()
        if msg_texts == '0':
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Анкет больше нет\n'
                                    f'VKinder - меню\n')
        # должно удалять из бд - чс
        elif msg_texts == '1':
            print(user.id)
            delete_db_blacklist(user.vk_id)
            write_msg(user_ids, f'Анкета удалена')
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Анкет больше нет\n'
                                    f'VKinder - меню\n')
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'VKinder - для активации бота.')
            break


if __name__ == '__main__':
    while True:
        msg_text, user_id = loop_bot()
        if msg_text == "VKinder":
            menu_bot(user_id)
            msg_text, user_id = loop_bot()
            if msg_text.lower() == 'да':
                reg_new_user(user_id)
            elif len(msg_text) > 1:
                sex = 0
                if msg_text[0:7].lower() == 'девушка':
                    sex = 1
                elif msg_text[0:7].lower() == 'мужчина':
                    sex = 2
                age_at = msg_text[8:10]
                if int(age_at) < 18:
                    write_msg(user_id, 'Минимальный возраст - 18 лет!')
                    age_at = 18
                age_to = msg_text[11:14]
                if int(age_to) >= 100:
                    write_msg(user_id, 'Максимальный влзраст 99 лет')
                    age_to = 99
                city = msg_text[14:len(msg_text)].lower()

                # поиск
                result = search_users(sex, int(age_at), int(age_to), city)
                json_create(result)
                current_user_id = check_db_master(user_id)
                for i in range(len(result)):
                    dating_user, blocked_user = check_db_user(result[i][3])
                    user_photo = get_photo(result[i][3])
                    if user_photo == 'фото нет' or dating_user is not None or blocked_user is not None:
                        continue
                    sorted_user_photo = sort_likes(user_photo)

                    write_msg(user_id, f'\n{result[i][0]}  {result[i][1]}  {result[i][2]}', )
                    try:
                        write_msg(user_id, f'фото:',
                                  attachment=','.join
                                  ([sorted_user_photo[-1][1], sorted_user_photo[-2][1],
                                    sorted_user_photo[-3][1]]))
                    except IndexError:
                        for photo in range(len(sorted_user_photo)):
                            write_msg(user_id, f'фото:',
                                      attachment=sorted_user_photo[photo][1])
                    # после поиска
                    write_msg(user_id, '1 - Добавить, 2 - Заблокировать, 0 - Далее, \nq - выход')
                    msg_text, user_id = loop_bot()
                    if msg_text == '0':
                        if i >= len(result) - 1:
                            show_info()

                    elif msg_text == '1':
                        if i >= len(result) - 1:
                            show_info()
                            break
                        # для добавления в бд + фото
                        try:
                            add_user(user_id, result[i][3], result[i][1],
                                     result[i][0], city, result[i][2], current_user_id.id)
                            add_user_photos(user_id, sorted_user_photo[0][1],
                                            sorted_user_photo[0][0], current_user_id.id)
                        except AttributeError:
                            write_msg(user_id, 'Вы зарегистрированы!\n Введите VKinder для перезагрузки бота')
                            break
                    # для ЧС
                    elif msg_text == '2':
                        if i >= len(result) - 1:
                            show_info()
                        add_to_black_list(user_id, result[i][3], result[i][1],
                                          result[i][0], city, result[i][2],
                                          sorted_user_photo[0][1],
                                          sorted_user_photo[0][0], current_user_id.id)
                    elif msg_text.lower() == 'q':
                        write_msg(user_id, 'Введите VKinder для активации бота')
                        break

            # избранное
            elif msg_text == '2':
                go_to_favorites(user_id)

            # в ЧС
            elif msg_text == '0':
                go_to_blacklist(user_id)