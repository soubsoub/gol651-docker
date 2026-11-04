-- =============================================================================
-- GOL651 - Lab schema: OR models (structure)
-- =============================================================================
-- Loaded into BOTH gol651 and gol651_exercises after 01_schema.sql / 02_data.sql.
-- This file is idempotent: tables are dropped and recreated on each run.
--
-- Models covered
--   lab_01  Réapprovisionnement  (uses existing tables: inventory, products,
--                                  product_suppliers — no new input tables)
--   lab_02  Production LP        production_resources, production_products
--   lab_03  Transport            transport_nodes, transport_routes
--   lab_04  Affectation          assignment_agents, assignment_tasks,
--                                  assignment_costs
--   lab_05  Flot en réseau       network_nodes, network_arcs
--   lab_06  Planification        planning_products, planning_periods,
--                                  planning_demand
--
-- Output table (gol651_exercises only):
--   lab_results  one row per solve attempt, all models
-- =============================================================================

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- Drop in reverse dependency order
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS planning_demand;
DROP TABLE IF EXISTS planning_periods;
DROP TABLE IF EXISTS planning_products;
DROP TABLE IF EXISTS network_arcs;
DROP TABLE IF EXISTS network_nodes;
DROP TABLE IF EXISTS assignment_costs;
DROP TABLE IF EXISTS assignment_tasks;
DROP TABLE IF EXISTS assignment_agents;
DROP TABLE IF EXISTS transport_routes;
DROP TABLE IF EXISTS transport_nodes;
DROP TABLE IF EXISTS production_products;
DROP TABLE IF EXISTS production_resources;

-- ---------------------------------------------------------------------------
-- lab_02 : Production LP
-- ---------------------------------------------------------------------------
-- Scenario: an entrepôt manufactures 4 product lines.
-- Each product consumes machine hours, labour hours and raw material.
-- Maximize total contribution margin.

CREATE TABLE production_resources (
    resource_id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name           VARCHAR(60)      NOT NULL,
    unit           VARCHAR(20)      NOT NULL,   -- e.g. 'h-machine', 'h-travail', 'kg'
    capacity       DECIMAL(10,2)    NOT NULL,   -- available per week
    CONSTRAINT pk_production_resources PRIMARY KEY (resource_id)
) ENGINE = InnoDB;

