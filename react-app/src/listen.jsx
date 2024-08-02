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
import { Button } from "./components/ui/button";
import { useLocation } from "react-router-dom";
import { Calendar, PlayIcon } from "lucide-react";

const Listen = () => {
  const audioRef = useRef(null);
  const [episodes, setEpisodes] = useState([]);

  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const brand_id = queryParams.get("brand_id");
  const rubric_id = queryParams.get("rubric_id");

  useEffect(() => {
    const getData = async () => {
      if (brand_id)
        axios.get(`/data/brands/${brand_id}.json`).then(({ data }) => {
          setEpisodes(data.contents[0].list);
        });
      if (rubric_id)
        axios.get(`/data/rubrics/${rubric_id}.json`).then(({ data }) => {
          setEpisodes(data.contents[0].list);
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

  if (episodes.length == 0) return <p>No episodes available</p>;

  return (
    <div>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Главная</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{episodes[0].title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="text-left">
        <h2 className="text-3xl py-4">{episodes[0].title}</h2>
        <img
          src={episodes[0].player.preview.source.main}
          className="rounded-md mb-4"
        />
        {episodes.map((item) => (
          <div
            key={item.id}
            className="p-4 shadow-md mb-3 content-start justify-start"
          >
            <div className="italic pb-1">{item.published}</div>
            <div className="font-bold pb-2">{item.anons}</div>
            <div>{item.description}</div>
            <Button
              className="mt-4"
              onClick={() => {
                play(item.id);
              }}
            >
              <PlayIcon /> Слушать
            </Button>
          </div>
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
    </div>
  );
};

export default Listen;
