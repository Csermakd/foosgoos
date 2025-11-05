import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Input } from '@/components/ui/input';
import { useMemo, useState } from 'react';

type PlayerSelectProps = {
  label: string;
  players: string[];
  value: string;
  onChange: (value: string) => void;
};

const PlayerSelect = ({ label, players, value, onChange }: PlayerSelectProps) => {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => {
      const q = query.trim().toLowerCase()
      if (!q) return players
      return players.filter(p => p.toLowerCase().includes(q))
    }, [query, players])
  return (
    <div>
      <label>{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select a player" />
        </SelectTrigger>
        <SelectContent>
          <Input className="mb-2" type="text" placeholder='Search players...' onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.stopPropagation()} onKeyUp={(e) => e.stopPropagation()} />
          {filtered.map((player) => (
            <SelectItem key={player} value={player} autoFocus={false}>
              {player}
            </SelectItem>
          ))}
          {filtered.length === 0 && <SelectItem key="no-players" value='No Players Found' disabled={true}>No players found</SelectItem>}
        </SelectContent>
      </Select>
    </div>
  )
}

export default PlayerSelect;