CREATE TABLE production_products (
    product_id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name            VARCHAR(60)      NOT NULL,
    margin          DECIMAL(10,2)    NOT NULL,  -- contribution margin per unit ($)
    -- resource consumption: one column per resource (3 here, labelled r1..r3)
    r1_consumption  DECIMAL(10,4)    NOT NULL,  -- resource_id = 1
    r2_consumption  DECIMAL(10,4)    NOT NULL,  -- resource_id = 2
    r3_consumption  DECIMAL(10,4)    NOT NULL,  -- resource_id = 3
    max_demand      INT UNSIGNED     NULL,      -- optional upper bound on production
    CONSTRAINT pk_production_products PRIMARY KEY (product_id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------------
-- lab_03 : Transport
-- ---------------------------------------------------------------------------
-- Scenario: 3 depots (sources) ship goods to 5 distribution centres (sinks).
-- Minimize total shipping cost.

CREATE TABLE transport_nodes (
    node_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(60)       NOT NULL,
    type       CHAR(6)           NOT NULL,   -- 'source' or 'sink'
    capacity   INT               NOT NULL,   -- supply (source) or demand (sink), units
    CONSTRAINT pk_transport_nodes       PRIMARY KEY (node_id),
    CONSTRAINT ck_transport_nodes_type  CHECK (type IN ('source','sink'))
) ENGINE = InnoDB;

CREATE TABLE transport_routes (
    from_node   SMALLINT UNSIGNED NOT NULL,
    to_node     SMALLINT UNSIGNED NOT NULL,
    cost_per_unit DECIMAL(10,2)   NOT NULL,
    CONSTRAINT pk_transport_routes          PRIMARY KEY (from_node, to_node),
    CONSTRAINT fk_transport_routes_from     FOREIGN KEY (from_node)
        REFERENCES transport_nodes (node_id) ON DELETE CASCADE,
    CONSTRAINT fk_transport_routes_to       FOREIGN KEY (to_node)
        REFERENCES transport_nodes (node_id) ON DELETE CASCADE,
    CONSTRAINT ck_transport_routes_cost     CHECK (cost_per_unit >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------------
-- lab_04 : Affectation (Assignment)
-- ---------------------------------------------------------------------------
-- Scenario: 4 agents are assigned to 4 tasks, one-to-one, minimum total cost.

CREATE TABLE assignment_agents (
    agent_id  TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name      VARCHAR(60)      NOT NULL,
    CONSTRAINT pk_assignment_agents PRIMARY KEY (agent_id)
) ENGINE = InnoDB;

CREATE TABLE assignment_tasks (
    task_id   TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name      VARCHAR(60)      NOT NULL,
    CONSTRAINT pk_assignment_tasks PRIMARY KEY (task_id)
) ENGINE = InnoDB;

CREATE TABLE assignment_costs (
    agent_id  TINYINT UNSIGNED NOT NULL,
    task_id   TINYINT UNSIGNED NOT NULL,
    cost      DECIMAL(10,2)    NOT NULL,
    CONSTRAINT pk_assignment_costs          PRIMARY KEY (agent_id, task_id),
    CONSTRAINT fk_assignment_costs_agent    FOREIGN KEY (agent_id)
        REFERENCES assignment_agents (agent_id) ON DELETE CASCADE,
    CONSTRAINT fk_assignment_costs_task     FOREIGN KEY (task_id)
        REFERENCES assignment_tasks (task_id) ON DELETE CASCADE,
    CONSTRAINT ck_assignment_costs_cost     CHECK (cost >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------------
-- lab_05 : Flot en réseau (Network flow)
-- ---------------------------------------------------------------------------
-- Scenario: route goods from 2 sources to 3 sinks through 3 transit nodes.
-- Minimize total arc cost respecting capacity and flow conservation.

CREATE TABLE network_nodes (
    node_id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(60)      NOT NULL,
    type       VARCHAR(10)      NOT NULL,   -- 'source','transit','sink'
    supply     INT              NOT NULL DEFAULT 0,
        -- positive = net supply, negative = net demand, 0 = transit
    CONSTRAINT pk_network_nodes       PRIMARY KEY (node_id),
    CONSTRAINT ck_network_nodes_type  CHECK (type IN ('source','transit','sink'))
) ENGINE = InnoDB;

CREATE TABLE network_arcs (
    arc_id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    from_node   TINYINT UNSIGNED NOT NULL,
    to_node     TINYINT UNSIGNED NOT NULL,
    cost        DECIMAL(10,2)    NOT NULL,
    capacity    INT UNSIGNED     NOT NULL,
    CONSTRAINT pk_network_arcs          PRIMARY KEY (arc_id),
    CONSTRAINT fk_network_arcs_from     FOREIGN KEY (from_node)
        REFERENCES network_nodes (node_id) ON DELETE CASCADE,
    CONSTRAINT fk_network_arcs_to       FOREIGN KEY (to_node)
        REFERENCES network_nodes (node_id) ON DELETE CASCADE,
    CONSTRAINT ck_network_arcs_cost     CHECK (cost >= 0),
    CONSTRAINT ck_network_arcs_capacity CHECK (capacity > 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------------
-- lab_06 : Planification multi-période (Multi-period production planning)
-- ---------------------------------------------------------------------------
-- Scenario: plan production over 6 periods for 3 product families.
-- Constraints: production capacity, inventory balance, non-negativity.
-- Minimize total production + inventory holding cost.

CREATE TABLE planning_products (
    product_id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name            VARCHAR(60)      NOT NULL,
    prod_cost       DECIMAL(10,2)    NOT NULL,  -- cost per unit produced
    holding_cost    DECIMAL(10,2)    NOT NULL,  -- cost per unit held at end of period
    initial_stock   INT UNSIGNED     NOT NULL DEFAULT 0,
    CONSTRAINT pk_planning_products PRIMARY KEY (product_id)
) ENGINE = InnoDB;

CREATE TABLE planning_periods (
    period_id   TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    label       VARCHAR(20)      NOT NULL,   -- e.g. 'P1', 'P2', …
    capacity    INT UNSIGNED     NOT NULL,   -- total production units available this period
    CONSTRAINT pk_planning_periods PRIMARY KEY (period_id)
) ENGINE = InnoDB;

CREATE TABLE planning_demand (
    product_id  TINYINT UNSIGNED NOT NULL,
    period_id   TINYINT UNSIGNED NOT NULL,
    demand      INT UNSIGNED     NOT NULL,
    CONSTRAINT pk_planning_demand           PRIMARY KEY (product_id, period_id),
    CONSTRAINT fk_planning_demand_product   FOREIGN KEY (product_id)
        REFERENCES planning_products (product_id) ON DELETE CASCADE,
    CONSTRAINT fk_planning_demand_period    FOREIGN KEY (period_id)
        REFERENCES planning_periods (period_id) ON DELETE CASCADE
) ENGINE = InnoDB;
