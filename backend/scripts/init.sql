-- Initialize database
CREATE DATABASE IF NOT EXISTS disk_inspection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON disk_inspection.* TO 'inspection'@'%';
FLUSH PRIVILEGES;
