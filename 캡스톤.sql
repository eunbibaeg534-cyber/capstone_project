USE capstone_project;

-- 1. risk_grid (부모 테이블 먼저)
CREATE TABLE `risk_grid` (
    `grid_id` INT NOT NULL AUTO_INCREMENT,
    `center_latitude` DOUBLE,
    `center_longitude` DOUBLE,
    `accident_count` INT DEFAULT 0,
    `serious_accident_count` INT DEFAULT 0,
    `death_accident_count` INT DEFAULT 0,
    `risk_score` DOUBLE,
    `risk_level` INT,
    `max_latitude` DOUBLE,
    `min_longitude` DOUBLE,
    `max_longitude` DOUBLE,
    `min_latitude` DOUBLE,
    PRIMARY KEY (`grid_id`)
);

-- 2. accident (FK 포함)
CREATE TABLE `accident` (
    `accident_id` INT NOT NULL AUTO_INCREMENT,
    `latitude` DOUBLE NOT NULL,
    `longitude` DOUBLE NOT NULL,
    `accident_count` INT DEFAULT 0,
    `serious_injury` INT DEFAULT 0,
    `death` INT DEFAULT 0,
    `schoolzone` BOOLEAN DEFAULT FALSE,
    `grid_id` INT NOT NULL,
    PRIMARY KEY (`accident_id`),
    FOREIGN KEY (`grid_id`) REFERENCES `risk_grid`(`grid_id`)
);

-- 3. hospital (수정 반영 완료)
CREATE TABLE `hospital` (
    `hospital_id` VARCHAR(50) NOT NULL,
    `hospital_name` VARCHAR(100),
    `address` VARCHAR(255),
    `region` VARCHAR(100),
    `latitude` DOUBLE,
    `longitude` DOUBLE,
    `emergency_room_yn` BOOLEAN,
    `operating_hours` TEXT,
    `hospital_status` VARCHAR(20),
    `phone` VARCHAR(20),
    PRIMARY KEY (`hospital_id`)
);

-- 4. chatbot
CREATE TABLE `chatbot` (
    `chat_id` INT NOT NULL AUTO_INCREMENT,
    `user_input` TEXT,
    `bot_response` TEXT,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`chat_id`)
);
ALTER TABLE accident
ADD COLUMN accident_type VARCHAR(50);

ALTER TABLE hospital
ADD COLUMN operating_hours_imputed BOOLEAN;

ALTER TABLE accident
ADD COLUMN region_name VARCHAR(100),
ADD COLUMN spot_name VARCHAR(200);

DESC risk_grid;
DESC accident;
DESC hospital;
DESC chatbot;

