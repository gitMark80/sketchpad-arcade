-- Guess My Doodle saves drawings, so allow bigger saved games (100 KB instead of 20 KB).
create or replace function public.vs_create(p_game text, p_state jsonb, p_token text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  alphabet constant text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  c text; g public.vs_games;
begin
  if p_game !~ '^[a-z0-9-]{2,40}$' then raise exception 'bad game'; end if;
  if length(coalesce(p_token, '')) < 20 then raise exception 'bad token'; end if;
  if pg_column_size(p_state) > 100000 then raise exception 'state too big'; end if;
  loop
    c := '';
    for i in 1..6 loop c := c || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1); end loop;
    begin
      insert into public.vs_games (code, game, state, seat0) values (c, p_game, p_state, public.vs_hash(p_token))
      returning * into g;
      exit;
    exception when unique_violation then
    end;
  end loop;
  return public.vs_public(g) || jsonb_build_object('seat', 0);
end $$;

create or replace function public.vs_move(p_code text, p_token text, p_version integer, p_state jsonb,
  p_turn smallint, p_status text, p_winner smallint default null)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare g public.vs_games; h text := public.vs_hash(p_token); s int;
begin
  if p_status not in ('playing', 'done') or p_turn not in (0, 1) then raise exception 'bad move'; end if;
  if pg_column_size(p_state) > 100000 then raise exception 'state too big'; end if;
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
