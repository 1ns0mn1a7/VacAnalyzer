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


def fetch_hh_vacancies(api_url, keyword, area=1, period=30, per_page=100):
    page = 0
    vacancies = []

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
        current_page_vacancies = api_response.get('items', [])

        if not current_page_vacancies:
            break

        vacancies.extend(current_page_vacancies)
        page += 1

        if page >= api_response.get('pages', 0):
            break

    return vacancies


def get_language_stats_hh(api_url, languages):
    stats = {}

    for language in languages:
        vacancies = fetch_hh_vacancies(api_url, language)
        salaries = [
            predict_rub_salary_hh(vacancy) for vacancy in vacancies
            if predict_rub_salary_hh(vacancy) is not None
        ]

        if salaries:
            average_salary = int(sum(salaries) / len(salaries))
            stats[language] = {
                "vacancies_found": len(vacancies),
                "vacancies_processed": len(salaries),
                "average_salary": average_salary
            }

    return stats


def fetch_superjob_vacancies(api_key, catalogue_id=48, town=4, count=100, keyword=""):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': api_key}
    page = 0
    vacancies = []

    while True:
        params = {
            'catalogues': catalogue_id,
            'town': town,
            'count': count,
            'page': page,
            'keyword': keyword
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        api_response = response.json()

        vacancies.extend(api_response.get('objects', []))

        if not api_response.get('more'):
            break

        page += 1

    return vacancies


def collect_superjob_stats(api_key, languages):
    stats = {}

    for language in languages:
        vacancies = fetch_superjob_vacancies(api_key, keyword=language)
        if not vacancies:
            continue

        salaries = [
            predict_rub_salary_superjob(vacancy) for vacancy in vacancies
            if predict_rub_salary_superjob(vacancy) is not None
        ]

        if salaries:
            average_salary = int(sum(salaries) / len(salaries))
            stats[language] = {
                "vacancies_found": len(vacancies),
                "vacancies_processed": len(salaries),
                "average_salary": average_salary
            }

    return stats


def print_stats_table(stats_headhunter, stats_superjob):
    column_titles = ['Язык программирования', 'Вакансий', 'Обработано', 'Средняя зарплата']

    headhunter_table_rows = [column_titles]
    for language, statistics in stats_headhunter.items():
        headhunter_table_rows.append([
            language,
            statistics["vacancies_found"],
            statistics["vacancies_processed"],
            statistics["average_salary"]
        ])

    superjob_table_rows = [column_titles]
    for language, statistics in stats_superjob.items():
        superjob_table_rows.append([
            language,
            statistics["vacancies_found"],
            statistics["vacancies_processed"],
            statistics["average_salary"]
        ])

    headhunter_table = AsciiTable(headhunter_table_rows)
    headhunter_table.title = "HeadHunter Москва"

    superjob_table = AsciiTable(superjob_table_rows)
    superjob_table.title = "SuperJob Москва"

    print(headhunter_table.table)
    print(superjob_table.table)


def main():
    load_dotenv()

    hh_api_url = 'https://api.hh.ru/vacancies'
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

    stats_headhunter = get_language_stats_hh(hh_api_url, languages)
    stats_superjob = collect_superjob_stats(superjob_api_key, languages)

    print_stats_table(stats_headhunter, stats_superjob)


if __name__ == '__main__':
    main()