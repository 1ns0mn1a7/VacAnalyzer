import requests
from terminaltables import AsciiTable
import os
from dotenv import load_dotenv


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def predict_rub_salary_hh(vacancy):
    if not vacancy or not vacancy.get('salary'):
        return None

    salary_from = vacancy['salary'].get('from')
    salary_to = vacancy['salary'].get('to')
    currency = vacancy['salary'].get('currency')

    if currency != 'RUR':
        return None

    return predict_salary(salary_from, salary_to)


def predict_rub_salary_superjob(vacancy):
    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')
    currency = vacancy.get('currency')

    if currency != 'rub':
        return None

    return predict_salary(salary_from, salary_to)


def fetch_hh_vacancies(keyword, area=1, period=30, per_page=100):
    api_url = 'https://api.hh.ru/vacancies'
    page = 0
    vacancies = []
    total_found = 0

    while True:
        params = {
            'text': keyword,
            'area': area,
            'period': period,
            'per_page': per_page,
            'page': page
        }
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        api_response = response.json()

        if page == 0:
            total_found = api_response.get('found', 0)

        current_page_vacancies = api_response.get('items', [])
        if not current_page_vacancies:
            break

        vacancies.extend(current_page_vacancies)
        page += 1

        if page >= api_response.get('pages', 0):
            break

    return vacancies, total_found


def get_language_stats_hh(languages):
    stats = {}

    for language in languages:
        vacancies, total_found = fetch_hh_vacancies(language)
        salaries = [
            salary for vacancy in vacancies
            if (salary := predict_rub_salary_hh(vacancy))
        ]

        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0

        stats[language] = {
            "vacancies_found": total_found,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }

    return stats


def fetch_superjob_vacancies(api_key, catalogue_id=48, town=4, count=100, keyword=""):
    api_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': api_key}
    page = 0
    vacancies = []
    total_found = 0

    while True:
        params = {
            'catalogues': catalogue_id,
            'town': town,
            'count': count,
            'page': page,
            'keyword': keyword
        }

        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        api_response = response.json()

        if page == 0:
            total_found = api_response.get('total', 0)

        vacancies.extend(api_response.get('objects', []))

        if not api_response.get('more'):
            break

        page += 1

    return vacancies, total_found


def collect_superjob_stats(api_key, languages):
    stats = {}

    for language in languages:
        vacancies, total_found = fetch_superjob_vacancies(
            api_key,
            keyword=language
        )
        salaries = [
            salary for vacancy in vacancies
            if (salary := predict_rub_salary_superjob(vacancy))
        ]

        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0

        stats[language] = {
            "vacancies_found": total_found,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }

    return stats


def print_stats_table(stats_headhunter, stats_superjob):
    def build_table(title, stats):
        column_titles = [
            'Язык программирования',
            'Вакансий',
            'Обработано',
            'Средняя зарплата'
        ]
        table_rows = [column_titles]

        for language, statistics in stats.items():
            table_rows.append([
                language,
                statistics["vacancies_found"],
                statistics["vacancies_processed"],
                statistics["average_salary"]
            ])

        table = AsciiTable(table_rows)
        table.title = title
        return table

    headhunter_table = build_table("HeadHunter Москва", stats_headhunter)
    superjob_table = build_table("SuperJob Москва", stats_superjob)

    print(headhunter_table.table)
    print(superjob_table.table)


def main():
    load_dotenv()

    superjob_api_key = os.environ["SUPERJOB_API_KEY"]

    languages = [
        "JavaScript",
        "Java",
        "Python",
        "Ruby",
        "PHP",
        "C++",
        "CSS",
        "C#",
        "C",
        "Go",
        "Shell",
        "Objective-C",
        "Scala",
        "Swift",
        "TypeScript",
        "1C"
    ]

    stats_headhunter = get_language_stats_hh(languages)
    stats_superjob = collect_superjob_stats(superjob_api_key, languages)

    print_stats_table(stats_headhunter, stats_superjob)


if __name__ == '__main__':
    main()
