import time

from environs import Env
from terminaltables import AsciiTable
import requests

LANGUAGES = ['Java', 'Python', 'PHP',
             '1С', 'C++', 'Ruby', 'Swift',
             'Go', 'Javascript', 'Kotlin']


def create_table(languages, title):
    salaries_data = [
        ['Язык программирования',
         'Вакансий найдено',
         'Вакансий обработано',
         'Средняя зарплата']
    ]
    for key, language in languages.items():
        salaries_data.append([key,
                              language["vacancies_found"],
                              language["vacancies_processed"],
                              language["average_salary"],
                              ])
    table = AsciiTable(salaries_data, title)
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


def fetch_vacancies_hh(user_agent, languages):
    headers = {
        'User-Agent': user_agent
    }
    for language in languages:
        all_pages = []
        salaries = []
        page = 0
        pages_number = 2
        days = 30
        area = 1
        seconds = 10
        while page < pages_number:
            payload = {'page': page,
                       'text': f'программист {language}',
                       'search_fields': 'name',
                       'currency': 'RUR',
                       'period': days,
                       'area': area}
            response = requests.get(url, headers=headers, params=payload)
            response.raise_for_status()
            page_payload = response.json()
            pages_number = page_payload.get('pages')
            all_pages.append(page_payload)
            page += 1

        time.sleep(seconds)

        for payload in all_pages:
            for vacancy in payload.get('items'):
                if predict_rub_salary_for_hh(vacancy):
                    salaries.append(predict_rub_salary_for_hh(vacancy))

        average = int(sum(salaries) / len(salaries)) if len(salaries) else 0
        languages[language]['vacancies_found'] = all_pages[0]['found']
        languages[language]['vacancies_processed'] = len(salaries)
        languages[language]['average_salary'] = average

    return languages


def fetch_vacancies_superjob(key, languages):
    headers = {
        'X-Api-App-Id': key
    }
    for language in languages:
        all_pages = []
        salaries = []
        page = 0
        count = 1
        area = 4
        seconds = 10
        directory = 48
        while True:
            payload = {'keyword': f'программист {language}',
                       'page': page,
                       'count': count,
                       't': area,
                       'key': directory
                       }
            response = requests.get(url, headers=headers, params=payload)
            response.raise_for_status()
            page_payload = response.json()
            all_pages.append(page_payload)
            page += 1
            if not page_payload.get('more'):
                break

        time.sleep(seconds)

        for pay in all_pages:
            all_vacancies = pay.get('objects')
            for vacancy in all_vacancies:
                if predict_rub_salary_for_superjob(vacancy):
                    salaries.append(predict_rub_salary_for_superjob(vacancy))

        average = int(sum(salaries) / len(salaries)) if len(salaries) else 0
        languages[language]['vacancies_found'] = page_payload.get('total')
        languages[language]['vacancies_processed'] = len(salaries)
        languages[language]['average_salary'] = average

    return languages


def main():
    env = Env()
    env.read_env()
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'
    table_hh = create_table(
        fetch_vacancies_hh(env('HH_USER_AGENT'), LANGUAGES),
        title_hh
    )
    table_sj = create_table(
        fetch_vacancies_superjob(env('SJ_API_KEY'), LANGUAGES),
        title_sj
    )
    print(table_hh)
    print(table_sj)


if __name__ == '__main__':
    main()
