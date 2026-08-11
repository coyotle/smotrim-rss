<h1 align="center">smotrim-rss</h1>
<p align="center">Скрипт создания RSS лент для подкастов с платформы Смотрим</p>
<p align="center">
  <a href="https://pay.cloudtips.ru/p/a368e9f8"> <img src="https://img.shields.io/badge/%E2%9D%A4_%D0%9F%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C_%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82-cloudtips.ru-e55"></a>
  <a href="https://github.com/coyotle/smotrim-rss/actions/workflows/update_pages.yml"><img src="https://github.com/coyotle/smotrim-rss/actions/workflows/update_pages.yml/badge.svg?branch"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

> [!NOTE]
> Часть выпусков на smotrim.ru публикуется только в виде видеопотока (HLS/m3u8) без отдельного аудиофайла.
> Такие выпуски попадают в RSS как video-enclosure (`application/vnd.apple.mpegurl`).
> Большинство подкаст-плееров воспроизводят только аудио, поэтому видео-выпуски могут не проигрываться в приложении.

> [!WARNING]
> Ссылки на некоторые ленты обновились (новое расположение `docs/podcast/{станция}/{brand_id}.xml`).
> Если подписка перестала обновляться — переподпишитесь на подкаст по актуальной ссылке ниже.


## Создание RSS лент самостоятельно
```sh
git clone https://github.com/coyotle/smotrim-rss.git
cd smotrim-rss
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python main.py
```

Файлы RSS будут созданы в директории `docs/podcast/{станция}/{brand_id}.xml`

## RSS ленты

- Внешний хостинг RSS лент: https://rss.coyotle.ru/
- Обновление происходит автоматически с помощью GitHub Actions каждые 2 часа
- Список всех подкастов доступен для импорта в формате [OPML](https://rss.coyotle.ru/podcasts.opml.xml)

### Ленты создаются для следующих программ:

#### Вести ФМ

- [Альтера Парс](https://rss.coyotle.ru/podcast/vesti/60977.xml)
- [Американские горки](https://rss.coyotle.ru/podcast/vesti/63263.xml)
- [Большой формат](https://rss.coyotle.ru/podcast/vesti/62330.xml)
- [Бывшие](https://rss.coyotle.ru/podcast/vesti/62046.xml)
- [Внешний контур](https://rss.coyotle.ru/podcast/vesti/70198.xml)
- [Восточная шкатулка](https://rss.coyotle.ru/podcast/vesti/62186.xml)
- [Дневной рубеж](https://rss.coyotle.ru/podcast/vesti/65871.xml)
- [Еврозона](https://rss.coyotle.ru/podcast/vesti/62139.xml)
- [Железная логика](https://rss.coyotle.ru/podcast/vesti/61016.xml)
- [Иллюзия власти](https://rss.coyotle.ru/podcast/vesti/67761.xml)
- [Информбистро](https://rss.coyotle.ru/podcast/vesti/61029.xml)
- [Научный факт](https://rss.coyotle.ru/podcast/vesti/69679.xml)
- [Нацвопрос](https://rss.coyotle.ru/podcast/vesti/61015.xml)
- [Параллели](https://rss.coyotle.ru/podcast/vesti/61175.xml)
- [Рулевой](https://rss.coyotle.ru/podcast/vesti/68922.xml)
- [Традиции](https://rss.coyotle.ru/podcast/vesti/64392.xml)
- [Угол зрения](https://rss.coyotle.ru/podcast/vesti/69014.xml)
- [Формула смысла](https://rss.coyotle.ru/podcast/vesti/61007.xml)
- [Хай-Тек](https://rss.coyotle.ru/podcast/vesti/60950.xml)
- [Штатный корреспондент](https://rss.coyotle.ru/podcast/vesti/66024.xml)
- [Энергономика](https://rss.coyotle.ru/podcast/vesti/68185.xml)

#### Соловьёв Live

- [Соловьёв LIVE](https://rss.coyotle.ru/podcast/soloviev/66924.xml)
- [Полный контакт](https://rss.coyotle.ru/podcast/soloviev/60948.xml)

#### Маяк

- [Белая студия](https://rss.coyotle.ru/podcast/mayak/60200.xml)
- [МузДок](https://rss.coyotle.ru/podcast/mayak/65317.xml)
- [Мужчина. Руководство по эксплуатации](https://rss.coyotle.ru/podcast/mayak/73273.xml)
- [Не просто Мария](https://rss.coyotle.ru/podcast/mayak/73178.xml)
- [Обратная сторона музыки](https://rss.coyotle.ru/podcast/mayak/73358.xml)
- [Пойми себя, если сможешь](https://rss.coyotle.ru/podcast/mayak/64495.xml)
- [Сергей Стиллавин и его друзья](https://rss.coyotle.ru/podcast/mayak/58219.xml)
- [Трудности перехода](https://rss.coyotle.ru/podcast/mayak/69881.xml)
- [Физики и лирики](https://rss.coyotle.ru/podcast/mayak/62250.xml)
- [Хорошо темперированный эфир](https://rss.coyotle.ru/podcast/mayak/67656.xml)

#### Радио России

- [КультБригада: слово, смысл, литература](https://rss.coyotle.ru/podcast/radiorus/65486.xml)
- [Российский радиоуниверситет](https://rss.coyotle.ru/podcast/radiorus/63253.xml)

P.S. Пишите, если хотите слушать еще какие-то подкасты с платформы "Смотрим".
