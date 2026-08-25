create table if not exists public.chatty_state (
  id text primary key,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default timezone('utc', now())
);

alter table public.chatty_state enable row level security;

revoke all on table public.chatty_state from anon, authenticated;
grant all on table public.chatty_state to service_role;

create or replace function public.touch_chatty_state_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists chatty_state_updated_at on public.chatty_state;
create trigger chatty_state_updated_at
before update on public.chatty_state
for each row execute function public.touch_chatty_state_updated_at();
