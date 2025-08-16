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
    };
    record: {
        wins: number;
        losses: number;
    };
    // We can add more things here later
}
