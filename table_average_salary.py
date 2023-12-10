import time

from environs import Env
from terminaltables import AsciiTable
import requests

LANGUAGES = [
    'Java', 'Python', 'PHP', '1С', 'C++', 'Ruby',
    'Swift', 'Go', 'Javascript', 'Kotlin'
]


def create_table(languages, title):
    salaries = [
        ['Язык программирования',
         'Вакансий найдено',
         'Вакансий обработано',
         'Средняя зарплата']
    ]
    for language, language_statistic in languages.items():
        salaries.append(
            [language,
            language_statistic["vacancies_found"],
            language_statistic["vacancies_processed"],
            language_statistic["average_salary"],
        ])
    table = AsciiTable(salaries, title)
    return table.table


def predict_salary(salary_from, salary_to):
    if not any((salary_from, salary_to)):
        return None
    if not salary_from:
        return salary_to * 0.8
    if not salary_to:
        return salary_from * 1.2
    return (salary_from + salary_to) / 2


def predict_rub_salary_for_superjob(vacancy):
    if vacancy.get('currency') != 'rub':
        return None
    return predict_salary(vacancy.get('payment_from'), vacancy.get('payment_to'))


def predict_rub_salary_for_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary:
        return None
    return predict_salary(salary.get('from'), salary.get('to'))


def fetch_statistics_hh(user_agent, languages):
    salary_per_languages = {}
    headers = {
        'User-Agent': user_agent
    }
    for language in languages:
        all_pages = []
        salaries = []
        page = 0
        pages_number = 1
        days = 30
        area = 1
        seconds = 1
        while page < pages_number:
            payload = {
                'page': page,
                'text': f'программист {language}',
                'search_fields': 'name',
                'currency': 'RUR',
                'period': days,
                'area': area
            }
            response = requests.get(
                'https://api.hh.ru/vacancies',
                headers=headers,
                params=payload
            )
            response.raise_for_status()
            page_payload = response.json()
            pages_number = page_payload.get('pages')
            all_pages.append(page_payload)
            page += 1

        time.sleep(seconds)

        for payload in all_pages:
            for vacancy in payload.get('items'):
                salary = predict_rub_salary_for_hh(vacancy)
                if salary:
                    salaries.append(salary)

        average = int(sum(salaries) / len(salaries)) if len(salaries) else 0
        salary_per_languages[language] = {
            'vacancies_found': all_pages[0]['found'],
            'vacancies_processed': len(salaries),
            'average_salary': average
        }
    return salary_per_languages


def fetch_statistics_superjob(key, languages):
    salary_per_languages = {}
    headers = {
        'X-Api-App-Id': key
    }
    for language in languages:
        all_pages = []
        salaries = []
        page = 0
        count = 1
        area = 4
        seconds = 1
        directory = 48
        while True:
            payload = {
                'keyword': f'программист {language}',
                'page': page,
                'count': count,
                't': area,
                'key': directory
            }
            response = requests.get(
                'https://api.superjob.ru/2.0/vacancies/',
                headers=headers,
                params=payload
            )
            response.raise_for_status()
            page_payload = response.json()
            all_pages.append(page_payload)
            page += 1
            if not page_payload.get('more'):
                break

        time.sleep(seconds)

        for one_page in all_pages:
            all_vacancies = one_page.get('objects')
            for vacancy in all_vacancies:
                salary = predict_rub_salary_for_superjob(vacancy)
                if salary:
                    salaries.append(salary)

        average = int(sum(salaries) / len(salaries)) if len(salaries) else 0
        salary_per_languages[language] = {
            'vacancies_found': page_payload.get('total'),
            'vacancies_processed': len(salaries),
            'average_salary': average
        }
    return salary_per_languages


def main():
    env = Env()
    env.read_env()
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'
    table_hh = create_table(
        fetch_statistics_hh(env('HH_USER_AGENT'), LANGUAGES),
        title_hh
    )
    table_sj = create_table(
        fetch_statistics_superjob(env('SJ_API_KEY'), LANGUAGES),
        title_sj
    )
    print(table_hh)
    print(table_sj)


if __name__ == '__main__':
    main()
