import logging
import bs4
import requests
import time
import csv

URL = 'https://odsluchane.eu/'
URL_DATA = 'https://www.odsluchane.eu/szukaj.php'  # ' ?r=44&date=23-05-2022&time_from=1&time_to=3'

# EDIT ROK - year AND STATION - station integer number default Radio Bielsko
ROK = 2020
STATION = 44

LOGGING_LV = logging.INFO

logging.basicConfig(level=LOGGING_LV, format=' %(asctime)s - %(levelname)s- %(message)s')
logging.debug('Początek programu')

if ROK % 4 == 0:
    logging.debug('Rok przestępny')
    month_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    MAX_DAYS = 366
else:
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    MAX_DAYS = 365


def convert_day_to_date(daynumber):
    month = 0
    while True:
        day = daynumber
        if daynumber > month_days[month]:
            daynumber -= month_days[month]
            month += 1
        else:
            return day, month + 1


def scrap_year(rok):
    for daynumber in range(1, MAX_DAYS + 1):
        logging.debug('Dzień:' + str(daynumber))
        day, month = convert_day_to_date(daynumber)
        for time in range(0, 12):
            time_start = time * 2
            time_end = time * 2 + 2
            if time_end == 24:
                time_end = 0
            yield day, month, time_start, time_end
    yield 0, 0, 0, 0


def get_page(url):
    logging.debug('Pobieram {}'.format(url))
    try:
        res = requests.get(url)
        res.raise_for_status()
        result = res.text
    except Exception as e:
        logging.error(e)
        result = ''
    return result


def bs_parse(content):
    lista = []

    soup = bs4.BeautifulSoup(content)
    # print(soup.select('div.column table.table')[0].select('tr td')[2].select('a.title-link')[0].getText().strip())

    try:
        soup_base = soup.select('div.column table.table')[0].select('tr')

        for zupa in soup_base:
            if zupa.select('td.bg-gray') or zupa.select('div.googl-ad-responsive'):
                continue
            if zupa.select('td'):
                time_em = zupa.select('td')[0].getText()
                lista.append(time_em)
            if zupa.select('td a.title-link'):
                song = zupa.select('td a.title-link')[0].getText().strip()
                lista.append(song)
    except:
        logging.error('Problem z przetwarzaniem strony')
    return lista


def save_data(data, st, day, month, year):
    dateday = "{0:04d}-{1:02d}-{2:02d}".format(year, month, day)
    timm = "00:00"
    for dd in data:
        if len(dd) == 5:
            timm = dd
        else:
            song = dd
            logging.debug('{0} {1} - {2}'.format(dateday, timm, song))
            data = [dateday, timm, song, STATION]

            with open('st{0}rok{1}.csv'.format(st, year), 'a', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(data)


# bs_parse(get_page(URL_DATA))
gnr = scrap_year(ROK)
while True:
    day, month, time_start, time_end = next(gnr)
    # logging.debug("Miesiac: "+str(month)+" Dzien: "+str(day)+" Godziny: "+str(time_start)+" - "+str(time_end))
    if day + month + time_start + time_end == 0:
        break

    # ' ?r=44&date=23-05-2022&time_from=1&time_to=3'
    zapytanie = URL_DATA + '?r={0}&date={1:02d}-{2:02d}-{3:04d}&time_from={4:01d}&time_to={5:01d}'.format(str(STATION),
                                                                                                          day,
                                                                                                          month, ROK,
                                                                                                          time_start,
                                                                                                          time_end)

    logging.info("Pobieram dane dla adresu: " + zapytanie)

    odpowiedz = bs_parse(get_page(zapytanie))
    if len(odpowiedz) == 0:
        logging.warning("Brak danych dla wybranego okresu")
        continue
    save_data(odpowiedz, STATION, day, month, ROK)

    time.sleep(1)
