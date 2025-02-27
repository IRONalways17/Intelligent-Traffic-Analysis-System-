-- Traffic database schema

-- Create database
CREATE DATABASE IF NOT EXISTS traffic_management;
USE traffic_management;

-- Intersections table
CREATE TABLE IF NOT EXISTS intersections (
    intersection_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    main_road_name VARCHAR(100),
    cross_road_name VARCHAR(100),
    camera_ids JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Traffic data table
CREATE TABLE IF NOT EXISTS traffic_data (
    data_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    intersection_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    vehicle_count INT NOT NULL,
    density DECIMAL(10, 6) NOT NULL,
    flow_rate DECIMAL(10, 6),
    avg_vehicle_speed DECIMAL(5, 2),
    pattern_id TINYINT,
    weather_condition VARCHAR(50),
    temperature DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id),
    INDEX idx_intersection_timestamp (intersection_id, timestamp)
);

-- Traffic patterns table
CREATE TABLE IF NOT EXISTS traffic_patterns (
    pattern_id TINYINT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    avg_vehicle_count DECIMAL(10, 2),
    avg_density DECIMAL(10, 6),
    avg_flow_rate DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Signal timing configurations
CREATE TABLE IF NOT EXISTS signal_configurations (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    intersection_id INT NOT NULL,
    pattern_id TINYINT NOT NULL,
    green_time_main INT NOT NULL,
    yellow_time_main INT NOT NULL,
    green_time_cross INT NOT NULL, 
    yellow_time_cross INT NOT NULL,
    cycle_length INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id),
    FOREIGN KEY (pattern_id) REFERENCES traffic_patterns(pattern_id),
    UNIQUE KEY unique_intersection_pattern (intersection_id, pattern_id)
);

-- Signal timing history
CREATE TABLE IF NOT EXISTS signal_timing_history (
    history_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    intersection_id INT NOT NULL,
    config_id INT NOT NULL,
    applied_at DATETIME NOT NULL,
    vehicle_count_before INT,
    vehicle_count_after INT,
    flow_rate_before DECIMAL(10, 6),
    flow_rate_after DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id),
    FOREIGN KEY (config_id) REFERENCES signal_configurations(config_id),
    INDEX idx_intersection_applied (intersection_id, applied_at)
);

-- Initial data insertion for patterns
INSERT INTO traffic_patterns (pattern_id, name, description, avg_vehicle_count, avg_density, avg_flow_rate)
VALUES 
(1, 'Light', 'Low traffic density with free-flowing vehicles', 10.5, 0.000015, 2.5),
(2, 'Moderate', 'Moderate traffic with occasional slowdowns', 25.3, 0.000035, 5.8),
(3, 'Heavy', 'Heavy traffic with reduced speeds', 45.7, 0.000070, 9.2),
(4, 'Congested', 'Congested traffic with significant delays', 75.2, 0.000120, 3.6);

-- Create a view for traffic analytics
CREATE VIEW traffic_analysis_view AS
SELECT 
    i.name AS intersection_name,
    DATE(td.timestamp) AS date,
    HOUR(td.timestamp) AS hour,
    DAYNAME(td.timestamp) AS day_of_week,
    AVG(td.vehicle_count) AS avg_vehicle_count,
    AVG(td.density) AS avg_density,
    AVG(td.flow_rate) AS avg_flow_rate,
    tp.name AS pattern_name
FROM 
    traffic_data td
JOIN 
    intersections i ON td.intersection_id = i.intersection_id
JOIN 
    traffic_patterns tp ON td.pattern_id = tp.pattern_id
GROUP BY 
    i.name, DATE(td.timestamp), HOUR(td.timestamp), DAYNAME(td.timestamp), tp.name;

-- Create stored procedure for optimizing signal timing
DELIMITER //
CREATE PROCEDURE optimize_signal_timing(IN p_intersection_id INT)
BEGIN
    DECLARE current_pattern TINYINT;
    
    -- Get current pattern based on most recent data
    SELECT pattern_id INTO current_pattern
    FROM traffic_data
    WHERE intersection_id = p_intersection_id
    ORDER BY timestamp DESC
    LIMIT 1;
    
    -- Apply optimal signal configuration
    INSERT INTO signal_timing_history (intersection_id, config_id, applied_at, vehicle_count_before)
    SELECT 
        p_intersection_id, 
        sc.config_id, 
        NOW(),
        (SELECT vehicle_count FROM traffic_data 
         WHERE intersection_id = p_intersection_id 
         ORDER BY timestamp DESC LIMIT 1)
    FROM signal_configurations sc
    WHERE sc.intersection_id = p_intersection_id AND sc.pattern_id = current_pattern
    LIMIT 1;
    
    -- Return the applied configuration details
    SELECT 
        sc.green_time_main, sc.yellow_time_main,
        sc.green_time_cross, sc.yellow_time_cross,
        sc.cycle_length, tp.name AS pattern_name
    FROM signal_configurations sc
    JOIN traffic_patterns tp ON sc.pattern_id = tp.pattern_id
    WHERE sc.intersection_id = p_intersection_id AND sc.pattern_id = current_pattern;
END //
DELIMITER ;