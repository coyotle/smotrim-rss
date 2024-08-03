import { Button } from "@/components/ui/button";
import { PlayIcon } from "lucide-react";

const EpisodeCard = ({ info, onClick }) => {
  return (
    <div className="p-4 shadow-md mb-3 content-start justify-start">
      <div className="italic pb-1">{info.published}</div>
      <div className="font-bold pb-2">{info.anons}</div>
      <div>{info.description}</div>
      <Button className="mt-4" onClick={onClick}>
        <PlayIcon /> Слушать
      </Button>
    </div>
  );
};

export default EpisodeCard;
