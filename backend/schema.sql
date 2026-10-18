-- ============================================================
-- MySQL Schema for Infant Pain Detection System
-- Database: infant_pain_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS infant_pain
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE infant_pain;

-- ── infants ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS infants (
    infant_id   VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    age_days    INT          NOT NULL DEFAULT 0,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (infant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── pain_predictions ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pain_predictions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    infant_id   VARCHAR(50)  NOT NULL,
    pain_level  ENUM('No Pain','Mild Pain','Moderate Pain','Severe Pain') NOT NULL,
    pain_score  FLOAT        NOT NULL COMMENT 'Probability of predicted class (0-1)',
    confidence  FLOAT        NOT NULL COMMENT 'Max softmax confidence (0-1)',
    image_path  TEXT,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_pred_infant FOREIGN KEY (infant_id)
        REFERENCES infants(infant_id) ON DELETE CASCADE,
    INDEX idx_pred_infant_id (infant_id),
    INDEX idx_pred_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── alerts ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    infant_id     VARCHAR(50) NOT NULL,
    pain_level    VARCHAR(50) NOT NULL,
    confidence    FLOAT       NOT NULL,
    alert_status  ENUM('active','acknowledged','resolved') NOT NULL DEFAULT 'active',
    created_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_alert_infant FOREIGN KEY (infant_id)
        REFERENCES infants(infant_id) ON DELETE CASCADE,
    INDEX idx_alert_infant_id (infant_id),
    INDEX idx_alert_status    (alert_status),
    INDEX idx_alert_created_at(created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Sample data (optional) ───────────────────────────────────
-- INSERT INTO infants (infant_id, name, age_days) VALUES ('B101', 'Baby John', 3);
