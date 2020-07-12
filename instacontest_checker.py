import os
import re
import argparse
from instabot import Bot
from dotenv import load_dotenv

parser = argparse.ArgumentParser(
    description='Программа проверяет пользователей на выполнение всех условий розыгрыша в Instagram.'
)
parser.add_argument('link', help='Ссылка на пост, который участвует в конкурсе.')
args = parser.parse_args()


def get_post_comments(bot, post_id):
    return {
        f"{comment['user_id']} {comment['user']['username']}": comment['text']
        for comment in bot.get_media_comments_all(post_id)
    }


def get_mentions_from_comment(comment_text):
    username_regex = '(?:@)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'
    return re.findall(rf'{username_regex}', comment_text)


def is_user_exist(bot, username):
    return bot.get_user_id_from_username(username) is not None


def get_mentions_by_user(bot, post_id):
    return {
        user: get_mentions_from_comment(comment)
        for user, comment in get_post_comments(bot, post_id).items()
    }


def get_valid_users(bot, post_id):
    poster_user_id = bot.get_media_info(post_id)[0]['user']['pk']
    post_likers = bot.get_media_likers(post_id)
    poster_user_followers = bot.get_user_followers(poster_user_id)
    mentions_by_user = get_mentions_by_user(bot, post_id)

    valid_users = []
    checks_left = len(list(mentions_by_user))
    for user, mentions in mentions_by_user.items():
        user_id, username = user.split(' ')
        if any([is_user_exist(bot, friend) for friend in mentions]) \
                and user_id in post_likers \
                and user_id in poster_user_followers:
            bot.logger.warning(f'User {username} is valid. Users to check left: {checks_left}')
            valid_users.append(username)
        checks_left -= 1
    return valid_users


def save_to_txt(valid_users):
    with open('valid_users.txt', 'w') as vu:
        for user in valid_users:
            vu.write("%s\n" % user)


def main():
    bot = Bot()
    bot.login(username=login, password=password)
    post_id = bot.get_media_id_from_link(args.link)
    valid_users = get_valid_users(bot, post_id)
    save_to_txt(valid_users)


if __name__ == '__main__':
    load_dotenv()
    login = os.getenv('LOGIN')
    password = os.getenv('PASSWORD')
    main()
