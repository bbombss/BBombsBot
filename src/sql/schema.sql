CREATE TABLE IF NOT EXISTS databaseSchema
(
    schemaVersion integer NOT NULL,
    PRIMARY KEY (schemaVersion)
);  

INSERT INTO databaseSchema(schemaVersion)
SELECT 0
WHERE
NOT EXISTS (
SELECT schemaVersion FROM databaseSchema
);

CREATE TABLE IF NOT EXISTS guilds
(
    guildId bigint NOT NULL,
    PRIMARY KEY (guildId)
);

CREATE TABLE IF NOT EXISTS users
(
    userId bigint NOT NULL,
    guildId bigint NOT NULL,
    PRIMARY KEY (userId, guildId),
    FOREIGN KEY (guildId) REFERENCES guilds (guildId)
        ON DELETE CASCADE
);


-- Copyright (C) 2025 BBombs

-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.