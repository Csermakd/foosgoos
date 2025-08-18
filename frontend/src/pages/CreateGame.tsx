import {Card} from '@/components/ui/Card'
import {Button} from '@/components/ui/button'
import PlayerSelect from '@/components/PlayerSelect'
type Props = {}

//Example data of Player
const playerOptions = [
    'Alice',
    'Bob',
    'Charlie',
    'Diana',
    'Ethan',
    'Fiona',
]

const CreateGame = (props: Props) => {
  return (
    <Card>
        <PlayerSelect
            label="Select Team A Player"
            players={playerOptions}
            value={playerOptions[0]} // Default value
            onChange={(value) => console.log('Team A Player selected:', value)}
            />
    </Card>
  )
}

export default CreateGame
