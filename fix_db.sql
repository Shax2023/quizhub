-- databasega ulanishdan keyin ishga tushiriladi

-- 1. schema fix
ALTER SCHEMA public OWNER TO postgres;

-- 2. permission berish
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO quizhub_user;

GRANT ALL PRIVILEGES ON DATABASE quizhub TO postgres;
GRANT ALL PRIVILEGES ON DATABASE quizhub TO quizhub_user;

-- 3. optional safety
ALTER ROLE postgres WITH SUPERUSER;