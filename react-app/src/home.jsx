import { useState, useEffect } from "react";
import axios from "axios";
import { Github, Heart, MessageCircle } from "lucide-react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
} from "./components/ui/breadcrumb";
import PodcastCard from "./components/podcastcard";

const Home = () => {
  const [podcasts, setPodcasts] = useState([]);

  useEffect(() => {
    const getData = async () => {
      axios.get("/data/podcasts.json").then(({ data }) => {
        const data_enriched = data.map((item) => ({
          ...item,
          listen_url: item.brand_id
            ? `/listen?brand_id=${item.brand_id}`
            : `/listen?rubric_id=${item.rubric_id}`,
        }));

        console.log("enriched: ", data_enriched);
        setPodcasts(data_enriched);
      });
    };
    getData();
  }, []);

  return (
    <div>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Главная</BreadcrumbLink>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="text-left text-3xl py-4">Подкасты Вести ФМ</div>
      <div className="text-left italic pb-4">
        Радио Вести ФМ на данный момент (декабрь 2023 г.) прекратило поддержку
        RSS лент своих передач. На этой странице представлено несколько лент
        которые мы хотим слушать в формате подкастов, делимся ими с вами.
      </div>
      <div className="text-left p-6 mb-4 bg-orange-100 rounded-md">
        <p className="mb-2 flex items-center space-x-1">
          <Github className="min-w-[24px]" />
          &nbsp;
          <span>
            Наш проект теперь с открытым кодом! Можете использовать или внести
            свой вклад на&nbsp;
            <a
              href="https://github.com/coyotle/vesti-rss"
              target="_blank"
              className="underline"
            >
              GitHub
            </a>
            .
          </span>
        </p>
        <p className="mb-2 flex items-center space-x-1">
          <Heart className="min-w-[24px]" /> &nbsp;
          <span>
            Вы можете поддержать проект,{" "}
            <a
              href="https://pay.cloudtips.ru/p/a368e9f8"
              target="_blank"
              className="underline"
            >
              сделав донат
            </a>
            . Спасибо всем, кто уже оказал поддержку! Общая сумма донатов: 3 800
            ₽
          </span>
        </p>
        <p className="mb-2 flex items-center space-x-1">
          <MessageCircle className="min-w-[24px]" /> &nbsp;
          <span>
            Поделитесь своими мыслями, пожеланиями, предложениями&nbsp;
            <a
              href="mailto:me@coyotle.ru?subject=ВестиФМ"
              className="underline"
            >
              me@coyotle.ru
            </a>
          </span>
        </p>
      </div>
      {podcasts.length <= 0 ? (
        <div>Нет данных для отображения</div>
      ) : (
        <div className="grid xl:grid-cols-3 md:grid-cols-2 sm:grid-cols-1 grid-cols-1 gap-4">
          {podcasts.map((item) => (
            <PodcastCard
              key={item.brand_id ? item.brand_id : item.rubric_id}
              info={item}
            />
          ))}
        </div>
      )}
      <div className="text-left pt-6">
        Мы не несем ответственности за содержание материалов и не храним их у
        себя. Представленные ленты являются "прокси" для оригинальных материалов
        размещаемых ВГТРК и доступных на платформе "Смотрим".
      </div>
    </div>
  );
};

export default Home;
