-- Sketchpad Arcade: invite-a-friend games (take turns whenever).
-- Players have no accounts. Each phone makes a random secret token and keeps it; only a hash of it is stored.
-- The table is locked away from the public API (RLS on, no policies). Everything goes through the functions
-- below, which check the token and whose turn it is before saving a move.

create extension if not exists pgcrypto with schema extensions;

create table if not exists public.vs_games (
  code        text primary key,
  game        text not null,
  state       jsonb not null,
  turn        smallint not null default 0,          -- seat whose turn it is: 0 (inviter) or 1 (friend)
  status      text not null default 'waiting',      -- waiting (friend hasn't opened it) | playing | done
  winner      smallint,                             -- 0, 1, or -1 for a draw
  version     integer not null default 0,           -- bumps on every move; stops two moves crossing
  seat0       text not null,                        -- sha256 of the inviter's token
  seat1       text,                                 -- sha256 of the friend's token
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists vs_games_updated_idx on public.vs_games (updated_at);
alter table public.vs_games enable row level security;
revoke all on public.vs_games from anon, authenticated;

create or replace function public.vs_hash(p_token text) returns text
language sql immutable set search_path = '' as $$
  select encode(extensions.digest(p_token, 'sha256'), 'hex')
$$;

create or replace function public.vs_public(g public.vs_games) returns jsonb
language sql stable set search_path = '' as $$
  select jsonb_build_object('code', g.code, 'game', g.game, 'state', g.state, 'turn', g.turn,
    'status', g.status, 'winner', g.winner, 'version', g.version, 'updated_at', g.updated_at)
$$;

-- Start a game. Returns the game with its new code.
create or replace function public.vs_create(p_game text, p_state jsonb, p_token text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  alphabet constant text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  c text; g public.vs_games;
begin
  if p_game !~ '^[a-z0-9-]{2,40}$' then raise exception 'bad game'; end if;
  if length(coalesce(p_token, '')) < 20 then raise exception 'bad token'; end if;
  if pg_column_size(p_state) > 20000 then raise exception 'state too big'; end if;
  loop
    c := '';
    for i in 1..6 loop c := c || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1); end loop;
    begin
      insert into public.vs_games (code, game, state, seat0) values (c, p_game, p_state, public.vs_hash(p_token))
      returning * into g;
      exit;
    exception when unique_violation then
      -- try another code
    end;
  end loop;
  return public.vs_public(g) || jsonb_build_object('seat', 0);
end $$;

-- Open a game from its link. The first other phone to open it takes seat 1; after that it's full.
-- Returns the game plus 'seat': 0 or 1 for a player, or -1 if the game is full and this phone isn't in it.
create or replace function public.vs_join(p_code text, p_token text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare g public.vs_games; h text := public.vs_hash(p_token); s int;
begin
  if length(coalesce(p_token, '')) < 20 then raise exception 'bad token'; end if;
  select * into g from public.vs_games where code = upper(p_code) for update;
  if not found then return null; end if;
  if g.seat0 = h then s := 0;
  elsif g.seat1 = h then s := 1;
  elsif g.seat1 is null then
    update public.vs_games set seat1 = h, status = case when status = 'waiting' then 'playing' else status end, updated_at = now()
      where code = g.code returning * into g;
    s := 1;
  else s := -1;
  end if;
  return public.vs_public(g) || jsonb_build_object('seat', s);
end $$;

-- Read one game (for checking whether the other player has moved).
create or replace function public.vs_get(p_code text)
returns jsonb language sql stable security definer set search_path = '' as $$
  select public.vs_public(g) from public.vs_games g where g.code = upper(p_code)
$$;

-- Read up to 30 games at once (for the "Your games" row on the home page).
create or replace function public.vs_list(p_codes text[])
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(public.vs_public(g)), '[]'::jsonb)
  from public.vs_games g where g.code = any (p_codes[1:30])
$$;

-- Save a move. Only the player whose turn it is can move, and only on the version they last saw.
create or replace function public.vs_move(p_code text, p_token text, p_version integer, p_state jsonb,
  p_turn smallint, p_status text, p_winner smallint default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare g public.vs_games; h text := public.vs_hash(p_token); s int;
begin
  if p_status not in ('playing', 'done') or p_turn not in (0, 1) then raise exception 'bad move'; end if;
  if pg_column_size(p_state) > 20000 then raise exception 'state too big'; end if;
  select * into g from public.vs_games where code = upper(p_code) for update;
  if not found then raise exception 'no game'; end if;
  s := case when g.seat0 = h then 0 when g.seat1 = h then 1 else -1 end;
  if s < 0 then raise exception 'not your game'; end if;
  if g.status = 'done' then raise exception 'game over'; end if;
  if g.turn <> s then raise exception 'not your turn'; end if;
  if g.version <> p_version then raise exception 'out of date'; end if;
  update public.vs_games set state = p_state, turn = p_turn, version = version + 1,
    status = case when p_status = 'done' then 'done' when seat1 is null then 'waiting' else 'playing' end,
    winner = case when p_status = 'done' then p_winner else null end, updated_at = now()
    where code = g.code returning * into g;
  return public.vs_public(g) || jsonb_build_object('seat', s);
end $$;

revoke execute on function public.vs_hash(text), public.vs_public(public.vs_games) from public, anon, authenticated;
grant execute on function public.vs_create(text, jsonb, text), public.vs_join(text, text), public.vs_get(text),
  public.vs_list(text[]), public.vs_move(text, text, integer, jsonb, smallint, text, smallint) to anon, authenticated;

-- Note: the Supabase security advisor flags these five functions as SECURITY DEFINER and callable by anon.
-- That is on purpose: they are the only way in, and each one checks the player's token before changing anything.
