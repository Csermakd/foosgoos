export type Team = {
    name: string;
    players: [Player, Player];
    score: number;
}

export type Player = {
    name: string;
    goals: number;
    // We can add more things here later
}
