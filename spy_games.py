import json
import requests

import time
start_time = time.time()

from datetime import datetime
st_time = datetime.now()

import sys

class SpyGames:
    api_url = 'https://api.vk.com/method/'
    params = {
        'access_token': 'ed1271af9e8883f7a7c2cefbfddfcbc61563029666c487b2f71a5227cce0d1b533c4af4c5b888633c06ae',
        'v': '5.92',
    }

    def __init__(self, valid_user_id):

        # Проверка на валидность пользователя
        if not valid_user_id.isdecimal():
            params = self.params.copy()
            params['users_id'] = valid_user_id
            valid_user_id = requests.get(self.format_url('users.get'), params=params).json()['response'][0]['id']

        self.user_id = valid_user_id

    # Фрматирование пути url-method ( https://api.vk.com/method//friends.get )
    def format_url(self, method_name):
        return f'{self.api_url}/{method_name}'

    # Выполнение запроса методов
    def make_request_method(self, method_name, user_id=None):
        method_url = self.format_url(method_name)

        params = self.params.copy()
        params['user_id'] = user_id or self.user_id

        result = requests.get(method_url, params=params).json()
        time.sleep(0.35)

        return result

    # Метод для выбора друзей пользователя
    def get_friends(self, ):
        return self.make_request_method('friends.get')

    # Метод для выбора групп пользователя и его друзей
    def get_groups(self, user_id=None):
        return self.make_request_method('groups.get', user_id)

    # Метод для выбора информации о группах
    def get_groups_info(self, group_ids):
        method_url = self.format_url('groups.getById')
        params = self.params.copy()
        params['fields'] = 'members_count'
        params['group_ids'] = ','.join(map(str, group_ids))

        result = requests.get(method_url, params=params).json()
        time.sleep(0.35)

        return result

    # Запись прмежуточных данных (тест)
    def write_json(self, data, filename):
        with open(filename, 'w', encoding='utf8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)


class GroupsInfo:

    def __init__(self, group):
        self.group = group

    def group_object_factory(self, group, members_count=None):
        if members_count == 'members_count':
            members_count = 0
        else:
            members_count = group['members_count']

        return {
            'name': group['name'],
            'gid': group['id'],
            'members_count': members_count,
        }


def main():
    result_file_name = 'groups.json'
    enter_value = input('\nВведите имя (eshmargunov) или id (171691064, 2916602, 197587476, 135653306) пользователя,'
                        ' для выхода - введите q: ')

    execute_time_code = (time.time() - start_time)
    print('\nВремя выполнения кода: {:.2f} секунд '.format(execute_time_code))

    if enter_value.lower() == 'q':
        return

    if len(enter_value) > 1:
        spy_games = SpyGames(enter_value)

        # Выбор всех друзей пользователя
        friends_response = spy_games.get_friends()
        friends_list = []
        try:
            if friends_response['response']['items']:
                friends_list = friends_response['response']['items']
                print('\nСписок друзей пользователя, всего - {}: '.format(len(friends_list)))
        except KeyError:
            if friends_response['error']['error_code'] == 30:
                print('Error = {} Закрытый профиль'.format(friends_response['error']['error_code']))
                sys.exit()
            else:
                print('Unknown error = {} '.format(friends_response))
                sys.exit()

        print('\nПоиск групп ...')

        # Выбор групп, в которых присутствует пользователь
        groups_response = spy_games.get_groups()
        groups_user_list = set(groups_response['response']['items'])
        print('\nСписок групп, в которых присутствует пользователь, всего - {}:'.format(len(groups_user_list)))

        print('\nПоиск и объединение групп, в которых присутствуют друзья пользователя...')
        groups_friends = set()

        for i, friend_id in enumerate(friends_list):
            time_left = execute_time_code - (i / len(friends_list) * execute_time_code)
            execute_left = 100 - (i / len(friends_list) * 100)
            print('  Осталось обработать: {:.2f}% - {} друзей'.format(execute_left, len(friends_list) - i))
            print('                       {:.2f} секунд '.format(time_left))

            response = spy_games.get_groups(friend_id)

            try:
                if response['response']['items']:
                    groups_friend = response['response']['items']
                    groups_friends.update(groups_friend)
            except KeyError:
                if response['error']['error_code'] == 7:
                    # print('Error = {} нет прав '.format(response['error']['error_code']))
                    pass
                elif response['error']['error_code'] == 18:
                    # print('Error = {} страница удалена или заблокирована'.format(response['error']['error_code']))
                    pass
                elif response['error']['error_code'] == 30:
                    # print('Error = {} This profile is private'.format(response['error']['error_code']))
                    pass
                elif response['error']['error_code'] == 6:
                    # print('Error = слишком много запросов в секунду '.format(response['error']['error_code']))
                    time.sleep(0.35)
                    continue
                else:
                    print('Error: {} '.format(response['error']['error_code']))
                    print('Error: {} '.format(response))
        print('  Сформированно множество, в которое входит {} групп :'.format(len(groups_friends)))

        print('\nПодводим итоги ...')

        intersection_groups = set.intersection(groups_user_list, groups_friends)
        print('\nСписок групп, в которых есть и пользователь и его общиие друзья, всего - {}:'
              '\n{}'.format(len(intersection_groups), intersection_groups))

        unique_groups = set.difference(groups_user_list, intersection_groups)
        print('\nСписок групп, в которых состоит пользователь, но не состоит никто из его друзей, всего - {}:'
              '\n{}'.format(len(unique_groups), unique_groups))

        result = list()
        if len(unique_groups):
            unique_groups_info = spy_games.get_groups_info(unique_groups)['response']
            spy_games.write_json(unique_groups_info, 'unique_groups_info.json')

            for group in unique_groups_info:
                groups_info = GroupsInfo(group)
                try:
                    format_group_info = groups_info.group_object_factory(group)
                    result.append(format_group_info)
                except KeyError:
                    if 'members_count' not in group:
                        format_group_info = groups_info.group_object_factory(group, 'members_count')
                        result.append(format_group_info)

        for i, result_list in enumerate(result, 1):
            print('  ', i, result_list)

        with open(result_file_name, 'w', encoding='utf8') as file:
            file.write(json.dumps(result, ensure_ascii=False, indent=2))
            print(f'\nРезультат записан в файл {result_file_name}\n')
    else:
        print('Введены не корректные данные')


if __name__ == '__main__':
    main()

end_time = datetime.now()
print('Время запуска кода: {}'.format(st_time))
print('Время окончания работы кода: {}'.format(end_time))
print('Время выполнения: {}'.format(end_time - st_time))