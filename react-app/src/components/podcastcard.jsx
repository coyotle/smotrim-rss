import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Play, RssIcon } from "lucide-react";

const PodcastCard = ({ info }) => {
  return (
    <div className="shadow-lg mb-3 text-left flex flex-col rounded-md overflow-hidden">
      <img src={info.image} />
      <div className="p-4">{info.description}</div>
      <div className="flex justify-between mt-auto pb-4 mx-4">
        <Link to={info.listen_url}>
          <Button>
            <Play /> Слушать
          </Button>
        </Link>
        <a href={info.feed} target="_blank" rel="noopener noreferrer">
          <Button>
            <RssIcon />
          </Button>
        </a>
      </div>
    </div>
  );
};

export default PodcastCard;
