import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import '../styles/ViewUser.css'
import bluePlayer from '../assets/blue_player.svg'

type Props = {}

type Player = {
  username: string
  stats: {
    games: number
    wins: number
    losses: number
    goals: number
  }
}

const samplePlayers: Player[] = [
  { username: 'BluePlayer1', stats: { games: 12, wins: 8, losses: 4, goals: 34 } },
  { username: 'RedRocket', stats: { games: 20, wins: 11, losses: 9, goals: 48 } },
  { username: 'Spinner', stats: { games: 5, wins: 2, losses: 3, goals: 7 } },
]

const ViewUser = (_props: Props) => {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Player | null>(null)
  const navigate = useNavigate()

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return samplePlayers
    return samplePlayers.filter(p => p.username.toLowerCase().includes(q))
  }, [query])

  function choosePlayer(p: Player) {
    setSelected(p)
    setIsOpen(false)
    setQuery('')
  }

  return (
    <div className="view-user-page">
      <div className="return-container">
        <Button variant="neutral" onClick={() => navigate('/')}>Return Home</Button>
      </div>
      <div className="search-container">
        <button className="search-toggle" onClick={() => setIsOpen(s => !s)}>
          Search Player ▾
        </button>

        {isOpen && (
          <div className="search-dropdown" role="dialog" aria-label="Search players">
            <input
              className="search-input"
              placeholder="Type a player name..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              autoFocus
            />

            <ul className="search-results">
              {filtered.map(p => (
                <li key={p.username} className="search-item" onClick={() => choosePlayer(p)}>
                  {p.username}
                </li>
              ))}
              {filtered.length === 0 && <li className="search-empty">No players found</li>}
            </ul>
          </div>
        )}
      </div>

      <div className="player-visual">
        <img src={bluePlayer} alt="Blue player" className="blue-player-img" />
      </div>

      <div className="user-info">
        <h2 className="username">{selected ? selected.username : 'No user selected'}</h2>

        <div className="stats">
          <div className="stat-row">
            <span className="stat-label">Games</span>
            <span className="stat-value">{selected ? selected.stats.games : '--'}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Wins</span>
            <span className="stat-value">{selected ? selected.stats.wins : '--'}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Losses</span>
            <span className="stat-value">{selected ? selected.stats.losses : '--'}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Goals</span>
            <span className="stat-value">{selected ? selected.stats.goals : '--'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ViewUser
