import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/Select';

type PlayerSelectProps = {
    label: string;
    players: string[];
    value: string;
    onChange: (value: string) => void;
    position: 'offense' | 'defense';
    onPositionChange: (position: 'offense' | 'defense') => void;
};

const PlayerSelect = ({ label, players, value, onChange, position, onPositionChange }: PlayerSelectProps) => {
    return (
        <div>
            <label>{label}</label>
            <Select value={value} onValueChange={onChange}>
               <SelectTrigger className="w-full">
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
            <div className="mt-2">
                <label>Position: </label>
                <select
                    value={position}
                    onChange={e => onPositionChange(e.target.value as 'defense' | 'offense')}
                    className="ml-2 border rounded px-2 py-1"
                >
                    <option value="defense">Defense</option>
                    <option value="offense">Offense</option>
                </select>
            </div>

        </div>
    )
}

export default PlayerSelect;
