import { useMemo, useState, useEffect, useRef, useCallback } from 'react';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Input } from '@/components/ui/input';

type PlayerSelectProps = {
  label: string;
  players: string[];
  value: string;
  onChange: (value: string) => void;
};

const PlayerSelect = ({ label, players, value, onChange }: PlayerSelectProps) => {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
      const q = query.trim().toLowerCase()
      if (!q) return players
      const searchResults = players.filter(p => p.toLowerCase().includes(q))
      if (value && !searchResults.includes(value)) {
        return [value, ...searchResults]
      }
      return searchResults
    }, [query, players, value])

  const handleGlobalKeydown = useCallback((e: KeyboardEvent) => {
      if (open && inputRef.current && document.activeElement !== inputRef.current) {
          if (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete') {
              inputRef.current.focus();
          }
      }
  }, [open]);

  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => {
          inputRef.current?.focus();
      }, 10);
      document.addEventListener('keydown', handleGlobalKeydown);
      return () => {
          clearTimeout(timer);
          document.removeEventListener('keydown', handleGlobalKeydown);
      };

    } else {
      setQuery('');
    }
  }, [open, handleGlobalKeydown]);

  return (
    <div className="flex w-full flex-col gap-1.5">
      {/* Was a bare <label> inheriting nothing, so slot labels rendered at a
          different size and weight to every other label in the app. */}
      <label className="text-sm font-heading uppercase tracking-wide text-muted-foreground">
        {label}
      </label>
      <Select value={value} onValueChange={onChange} onOpenChange={setOpen} open={open}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select a player" />
        </SelectTrigger>
        <SelectContent>
          <Input className="mb-2" type="text" value={query} ref={inputRef} placeholder='Search players...' onChange={(e) => setQuery(e.target.value)} />
          {filtered.map((player) => (
            <SelectItem key={player} value={player}>
              {player}
            </SelectItem>
          ))}
          {filtered.length === 0 && <SelectItem key="no-players" value='No Players Found' disabled={true}>No players found</SelectItem>}
        </SelectContent>
      </Select>
    </div>
  );
};

export default PlayerSelect;
