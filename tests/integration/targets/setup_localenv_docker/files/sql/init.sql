-- Create users to manage database connections
CREATE USER con1 WITH PASSWORD 'con1';
CREATE USER con2 WITH PASSWORD 'con2';
CREATE USER con3 WITH PASSWORD 'con3';
CREATE USER con4 WITH PASSWORD 'con4';
CREATE USER con5 WITH PASSWORD 'con5';

-- Create another user to manage credential rotation
-- CREATE USER usr_to_rotate with PASSWORD 'SuperSecret' SUPERUSER;

-- Create users to manage static roles
CREATE USER role1;
CREATE USER role2;
CREATE USER role3;
CREATE USER role4;
CREATE USER role5;
