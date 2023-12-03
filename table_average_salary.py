import time

from terminaltables import AsciiTable
import requests


LANGUAGES = {'Java': {}, 'Python': {}, 'PHP': {},
             '1С': {}, 'C++': {}, 'Ruby': {}, 'Swift': {},
             'Go': {}, 'Javascript': {}, 'Kotlin': {}}


def get_response(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response


def make_dict(languages, language, salary, total):
    average = int(sum(salary) / len(salary)) if len(salary) else 0
    languages[language]['vacancies_found'] = total
    languages[language]['vacancies_processed'] = len(salary)
    languages[language]['average_salary'] = average
    return languages


def create_table(thesauruses, title):
    table_data = [
        ['Язык программирования',
         'Вакансий найдено',
         'Вакансий обработано',
         'Средняя зарплата']
    ]
    for key, thesaurus in thesauruses.items():
        table_data.append([key,
                           thesaurus["vacancies_found"],
                           thesaurus["vacancies_processed"],
                           thesaurus["average_salary"],
                           ])
    table = AsciiTable(table_data, title)
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


def fetch_hh(languages):
    dict_languages = {}
    headers = {
        'User-Agent': 'hh.py (mandarina776@gmail.com)'
    }
    for language in languages:
        all_pages = []
        salary = []
        page = 0
        pages_number = 2
        while page < pages_number:
            payload = {'page': page,
                       'text': f'программист {language}',
                       'search_fields': 'name',
                       'currency': 'RUR',
                       'period': 30,
                       'area': 1}
            page_payload = get_response(
                'https://api.hh.ru/vacancies',
                headers,
                payload
            ).json()
            pages_number = page_payload.get('pages')
            all_pages.append(page_payload)
            page += 1

        time.sleep(10)

        for payload in all_pages:
            for vacancy in payload.get('items'):
                if predict_rub_salary_for_hh(vacancy):
                    salary.append(predict_rub_salary_for_hh(vacancy))

        dict_languages = make_dict(
            languages,
            language,
            salary,
            all_pages[0]['found']
        )

    return dict_languages


def fetch_superjob(languages):
    dict_languages = {}
    headers = {
        'X-Api-App-Id': 'v3.r.137979758.a1aa693d4024c996d8e001a7af7b'
                        '24662748bae2.220d6b91874162cb06ea8c028cb68deb7094b1d6'
    }
    for language in languages:
        all_pages = []
        salary = []
        page = 0
        while True:
            payload = {'keyword': f'программист {language}',
                       'page': page,
                       'count': 1,
                       't': 4,
                       'key': 48
                       }
            page_payload = get_response(
                'https://api.superjob.ru/2.0/vacancies/',
                headers,
                payload
            ).json()
            all_pages.append(page_payload)
            page += 1
            if not page_payload.get('more'):
                break

        time.sleep(10)

        for pay in all_pages:
            all_vacancies = pay.get('objects')
            for vacancy in all_vacancies:
                if predict_rub_salary_for_superjob(vacancy):
                    salary.append(predict_rub_salary_for_superjob(vacancy))

        dict_languages = make_dict(
            languages,
            language,
            salary,
            page_payload.get('total')
        )

    return dict_languages


def main():
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'
    table_hh = create_table(fetch_hh(LANGUAGES), title_hh)
    table_sj = create_table(fetch_superjob(LANGUAGES), title_sj)
    print(table_hh)
    print(table_sj)


if __name__ == '__main__':
    main()
