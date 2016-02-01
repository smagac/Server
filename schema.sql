drop table if exists deaths;
create table deaths (
  id integer primary key autoincrement,
  steam_id integer unique,
  steam_name text,
  dead_to text not null,
  x integer not null,
  y integer not null,
  level integer not null
);