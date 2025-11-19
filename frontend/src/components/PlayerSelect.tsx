import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";

type PlayerSelectProps = {
  label: string;
  players: string[];
  value: string;
  onChange: (value: string) => void;
};

const PlayerSelect = ({
  label,
  players,
  value,
  onChange,
}: PlayerSelectProps) => {
  return (
    <div className="w-full">
      <label className="text-sm font-medium mb-1 block">{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full bg-white">
          <SelectValue placeholder="Select a player" />
        </SelectTrigger>
        <SelectContent>
          {players.map((player) => (
            <SelectItem key={player} value={player}>
              {player}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default PlayerSelect;
