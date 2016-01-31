drop table if exists deaths;
create table deaths (
  id integer primary key autoincrement,
  steam_id integer,
  steam_name text,
  dead_to text,
  x integer,
  y integer,
  level integer
);