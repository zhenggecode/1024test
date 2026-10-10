CREATE DATABASE IF NOT EXISTS `1024test`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `1024test`;

CREATE TABLE IF NOT EXISTS accounts (
  username VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  salt BINARY(16) NOT NULL,
  password_hash BINARY(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
  setting_key VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  setting_value VARCHAR(255) NOT NULL
);

INSERT INTO app_settings (setting_key, setting_value)
VALUES ('schema_version', '1')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);
