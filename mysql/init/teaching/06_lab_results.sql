-- =============================================================================
-- GOL651 - Lab results table (gol651_exercises only)
-- =============================================================================
-- Written to only once per solve: one row per student attempt.
-- Loaded ONLY into gol651_exercises (see 02_teaching_schema.sh).
-- =============================================================================

SET NAMES utf8mb4;

DROP TABLE IF EXISTS lab_results;

CREATE TABLE lab_results (
    result_id       INT UNSIGNED     NOT NULL AUTO_INCREMENT,
    student_id      VARCHAR(60)      NOT NULL,          -- entered by student at session start
    model_name      VARCHAR(40)      NOT NULL,          -- e.g. 'lab_02_production'
    solved_at       TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(20)      NOT NULL,          -- 'Optimal','Infeasible','Unbounded','Not Solved'
    objective_value DECIMAL(14, 4)   NULL,              -- NULL when infeasible/unbounded
    variables       JSON             NULL,              -- {"x1": 42.5, "x2": 0.0, ...}
    solver_params   JSON             NULL,              -- {"solver": "CBC", "time_limit": 60, ...}
    notes           TEXT             NULL,              -- optional student comment
    CONSTRAINT pk_lab_results           PRIMARY KEY (result_id),
    CONSTRAINT ck_lab_results_status    CHECK (status IN ('Optimal','Infeasible','Unbounded','Not Solved')),
    INDEX idx_lab_results_student  (student_id),
    INDEX idx_lab_results_model    (model_name),
    INDEX idx_lab_results_solved   (solved_at)
) ENGINE = InnoDB;
