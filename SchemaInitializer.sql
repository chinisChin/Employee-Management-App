-- -----------------------------------------------------
-- Schema Setup
-- -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS `employee`
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

USE `employee`;

-- -----------------------------------------------------
-- Table `employees`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `employees` (
  `employee_id` VARCHAR(50) NOT NULL,
  `employee_name` VARCHAR(150) NOT NULL,
  `department` VARCHAR(100) NULL DEFAULT NULL,
  `position` VARCHAR(100) NULL DEFAULT NULL,
  `monthly_salary` DECIMAL(10,2) NULL DEFAULT NULL,
  PRIMARY KEY (`employee_id`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `attendance_logs`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `attendance_logs` (
  `log_id` INT NOT NULL AUTO_INCREMENT,
  `employee_id` VARCHAR(50) NULL DEFAULT NULL,
  `date` DATE NOT NULL,
  `attendance_status` VARCHAR(50) NULL DEFAULT NULL,
  `hours_worked` DECIMAL(5,2) NULL DEFAULT NULL,
  `tasks_completed` DECIMAL(5,2) NULL DEFAULT NULL,
  `performance_rating` DECIMAL(3,2) NULL DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  -- Optional but highly recommended: Links logs back to the employees table
  CONSTRAINT `fk_attendance_logs_employees`
    FOREIGN KEY (`employee_id`)
    REFERENCES `employees` (`employee_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB;