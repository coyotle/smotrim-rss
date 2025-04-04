<h1 align="center">smotrim-rss</h1>
<p align="center">Скрипт создания RSS лент для подкастов с платформы Смотрим</p>
<p align="center">
  <a href="https://pay.cloudtips.ru/p/a368e9f8"> <img src="https://img.shields.io/badge/%E2%9D%A4_%D0%9F%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C_%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82-cloudtips.ru-e55"></a>
  <a href="https://github.com/coyotle/vesti-rss/actions/workflows/update_pages.yml"><img src="https://github.com/coyotle/vesti-rss/actions/workflows/update_pages.yml/badge.svg?branch"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

Для создания лент самостоятельно:

```sh
git clone https://github.com/coyotle/smotrim-rss.git
cd smotrim-rss
python -m venv venv
. venv/bin/activate
pip install requirements.txt
python main.py
```

Файлы RSS будут в директории `docs/`

## RSS ленты

- Внешний хостинг RSS лент: https://rss.coyotle.ru/
- Обновление происходит автоматически с помощью GitHub Actions каждые в 2 часа

### Ленты создаются для следующих программ:

#### Вести ФМ

- [Альтера Парс](https://rss.coyotle.ru/60977.xml)
- [Американские горки](https://rss.coyotle.ru/amgorki.xml)
- [Большой формат](https://rss.coyotle.ru/62330.xml)
- [Бывшие](https://rss.coyotle.ru/former.xml)
- [Внешний контур](https://rss.coyotle.ru/70198.xml)
- [Восточная шкатулка](https://rss.coyotle.ru/vshkatulka.xml)
- [Дневной рубеж](https://rss.coyotle.ru/65871.xml)
- [Дни и ночи войны](https://rss.coyotle.ru/69811.xml)
- [Еврозона](https://rss.coyotle.ru/eurozone.xml)
- [Железная логика](https://rss.coyotle.ru/zheleznaya.xml)
- [Иллюзия власти](https://rss.coyotle.ru/illusion.xml)
- [Информбистро](https://rss.coyotle.ru/61029.xml)
- [Нацвопрос](https://rss.coyotle.ru/natsvopros.xml)
- [Наша Арктика](https://rss.coyotle.ru/69169.xml)
- [Параллели](https://rss.coyotle.ru/paralleli.xml)
- [Поворот на Восток](https://rss.coyotle.ru/povorotnavostok.xml)
- [Поле Куликова](https://rss.coyotle.ru/polekulikova.xml)
- [Традиции](https://rss.coyotle.ru/64392.xml)
- [Турецкий хаб](https://rss.coyotle.ru/turhub.xml)
- [Угол зрения](https://rss.coyotle.ru/69014.xml)
- [Формула смысла](https://rss.coyotle.ru/formula.xml)
- [Хай-Тек](https://rss.coyotle.ru/vesti/60950.xml)
- [Штатный корреспондент](https://rss.coyotle.ru/66024.xml)
- [Энергономика](https://rss.coyotle.ru/68185.xml)

#### Соловьёв Live

- [Соловьёв LIVE](https://rss.coyotle.ru/66924.xml)
- [Полный контакт](https://rss.coyotle.ru/soloviev/60948.xml)

#### Маяк

- [Белая студия](https://rss.coyotle.ru/mayak/60200.xml)
- [МузДок](https://rss.coyotle.ru/mayak/65317.xml)
- [Мужчина. Руководство по эксплуатации](https://rss.coyotle.ru/mayak/1641.xml)
- [Не просто Мария](https://rss.coyotle.ru/mayak/3041.xml)
- [Пойми себя, если сможешь](https://rss.coyotle.ru/mayak/64495.xml)
- [Сергей Стиллавин и его друзья](https://rss.coyotle.ru/mayak/58219.xml)
- [Трудности перехода](https://rss.coyotle.ru/mayak/69881.xml)
- [Физики и лирики](https://rss.coyotle.ru/mayak/62250.xml)
- [Хорошо темперированный эфир](https://rss.coyotle.ru/mayak/67656.xml)

#### Радио России

- [КультБригада: слово, смысл, литература](https://rss.coyotle.ru/radiorus/65486.xml)
- [Российский радиоуниверситет](https://rss.coyotle.ru/radiorus/63253.xml)
- [Театр у микрофона](https://rss.coyotle.ru/radiorus/62853.xml)

P.S. Пишите, если хотите слушать еще какие-то подкасты с платформы "Смотрим".
