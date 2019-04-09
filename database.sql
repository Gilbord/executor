DROP TABLE tasks;
CREATE TABLE tasks (
    task_id SERIAL,
    status varchar(10),
    create_time timestamp without time zone default (now() at time zone 'utc'),
    start_time timestamp without time zone default (now() at time zone 'utc'),
    time_to_execute INT
);