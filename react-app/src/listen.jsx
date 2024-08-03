import { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "./components/ui/breadcrumb";
import { useLocation } from "react-router-dom";
import EpisodeCard from "./components/episodecard";

// remove start and end qoutes
function del_quotes(str) {
  str = str.replace(/^"|"$/g, "");
  return str;
}

const Listen = () => {
  const audioRef = useRef(null);
  const [episodes, setEpisodes] = useState([]);

  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const brand_id = queryParams.get("brand_id");
  const rubric_id = queryParams.get("rubric_id");

  useEffect(() => {
    const getData = async () => {
      let url = "";
      if (brand_id) url = `/data/brands/${brand_id}.json`;
      else if (rubric_id) url = `/data/rubrics/${brand_id}.json`;
      else return;

      axios
        .get(url)
        .then(({ data }) => {
          if (data.contents) {
            const eps = data.contents[0].list.map((item) => {
              return { ...item, anons: del_quotes(item.anons) };
            });
            setEpisodes(eps);
          }
        })
        .catch(() => {
          console.log("не могу загрузить эпизоды");
        });
    };
    getData();
  }, []);

  const play = (audioId) => {
    const src = `https://vgtrk-podcast.cdnvideo.ru/audio/listen?id=${audioId}`;
    console.log(src);
    if (audioRef.current) {
      audioRef.current.src = src;
      audioRef.current.play();
    }
  };

  return (
    <div>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Главная</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>
              {episodes.lenght > 0 ? episodes[0].title : ""}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {episodes.length <= 0 ? (
        <div className="py-4">Нет данных для отображения</div>
      ) : (
        <div className="text-left">
          <h2 className="text-3xl py-4">{episodes[0].title}</h2>
          <img
            src={episodes[0].player.preview.source.main}
            className="rounded-md mb-4"
          />
          {episodes.map((item) => (
            <EpisodeCard
              key={item.id}
              info={item}
              onClick={() => {
                play(item.id);
              }}
            />
          ))}
          <div className="fixed bottom-0 w-full bg-white">
            <audio
              controls
              ref={audioRef}
              className="w-full max-w-lg"
              preload="auto"
            >
              <source id="audioSource" type="audio/mp3" />
              Your browser does not support the audio element.
            </audio>
          </div>
        </div>
      )}
    </div>
  );
};

export default Listen;
