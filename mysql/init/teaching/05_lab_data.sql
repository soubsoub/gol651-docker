-- =============================================================================
-- GOL651 - Lab schema: OR models seed data
-- =============================================================================
-- Loaded after 04_lab_schema.sql into BOTH gol651 and gol651_exercises.
-- All numbers are realistic but fictional (Québec warehouse & logistics context).
-- =============================================================================

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- lab_02 : Production LP
-- ---------------------------------------------------------------------------
-- Scenario: Entrepôts Nordique fabrique 4 lignes de produits d'emballage.
-- Ressources : machines (h), main-d'œuvre (h), matière première (kg).
-- Objectif : maximiser la marge de contribution hebdomadaire.

INSERT INTO production_resources (resource_id, name, unit, capacity) VALUES
    (1, 'Heures-machine',          'h/sem',   120),
    (2, 'Heures de main-d''œuvre', 'h/sem',   160),
    (3, 'Matière première',        'kg/sem', 2000);

-- Columns: name, margin($/unit), r1_consumption, r2_consumption, r3_consumption, max_demand
INSERT INTO production_products (product_id, name, margin, r1_consumption, r2_consumption, r3_consumption, max_demand) VALUES
    (1, 'Boîte carton simple',   8.50,  0.5,  0.8,  3.0, 150),
    (2, 'Boîte carton double',  12.00,  0.8,  1.2,  5.5, 100),
    (3, 'Film étirable 18 po',   6.00,  0.3,  0.5,  2.0, 200),
    (4, 'Ruban adhésif 48 mm',   4.50,  0.2,  0.4,  1.5, NULL);

-- ---------------------------------------------------------------------------
-- lab_03 : Transport
-- ---------------------------------------------------------------------------
-- Scenario: 3 dépôts expédient vers 5 centres de distribution.
-- Minimiser le coût total de transport.
-- Nodes 1-3 = sources (dépôts), nodes 4-8 = sinks (centres de distribution).

INSERT INTO transport_nodes (node_id, name, type, capacity) VALUES
    -- sources (supply)
    (1, 'Dépôt Montréal',         'source',  350),
    (2, 'Dépôt Québec',           'source',  280),
    (3, 'Dépôt Sherbrooke',       'source',  200),
    -- sinks (demand)
    (4, 'Centre Laval',           'sink',    150),
    (5, 'Centre Longueuil',       'sink',    120),
    (6, 'Centre Gatineau',        'sink',    110),
    (7, 'Centre Trois-Rivières',  'sink',    180),
    (8, 'Centre Saguenay',        'sink',    270);

-- Cost matrix ($/unit): every source → every sink
INSERT INTO transport_routes (from_node, to_node, cost_per_unit) VALUES
    -- Montréal → centres
    (1, 4,  2.10), (1, 5,  2.80), (1, 6,  4.50), (1, 7,  5.20), (1, 8,  9.80),
    -- Québec → centres
    (2, 4,  5.60), (2, 5,  6.30), (2, 6,  3.80), (2, 7,  2.20), (2, 8,  4.10),
    -- Sherbrooke → centres
    (3, 4,  4.20), (3, 5,  3.50), (3, 6,  5.10), (3, 7,  4.80), (3, 8, 11.20);

-- ---------------------------------------------------------------------------
-- lab_04 : Affectation
-- ---------------------------------------------------------------------------
-- Scenario: 4 agents (préposés) assignés à 4 tâches de manutention.
-- Chaque agent a un coût différent pour chaque tâche (formation, distance, etc.).
-- Objectif : minimiser le coût total, chaque agent fait exactement une tâche.

INSERT INTO assignment_agents (agent_id, name) VALUES
    (1, 'Ahmed Khelil'),
    (2, 'Brigitte Ouellet'),
    (3, 'Carlos Mendez'),
    (4, 'Diana Tremblay');

INSERT INTO assignment_tasks (task_id, name) VALUES
    (1, 'Réception des marchandises'),
    (2, 'Préparation des commandes'),
    (3, 'Chargement des camions'),
    (4, 'Inventaire et étiquetage');

-- Cost matrix ($ per shift): rows = agents, columns = tasks
INSERT INTO assignment_costs (agent_id, task_id, cost) VALUES
    (1, 1, 150), (1, 2, 210), (1, 3, 190), (1, 4, 170),
    (2, 1, 180), (2, 2, 130), (2, 3, 220), (2, 4, 160),
    (3, 1, 200), (3, 2, 180), (3, 3, 140), (3, 4, 230),
    (4, 1, 160), (4, 2, 190), (4, 3, 175), (4, 4, 120);

-- ---------------------------------------------------------------------------
-- lab_05 : Flot en réseau
-- ---------------------------------------------------------------------------
-- Scenario: réseau de distribution avec 2 sources, 3 nœuds de transit, 3 puits.
-- supply > 0 (source), supply = 0 (transit), supply < 0 (sink/demand).

INSERT INTO network_nodes (node_id, name, type, supply) VALUES
    (1, 'Usine Montréal',           'source',   300),
    (2, 'Usine Québec',             'source',   250),
    (3, 'Hub Laval',                'transit',    0),
    (4, 'Hub Drummondville',        'transit',    0),
    (5, 'Hub Sherbrooke',           'transit',    0),
    (6, 'Client Gatineau',          'sink',    -150),
    (7, 'Client Trois-Rivières',    'sink',    -200),
    (8, 'Client Saguenay',          'sink',    -200);

-- Arcs: (from, to, cost/unit, capacity)
INSERT INTO network_arcs (from_node, to_node, cost, capacity) VALUES
    -- Sources → Hubs
    (1, 3,  3.0, 200), (1, 4,  4.5, 150),
    (2, 4,  2.5, 180), (2, 5,  3.2, 200),
    -- Hubs → Hubs
    (3, 4,  1.5, 100), (4, 5,  2.0,  80),
    -- Hubs → Sinks
    (3, 6,  2.8, 150), (4, 7,  3.1, 200),
    (5, 7,  2.4, 120), (5, 8,  3.5, 220),
    (4, 8,  5.0, 100);

-- ---------------------------------------------------------------------------
-- lab_06 : Planification multi-période
-- ---------------------------------------------------------------------------
-- Scenario: planifier la production sur 6 périodes pour 3 familles de produits.
-- Minimiser coût de production + coût de détention des stocks.

INSERT INTO planning_products (product_id, name, prod_cost, holding_cost, initial_stock) VALUES
    (1, 'Famille A — Palettes',     12.00, 1.50,  50),
    (2, 'Famille B — Emballage',     8.00, 0.80, 100),
    (3, 'Famille C — Sécurité',     15.00, 2.00,  30);

INSERT INTO planning_periods (period_id, label, capacity) VALUES
    (1, 'P1 — Jan', 500),
    (2, 'P2 — Fév', 500),
    (3, 'P3 — Mar', 600),
    (4, 'P4 — Avr', 600),
    (5, 'P5 — Mai', 550),
    (6, 'P6 — Jun', 550);

-- Demand matrix: product × period
INSERT INTO planning_demand (product_id, period_id, demand) VALUES
    -- Famille A
    (1, 1,  80), (1, 2,  90), (1, 3, 120), (1, 4, 100), (1, 5,  85), (1, 6,  95),
    -- Famille B
    (2, 1, 150), (2, 2, 130), (2, 3, 180), (2, 4, 160), (2, 5, 140), (2, 6, 170),
    -- Famille C
    (3, 1,  60), (3, 2,  70), (3, 3,  80), (3, 4,  65), (3, 5,  75), (3, 6,  90);
