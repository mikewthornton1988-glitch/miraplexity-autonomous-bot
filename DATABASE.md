# Database Schema

This document describes the Supabase database schema required for the Miraplexity Pool Game Bot.

## Tables

### tournaments
Stores tournament information including prize pools and entry fees.

```sql
CREATE TABLE tournaments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    prize_pool NUMERIC DEFAULT 0,
    entry_fee NUMERIC DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### players
Stores player information and their tournament participation.

```sql
CREATE TABLE players (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    skill_rating INTEGER DEFAULT 100,
    wallet NUMERIC DEFAULT 0,
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### matches
Stores match results between players.

```sql
CREATE TABLE matches (
    id UUID PRIMARY KEY,
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    player1 UUID REFERENCES players(id) ON DELETE CASCADE,
    player2 UUID REFERENCES players(id) ON DELETE CASCADE,
    winner UUID REFERENCES players(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Indexes

For better performance, create these indexes:

```sql
CREATE INDEX idx_players_tournament ON players(tournament_id);
CREATE INDEX idx_players_skill ON players(skill_rating DESC);
CREATE INDEX idx_matches_tournament ON matches(tournament_id);
CREATE INDEX idx_tournaments_name ON tournaments(name);
```

## Sample Data

To get started, insert a sample tournament:

```sql
INSERT INTO tournaments (id, name, prize_pool, entry_fee) 
VALUES (
    uuid_generate_v4(), 
    'Championship Pool', 
    100, 
    10
);
```
