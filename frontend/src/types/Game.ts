export type Team = {
    name: string;
    players: [Player, Player];
    score: number;
}

export type Player = {
    name: string;
    goals: {
        goalie: number;
        twoBar: number;
        threeBar: number;
        fiveBar: number;
        ownGoal: number;
    };
    record: {
        wins: number;
        losses: number;
    };
    position: 'offense' | 'defense';
    // We can add more things here later
}

export type PlayerAssignment = {
    id: number;
    name: string;
    position: 'offense' | 'defense';
}

export type GameResult = {
    winners: [string, string];
    losers: [string, string];
    date: string; // ISO string
}

export type GoalEvent = {
  team: 'blue' | 'red';
  playerName: string;
  position: 'offense' | 'defense';
  goalType: '5bar' | '3bar' | 'goalie' | '2bar' | 'ownGoal';
};
 
