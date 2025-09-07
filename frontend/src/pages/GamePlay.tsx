import {useSelector} from "react-redux";
import { type RootState } from "@/store";

type GamePlayPageProps = {
    //teamA: Team;
    //teamB: Team;
}

const GamePlay = (props: GamePlayPageProps) => {
    const bluePlayers = useSelector((state: RootState) => state.game.blue);
    const redPlayers = useSelector((state: RootState) => state.game.red);

    console.log('Blue Team Players:', bluePlayers);
    console.log('Red Team Players:', redPlayers);
  return (
    <div>Some dummy text</div>
  )
}

export default GamePlay
