-------------------------------------------------------------
-- FreshLink Kamonyi District Seed Data
-- Execute after database/schema.sql and database/indexes.sql.
-------------------------------------------------------------

INSERT INTO users
    (user_id, username, password_hash, role, is_active, last_login, created_at, email)
VALUES
    (1, 'super.admin', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'ADMIN', TRUE, '2026-07-15 08:30:00', '2026-06-01 08:00:00', 'super.admin@freshlink.rw'),
    (2, 'kamonyi.admin.east', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'ADMIN', TRUE, '2026-07-16 09:15:00', '2026-06-01 08:10:00', 'east.admin@freshlink.rw'),
    (3, 'kamonyi.admin.west', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'ADMIN', TRUE, '2026-07-16 10:05:00', '2026-06-01 08:20:00', 'west.admin@freshlink.rw'),
    (4, 'hub.central.manager', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'HUB_OPERATOR', TRUE, '2026-07-16 07:45:00', '2026-06-02 08:00:00', 'central.hub@freshlink.rw'),
    (5, 'hub.runda.manager', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'HUB_OPERATOR', TRUE, '2026-07-15 15:10:00', '2026-06-02 08:10:00', 'runda.hub@freshlink.rw'),
    (6, 'hub.musambira.manager', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'HUB_OPERATOR', TRUE, '2026-07-15 14:30:00', '2026-06-02 08:20:00', 'musambira.hub@freshlink.rw'),
    (7, 'hub.kayenzi.manager', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'HUB_OPERATOR', TRUE, '2026-07-14 16:25:00', '2026-06-02 08:30:00', 'kayenzi.hub@freshlink.rw'),
    (8, 'hub.mugina.manager', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'HUB_OPERATOR', TRUE, '2026-07-14 12:05:00', '2026-06-02 08:40:00', 'mugina.hub@freshlink.rw'),
    (9, 'kamonyi.fresh.logistics', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'TRANSPORTER', TRUE, '2026-07-16 06:50:00', '2026-06-03 08:00:00', 'dispatch@kamonyifresh.rw'),
    (10, 'southern.agro.transport', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'TRANSPORTER', TRUE, '2026-07-16 07:05:00', '2026-06-03 08:10:00', 'ops@southernagro.rw'),
    (11, 'rwanda.cold.chain', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'TRANSPORTER', TRUE, '2026-07-15 18:35:00', '2026-06-03 08:20:00', 'kamonyi@rwandacoldchain.rw'),
    (12, 'green.route.logistics', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'TRANSPORTER', TRUE, '2026-07-15 13:20:00', '2026-06-03 08:30:00', 'dispatch@greenroute.rw'),
    (13, 'kamonyi.coop.transport', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'TRANSPORTER', TRUE, '2026-07-14 11:10:00', '2026-06-03 08:40:00', 'transport@kamonyicoop.rw'),
    (100, 'farmer.marie.uwase', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-12 07:00:00', '2026-06-05 08:00:00', 'marie.uwase@example.rw'),
    (101, 'farmer.jean.ndayisaba', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-12 07:10:00', '2026-06-05 08:05:00', 'jean.ndayisaba@example.rw'),
    (102, 'farmer.claudine.mukamana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 06:55:00', '2026-06-05 08:10:00', 'claudine.mukamana@example.rw'),
    (103, 'farmer.emmanuel.habimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 07:20:00', '2026-06-05 08:15:00', 'emmanuel.habimana@example.rw'),
    (104, 'farmer.aline.niyonsenga', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 07:35:00', '2026-06-05 08:20:00', 'aline.niyonsenga@example.rw'),
    (105, 'farmer.theoneste.nsengiyumva', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 08:25:00', 'theoneste.nsengiyumva@example.rw'),
    (106, 'farmer.beatrice.mukeshimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-11 09:40:00', '2026-06-05 08:30:00', 'beatrice.mukeshimana@example.rw'),
    (107, 'farmer.patrick.hategekimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 08:35:00', 'patrick.hategekimana@example.rw'),
    (108, 'farmer.chantal.nyirahabimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-11 10:20:00', '2026-06-05 08:40:00', 'chantal.nyirahabimana@example.rw'),
    (109, 'farmer.celestin.rugamba', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-10 17:15:00', '2026-06-05 08:45:00', 'celestin.rugamba@example.rw'),
    (110, 'farmer.angelique.mutuyimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-12 08:25:00', '2026-06-05 08:50:00', 'angelique.mutuyimana@example.rw'),
    (111, 'farmer.bosco.tuyisenge', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 08:55:00', 'bosco.tuyisenge@example.rw'),
    (112, 'farmer.diane.uwimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 08:10:00', '2026-06-05 09:00:00', 'diane.uwimana@example.rw'),
    (113, 'farmer.fidele.nzeyimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 09:05:00', 'fidele.nzeyimana@example.rw'),
    (114, 'farmer.francoise.mukantabana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-12 12:00:00', '2026-06-05 09:10:00', 'francoise.mukantabana@example.rw'),
    (115, 'farmer.gaspard.rukundo', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 05:45:00', '2026-06-05 09:15:00', 'gaspard.rukundo@example.rw'),
    (116, 'farmer.jacqueline.iradukunda', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 09:20:00', 'jacqueline.iradukunda@example.rw'),
    (117, 'farmer.leonidas.munyaneza', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-14 06:30:00', '2026-06-05 09:25:00', 'leonidas.munyaneza@example.rw'),
    (118, 'farmer.odette.niyitegeka', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-13 13:45:00', '2026-06-05 09:30:00', 'odette.niyitegeka@example.rw'),
    (119, 'farmer.sylvere.ngabonziza', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 09:35:00', 'sylvere.ngabonziza@example.rw'),
    (120, 'farmer.valentine.mukamurenzi', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-14 07:50:00', '2026-06-05 09:40:00', 'valentine.mukamurenzi@example.rw'),
    (121, 'farmer.didier.nshimiyimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-12 15:05:00', '2026-06-05 09:45:00', 'didier.nshimiyimana@example.rw'),
    (122, 'farmer.esther.ishimwe', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 09:50:00', 'esther.ishimwe@example.rw'),
    (123, 'farmer.aloys.hakizimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 06:40:00', '2026-06-05 09:55:00', 'aloys.hakizimana@example.rw'),
    (124, 'farmer.epiphanie.nyiransabimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-14 18:10:00', '2026-06-05 10:00:00', 'epiphanie.nyiransabimana@example.rw'),
    (125, 'farmer.jeanette.mukandayisenga', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 10:05:00', 'jeanette.mukandayisenga@example.rw'),
    (126, 'farmer.innocent.habyarimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 11:35:00', '2026-06-05 10:10:00', 'innocent.habyarimana@example.rw'),
    (127, 'farmer.mediatrice.uwase', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 09:05:00', '2026-06-05 10:15:00', 'mediatrice.uwase@example.rw'),
    (128, 'farmer.protais.kayitare', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 10:20:00', 'protais.kayitare@example.rw'),
    (129, 'farmer.sandrine.mukamana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-14 07:05:00', '2026-06-05 10:25:00', 'sandrine.mukamana@example.rw'),
    (130, 'farmer.gilbert.nsabimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 16:25:00', '2026-06-05 10:30:00', 'gilbert.nsabimana@example.rw'),
    (131, 'farmer.olive.uwitonze', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 10:35:00', 'olive.uwitonze@example.rw'),
    (132, 'farmer.philippe.mugenzi', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 08:55:00', '2026-06-05 10:40:00', 'philippe.mugenzi@example.rw'),
    (133, 'farmer.regine.niyigena', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-15 10:15:00', '2026-06-05 10:45:00', 'regine.niyigena@example.rw'),
    (134, 'farmer.samuel.nkurunziza', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 10:50:00', 'samuel.nkurunziza@example.rw'),
    (135, 'farmer.alphonsine.mukarushema', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 06:15:00', '2026-06-05 10:55:00', 'alphonsine.mukarushema@example.rw'),
    (136, 'farmer.bonaventure.ndagijimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 06:35:00', '2026-06-05 11:00:00', 'bonaventure.ndagijimana@example.rw'),
    (137, 'farmer.claire.mutesi', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 11:05:00', 'claire.mutesi@example.rw'),
    (138, 'farmer.damascene.rwema', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 07:25:00', '2026-06-05 11:10:00', 'damascene.rwema@example.rw'),
    (139, 'farmer.eugenie.nyirahabineza', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 08:15:00', '2026-06-05 11:15:00', 'eugenie.nyirahabineza@example.rw'),
    (140, 'farmer.florien.mugisha', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 11:20:00', 'florien.mugisha@example.rw'),
    (141, 'farmer.grace.nyiransengiyumva', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 08:45:00', '2026-06-05 11:25:00', 'grace.nyiransengiyumva@example.rw'),
    (142, 'farmer.hassan.niyonzima', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 09:30:00', '2026-06-05 11:30:00', 'hassan.niyonzima@example.rw'),
    (143, 'farmer.irma.mukazayire', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 11:35:00', 'irma.mukazayire@example.rw'),
    (144, 'farmer.justin.twagirimana', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 10:20:00', '2026-06-05 11:40:00', 'justin.twagirimana@example.rw'),
    (145, 'farmer.louise.mukamugema', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 11:05:00', '2026-06-05 11:45:00', 'louise.mukamugema@example.rw'),
    (146, 'farmer.martin.habumugisha', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, NULL, '2026-06-05 11:50:00', 'martin.habumugisha@example.rw'),
    (147, 'farmer.nadine.uwamahoro', '$2b$12$freshlinkseedhash000000000000000000000000000000000000000000', 'FARMER', TRUE, '2026-07-16 12:10:00', '2026-06-05 11:55:00', 'nadine.uwamahoro@example.rw');

INSERT INTO sectors
    (sector_id, name, district, cell, village)
VALUES
    (1, 'Gacurabwenge', 'Kamonyi', 'Gihinga', 'Nyagisozi'),
    (2, 'Karama', 'Kamonyi', 'Buhoro', 'Kabeza'),
    (3, 'Kayenzi', 'Kamonyi', 'Bugarama', 'Kivumu'),
    (4, 'Kayumbu', 'Kamonyi', 'Busoro', 'Rugarama'),
    (5, 'Mugina', 'Kamonyi', 'Jenda', 'Nyagacyamo'),
    (6, 'Musambira', 'Kamonyi', 'Kigusa', 'Rugogwe'),
    (7, 'Ngamba', 'Kamonyi', 'Kabuga', 'Cyanya'),
    (8, 'Nyamiyaga', 'Kamonyi', 'Bibungo', 'Gitega'),
    (9, 'Nyarubaka', 'Kamonyi', 'Kambyeyi', 'Gaseke'),
    (10, 'Rugalika', 'Kamonyi', 'Sheli', 'Nyagacyamu'),
    (11, 'Rukoma', 'Kamonyi', 'Buguri', 'Kagasa'),
    (12, 'Runda', 'Kamonyi', 'Ruyenzi', 'Nyagacaca');

INSERT INTO farmers
    (farmer_id, user_id, sector_id, name, phone, cell, village)
VALUES
    (1, 100, 1, 'Marie Uwase', '0784100001', 'Gihinga', 'Nyagisozi'),
    (2, 101, 1, 'Jean Ndayisaba', '0784100002', 'Nkingo', 'Kigarama'),
    (3, 102, 1, 'Claudine Mukamana', '0784100003', 'Gihinga', 'Ruhango'),
    (4, 103, 1, 'Emmanuel Habimana', '0784100004', 'Kabuye', 'Kabeza'),
    (5, 104, 2, 'Aline Niyonsenga', '0784100005', 'Buhoro', 'Kabeza'),
    (6, 105, 2, 'Theoneste Nsengiyumva', '0784100006', 'Muganza', 'Nyagahinga'),
    (7, 106, 2, 'Beatrice Mukeshimana', '0784100007', 'Buhoro', 'Karambi'),
    (8, 107, 2, 'Patrick Hategekimana', '0784100008', 'Nyamirembe', 'Kigarama'),
    (9, 108, 3, 'Chantal Nyirahabimana', '0784100009', 'Bugarama', 'Kivumu'),
    (10, 109, 3, 'Celestin Rugamba', '0784100010', 'Cubi', 'Gisiza'),
    (11, 110, 3, 'Angelique Mutuyimana', '0784100011', 'Bugarama', 'Gitwa'),
    (12, 111, 3, 'Bosco Tuyisenge', '0784100012', 'Kayenzi', 'Rugarama'),
    (13, 112, 4, 'Diane Uwimana', '0784100013', 'Busoro', 'Rugarama'),
    (14, 113, 4, 'Fidele Nzeyimana', '0784100014', 'Kirwa', 'Nyakabungo'),
    (15, 114, 4, 'Francoise Mukantabana', '0784100015', 'Busoro', 'Kagano'),
    (16, 115, 4, 'Gaspard Rukundo', '0784100016', 'Nyamirama', 'Gatovu'),
    (17, 116, 5, 'Jacqueline Iradukunda', '0784100017', 'Jenda', 'Nyagacyamo'),
    (18, 117, 5, 'Leonidas Munyaneza', '0784100018', 'Mugina', 'Kabaya'),
    (19, 118, 5, 'Odette Niyitegeka', '0784100019', 'Mbati', 'Rugarama'),
    (20, 119, 5, 'Sylvere Ngabonziza', '0784100020', 'Jenda', 'Gatagara'),
    (21, 120, 6, 'Valentine Mukamurenzi', '0784100021', 'Kigusa', 'Rugogwe'),
    (22, 121, 6, 'Didier Nshimiyimana', '0784100022', 'Musambira', 'Karambo'),
    (23, 122, 6, 'Esther Ishimwe', '0784100023', 'Kivumu', 'Nyakabungo'),
    (24, 123, 6, 'Aloys Hakizimana', '0784100024', 'Kigusa', 'Rugarama'),
    (25, 124, 7, 'Epiphanie Nyiransabimana', '0784100025', 'Kabuga', 'Cyanya'),
    (26, 125, 7, 'Jeanette Mukandayisenga', '0784100026', 'Marembo', 'Kagarama'),
    (27, 126, 7, 'Innocent Habyarimana', '0784100027', 'Kabuga', 'Buhoro'),
    (28, 127, 7, 'Mediatrice Uwase', '0784100028', 'Ruyenzi', 'Kanyinya'),
    (29, 128, 8, 'Protais Kayitare', '0784100029', 'Bibungo', 'Gitega'),
    (30, 129, 8, 'Sandrine Mukamana', '0784100030', 'Mukinga', 'Rugarika'),
    (31, 130, 8, 'Gilbert Nsabimana', '0784100031', 'Bibungo', 'Kagano'),
    (32, 131, 8, 'Olive Uwitonze', '0784100032', 'Nyamiyaga', 'Karama'),
    (33, 132, 9, 'Philippe Mugenzi', '0784100033', 'Kambyeyi', 'Gaseke'),
    (34, 133, 9, 'Regine Niyigena', '0784100034', 'Nyarubaka', 'Ruhina'),
    (35, 134, 9, 'Samuel Nkurunziza', '0784100035', 'Kambyeyi', 'Kigarama'),
    (36, 135, 9, 'Alphonsine Mukarushema', '0784100036', 'Gihara', 'Nyabitare'),
    (37, 136, 10, 'Bonaventure Ndagijimana', '0784100037', 'Sheli', 'Nyagacyamu'),
    (38, 137, 10, 'Claire Mutesi', '0784100038', 'Rugalika', 'Karambo'),
    (39, 138, 10, 'Damascene Rwema', '0784100039', 'Sheli', 'Rukambura'),
    (40, 139, 10, 'Eugenie Nyirahabineza', '0784100040', 'Nkingo', 'Kivumu'),
    (41, 140, 11, 'Florien Mugisha', '0784100041', 'Buguri', 'Kagasa'),
    (42, 141, 11, 'Grace Nyiransengiyumva', '0784100042', 'Murehe', 'Nyagisozi'),
    (43, 142, 11, 'Hassan Niyonzima', '0784100043', 'Buguri', 'Kagarama'),
    (44, 143, 11, 'Irma Mukazayire', '0784100044', 'Rukoma', 'Gatovu'),
    (45, 144, 12, 'Justin Twagirimana', '0784100045', 'Ruyenzi', 'Nyagacaca'),
    (46, 145, 12, 'Louise Mukamugema', '0784100046', 'Gihara', 'Kabeza'),
    (47, 146, 12, 'Martin Habumugisha', '0784100047', 'Runda', 'Biryogo'),
    (48, 147, 12, 'Nadine Uwamahoro', '0784100048', 'Ruyenzi', 'Gasharu');

INSERT INTO farmer_admin_profiles
    (farmer_id, national_id, registration_status, registered_at)
VALUES
    (1, '1198080000000001', 'ACTIVE', '2026-06-05 08:00:00'),
    (2, '1198080000000002', 'ACTIVE', '2026-06-05 08:05:00'),
    (3, '1198080000000003', 'ACTIVE', '2026-06-05 08:10:00'),
    (4, '1198080000000004', 'ACTIVE', '2026-06-05 08:15:00'),
    (5, '1198080000000005', 'ACTIVE', '2026-06-05 08:20:00'),
    (6, '1198080000000006', 'ACTIVE', '2026-06-05 08:25:00'),
    (7, '1198080000000007', 'ACTIVE', '2026-06-05 08:30:00'),
    (8, '1198080000000008', 'ACTIVE', '2026-06-05 08:35:00'),
    (9, '1198080000000009', 'ACTIVE', '2026-06-05 08:40:00'),
    (10, '1198080000000010', 'ACTIVE', '2026-06-05 08:45:00'),
    (11, '1198080000000011', 'ACTIVE', '2026-06-05 08:50:00'),
    (12, '1198080000000012', 'ACTIVE', '2026-06-05 08:55:00'),
    (13, '1198080000000013', 'ACTIVE', '2026-06-05 09:00:00'),
    (14, '1198080000000014', 'ACTIVE', '2026-06-05 09:05:00'),
    (15, '1198080000000015', 'ACTIVE', '2026-06-05 09:10:00'),
    (16, '1198080000000016', 'ACTIVE', '2026-06-05 09:15:00'),
    (17, '1198080000000017', 'ACTIVE', '2026-06-05 09:20:00'),
    (18, '1198080000000018', 'ACTIVE', '2026-06-05 09:25:00'),
    (19, '1198080000000019', 'ACTIVE', '2026-06-05 09:30:00'),
    (20, '1198080000000020', 'ACTIVE', '2026-06-05 09:35:00'),
    (21, '1198080000000021', 'ACTIVE', '2026-06-05 09:40:00'),
    (22, '1198080000000022', 'ACTIVE', '2026-06-05 09:45:00'),
    (23, '1198080000000023', 'ACTIVE', '2026-06-05 09:50:00'),
    (24, '1198080000000024', 'ACTIVE', '2026-06-05 09:55:00'),
    (25, '1198080000000025', 'ACTIVE', '2026-06-05 10:00:00'),
    (26, '1198080000000026', 'ACTIVE', '2026-06-05 10:05:00'),
    (27, '1198080000000027', 'ACTIVE', '2026-06-05 10:10:00'),
    (28, '1198080000000028', 'ACTIVE', '2026-06-05 10:15:00'),
    (29, '1198080000000029', 'ACTIVE', '2026-06-05 10:20:00'),
    (30, '1198080000000030', 'ACTIVE', '2026-06-05 10:25:00'),
    (31, '1198080000000031', 'ACTIVE', '2026-06-05 10:30:00'),
    (32, '1198080000000032', 'ACTIVE', '2026-06-05 10:35:00'),
    (33, '1198080000000033', 'ACTIVE', '2026-06-05 10:40:00'),
    (34, '1198080000000034', 'ACTIVE', '2026-06-05 10:45:00'),
    (35, '1198080000000035', 'ACTIVE', '2026-06-05 10:50:00'),
    (36, '1198080000000036', 'ACTIVE', '2026-06-05 10:55:00'),
    (37, '1198080000000037', 'ACTIVE', '2026-06-05 11:00:00'),
    (38, '1198080000000038', 'ACTIVE', '2026-06-05 11:05:00'),
    (39, '1198080000000039', 'ACTIVE', '2026-06-05 11:10:00'),
    (40, '1198080000000040', 'ACTIVE', '2026-06-05 11:15:00'),
    (41, '1198080000000041', 'ACTIVE', '2026-06-05 11:20:00'),
    (42, '1198080000000042', 'ACTIVE', '2026-06-05 11:25:00'),
    (43, '1198080000000043', 'ACTIVE', '2026-06-05 11:30:00'),
    (44, '1198080000000044', 'ACTIVE', '2026-06-05 11:35:00'),
    (45, '1198080000000045', 'ACTIVE', '2026-06-05 11:40:00'),
    (46, '1198080000000046', 'ACTIVE', '2026-06-05 11:45:00'),
    (47, '1198080000000047', 'ACTIVE', '2026-06-05 11:50:00'),
    (48, '1198080000000048', 'ACTIVE', '2026-06-05 11:55:00');

INSERT INTO transporters
    (transporter_id, user_id, sector_id, name, phone)
VALUES
    (1, 9, 1, 'Kamonyi Fresh Logistics Ltd', '0788200001'),
    (2, 10, 6, 'Southern Agro Transport', '0788200002'),
    (3, 11, 12, 'Rwanda Cold Chain Transport', '0788200003'),
    (4, 12, 3, 'Green Route Logistics', '0788200004'),
    (5, 13, 9, 'Kamonyi Cooperative Transport', '0788200005');

INSERT INTO cold_hubs
    (hub_id, sector_id, name, phone, total_capacity_kg, available_capacity_kg, operating_status)
VALUES
    (1, 1, 'Kamonyi Central Cold Hub', '0788300001', 65000, 41200, 'OPEN'),
    (2, 12, 'Runda Fresh Storage Center', '0788300002', 52000, 31750, 'OPEN'),
    (3, 6, 'Musambira Agro Cold Hub', '0788300003', 48000, 28600, 'OPEN'),
    (4, 3, 'Kayenzi Farmers Cooling Center', '0788300004', 36000, 21400, 'OPEN'),
    (5, 5, 'Mugina Cold Storage Facility', '0788300005', 42000, 26100, 'OPEN'),
    (6, 9, 'Nyarubaka Produce Cooling Point', '0788300006', 24000, 16800, 'OPEN');

INSERT INTO cold_hub_accounts
    (hub_id, user_id)
VALUES
    (1, 4),
    (2, 5),
    (3, 6),
    (4, 7),
    (5, 8);

INSERT INTO trucks
    (truck_id, transporter_id, plate_number, capacity_kg, sector_id, status)
VALUES
    (1, 1, 'RAE 102F', 6500, 1, 'BUSY'),
    (2, 1, 'RAE 214G', 4200, 2, 'AVAILABLE'),
    (3, 2, 'RAF 305C', 7200, 6, 'BUSY'),
    (4, 2, 'RAF 411D', 5000, 5, 'AVAILABLE'),
    (5, 3, 'RAG 612H', 9000, 12, 'BUSY'),
    (6, 3, 'RAG 730J', 6000, 10, 'MAINTENANCE'),
    (7, 4, 'RAH 144K', 4500, 3, 'AVAILABLE'),
    (8, 4, 'RAH 289L', 5500, 4, 'BUSY'),
    (9, 5, 'RAJ 391M', 7800, 9, 'AVAILABLE'),
    (10, 5, 'RAJ 455N', 3500, 8, 'BUSY');

INSERT INTO truck_operational_details
    (truck_id, vehicle_model, driver_name, current_location, notes, updated_by_user_id, updated_at)
VALUES
    (1, 'Isuzu NPR Refrigerated', 'Eric Nshimiyimana', 'Gacurabwenge market collection point', 'Pre-cooled for tomato pickup route', 9, '2026-07-16 06:40:00'),
    (2, 'Toyota Dyna Cold Van', 'Jean Paul Nkurikiyimana', 'Karama sector office', 'Available for short village collection runs', 9, '2026-07-16 07:00:00'),
    (3, 'Fuso Canter Reefer', 'Aime Tuyisenge', 'Musambira cooperative yard', 'Assigned to Musambira and Mugina route', 10, '2026-07-16 06:55:00'),
    (4, 'Hyundai Mighty Refrigerated', 'Moses Ndayambaje', 'Mugina road junction', 'Available with clean crates', 10, '2026-07-16 07:05:00'),
    (5, 'Mercedes Atego Reefer', 'Claude Rukundo', 'Runda Fresh Storage Center', 'Large capacity truck for Runda and Rugalika', 11, '2026-07-16 07:10:00'),
    (6, 'Isuzu FVR Refrigerated', 'Pascal Mugenzi', 'Rugalika garage', 'Cooling unit scheduled for service', 11, '2026-07-15 16:00:00'),
    (7, 'Toyota Dyna Cold Van', 'Emmanuel Habineza', 'Kayenzi Farmers Cooling Center', 'Available after morning delivery', 12, '2026-07-16 07:15:00'),
    (8, 'Fuso Fighter Reefer', 'David Mutabazi', 'Kayumbu village route', 'Assigned to Kayumbu tomato route', 12, '2026-07-16 06:35:00'),
    (9, 'Isuzu NPR Refrigerated', 'Samuel Kwizera', 'Nyarubaka cooperative office', 'Available for afternoon dispatch', 13, '2026-07-16 07:25:00'),
    (10, 'Toyota Hiace Cold Van', 'Blaise Niyitegeka', 'Nyamiyaga collection point', 'Small-volume route for green pepper and tomatoes', 13, '2026-07-16 06:45:00');

INSERT INTO harvest_forecasts
    (forecast_id, farmer_id, quantity_kg, harvest_date, status, submitted_at)
VALUES
    (1, 1, 8200, '2026-07-22 06:30:00', 'ALLOCATED', '2026-07-10 08:00:00'),
    (2, 2, 3600, '2026-07-22 07:00:00', 'ALLOCATED', '2026-07-10 08:10:00'),
    (3, 3, 11800, '2026-07-25 06:45:00', 'PENDING', '2026-07-11 09:00:00'),
    (4, 4, 2400, '2026-08-01 07:15:00', 'PENDING', '2026-07-11 09:20:00'),
    (5, 5, 9500, '2026-07-24 06:30:00', 'ALLOCATED', '2026-07-10 10:00:00'),
    (6, 6, 1750, '2026-08-03 08:00:00', 'PENDING', '2026-07-11 10:10:00'),
    (7, 7, 5600, '2026-08-04 07:30:00', 'PENDING', '2026-07-11 10:25:00'),
    (8, 8, 13300, '2026-07-29 06:20:00', 'ALLOCATED', '2026-07-12 08:40:00'),
    (9, 9, 6200, '2026-07-26 06:40:00', 'ALLOCATED', '2026-07-10 11:00:00'),
    (10, 10, 4300, '2026-08-06 07:10:00', 'PENDING', '2026-07-12 09:30:00'),
    (11, 11, 7900, '2026-08-09 06:55:00', 'PENDING', '2026-07-12 09:45:00'),
    (12, 12, 3100, '2026-07-27 07:35:00', 'ALLOCATED', '2026-07-10 11:15:00'),
    (13, 13, 10400, '2026-07-28 06:30:00', 'ALLOCATED', '2026-07-10 12:00:00'),
    (14, 14, 1400, '2026-08-10 07:45:00', 'PENDING', '2026-07-13 08:00:00'),
    (15, 15, 7200, '2026-08-12 07:00:00', 'PENDING', '2026-07-13 08:15:00'),
    (16, 16, 2800, '2026-07-30 07:25:00', 'ALLOCATED', '2026-07-10 12:20:00'),
    (17, 17, 14500, '2026-07-23 06:15:00', 'ALLOCATED', '2026-07-10 13:00:00'),
    (18, 18, 5100, '2026-08-14 07:05:00', 'PENDING', '2026-07-13 09:00:00'),
    (19, 19, 3800, '2026-08-15 08:00:00', 'PENDING', '2026-07-13 09:10:00'),
    (20, 20, 11600, '2026-07-31 06:50:00', 'ALLOCATED', '2026-07-10 13:10:00'),
    (21, 21, 8700, '2026-07-26 06:35:00', 'ALLOCATED', '2026-07-10 14:00:00'),
    (22, 22, 2200, '2026-08-17 07:30:00', 'PENDING', '2026-07-13 10:00:00'),
    (23, 23, 6400, '2026-08-18 07:10:00', 'PENDING', '2026-07-13 10:20:00'),
    (24, 24, 12700, '2026-08-02 06:25:00', 'ALLOCATED', '2026-07-10 14:20:00'),
    (25, 25, 5200, '2026-07-29 06:45:00', 'ALLOCATED', '2026-07-10 15:00:00'),
    (26, 26, 1900, '2026-08-20 07:40:00', 'PENDING', '2026-07-14 08:00:00'),
    (27, 27, 8100, '2026-08-21 06:50:00', 'PENDING', '2026-07-14 08:15:00'),
    (28, 28, 4500, '2026-08-04 07:00:00', 'ALLOCATED', '2026-07-10 15:20:00'),
    (29, 29, 6900, '2026-08-05 07:15:00', 'ALLOCATED', '2026-07-10 15:40:00'),
    (30, 30, 3100, '2026-08-24 08:10:00', 'PENDING', '2026-07-14 09:00:00'),
    (31, 31, 15200, '2026-08-25 06:30:00', 'PENDING', '2026-07-14 09:10:00'),
    (32, 32, 5700, '2026-08-06 06:55:00', 'ALLOCATED', '2026-07-10 16:00:00'),
    (33, 33, 4300, '2026-08-07 07:20:00', 'ALLOCATED', '2026-07-10 16:20:00'),
    (34, 34, 2450, '2026-08-27 07:35:00', 'PENDING', '2026-07-14 10:00:00'),
    (35, 35, 9600, '2026-08-28 06:40:00', 'PENDING', '2026-07-14 10:10:00'),
    (36, 36, 7600, '2026-08-08 06:45:00', 'ALLOCATED', '2026-07-10 16:40:00'),
    (37, 37, 3400, '2026-08-09 07:05:00', 'ALLOCATED', '2026-07-10 17:00:00'),
    (38, 38, 12800, '2026-08-30 06:20:00', 'PENDING', '2026-07-14 11:00:00'),
    (39, 39, 2100, '2026-08-31 08:00:00', 'PENDING', '2026-07-14 11:10:00'),
    (40, 40, 8300, '2026-08-10 06:35:00', 'ALLOCATED', '2026-07-10 17:20:00'),
    (41, 41, 6100, '2026-08-11 06:55:00', 'ALLOCATED', '2026-07-10 17:40:00'),
    (42, 42, 1700, '2026-09-02 07:25:00', 'PENDING', '2026-07-15 08:00:00'),
    (43, 43, 7400, '2026-09-03 07:05:00', 'PENDING', '2026-07-15 08:20:00'),
    (44, 44, 4100, '2026-08-12 07:30:00', 'ALLOCATED', '2026-07-10 18:00:00'),
    (45, 45, 10900, '2026-08-13 06:35:00', 'ALLOCATED', '2026-07-10 18:20:00'),
    (46, 46, 2800, '2026-09-05 07:45:00', 'PENDING', '2026-07-15 09:00:00'),
    (47, 47, 6700, '2026-09-06 07:00:00', 'PENDING', '2026-07-15 09:10:00'),
    (48, 48, 5900, '2026-08-14 06:50:00', 'ALLOCATED', '2026-07-10 18:40:00');

INSERT INTO forecast_requirements
    (forecast_id, needs_transport, needs_storage, notes, source)
VALUES
    (1, TRUE, TRUE, 'Tomatoes; farm size 1.8 ha; mature green to breaker stage', 'USSD'),
    (2, TRUE, TRUE, 'Irish Potatoes; farm size 0.7 ha; ready for collection', 'WEB'),
    (3, TRUE, TRUE, 'Tomatoes; farm size 2.4 ha; flowering blocks finishing', 'USSD'),
    (4, TRUE, FALSE, 'Carrots; farm size 0.5 ha; farmer has temporary shade storage', 'WEB'),
    (5, TRUE, TRUE, 'Tomatoes; farm size 1.9 ha; red-ripe harvest expected', 'USSD'),
    (6, FALSE, TRUE, 'Onions; farm size 0.6 ha; farmer will deliver to hub', 'WEB'),
    (7, TRUE, TRUE, 'Cabbage; farm size 1.2 ha; cooling required after trimming', 'USSD'),
    (8, TRUE, TRUE, 'Tomatoes; farm size 2.7 ha; high-volume cluster harvest', 'WEB'),
    (9, TRUE, TRUE, 'Green Pepper; farm size 1.0 ha; crate handling needed', 'USSD'),
    (10, TRUE, TRUE, 'Tomatoes; farm size 1.3 ha; staged harvest', 'WEB'),
    (11, TRUE, TRUE, 'Tomatoes; farm size 1.6 ha; requires morning pickup', 'USSD'),
    (12, TRUE, FALSE, 'Irish Potatoes; farm size 0.8 ha; transport only', 'WEB'),
    (13, TRUE, TRUE, 'Tomatoes; farm size 2.1 ha; avoid afternoon heat', 'USSD'),
    (14, FALSE, TRUE, 'Carrots; farm size 0.4 ha; hub reservation only', 'WEB'),
    (15, TRUE, TRUE, 'Tomatoes; farm size 1.5 ha; sorting at collection point', 'USSD'),
    (16, TRUE, TRUE, 'Cabbage; farm size 0.9 ha; cold room pallet required', 'WEB'),
    (17, TRUE, TRUE, 'Tomatoes; farm size 3.0 ha; cooperative harvest team', 'USSD'),
    (18, TRUE, TRUE, 'Green Pepper; farm size 1.1 ha; moisture control needed', 'WEB'),
    (19, TRUE, FALSE, 'Onions; farm size 0.9 ha; ventilated transport', 'USSD'),
    (20, TRUE, TRUE, 'Tomatoes; farm size 2.3 ha; fragile produce', 'WEB'),
    (21, TRUE, TRUE, 'Tomatoes; farm size 1.7 ha; pre-cooling requested', 'USSD'),
    (22, FALSE, TRUE, 'Carrots; farm size 0.5 ha; farmer handles transport', 'WEB'),
    (23, TRUE, TRUE, 'Cabbage; farm size 1.4 ha; storage for two days', 'USSD'),
    (24, TRUE, TRUE, 'Tomatoes; farm size 2.5 ha; mixed maturity stages', 'WEB'),
    (25, TRUE, TRUE, 'Green Pepper; farm size 0.8 ha; crate count confirmed', 'USSD'),
    (26, TRUE, FALSE, 'Onions; farm size 0.6 ha; transport only', 'WEB'),
    (27, TRUE, TRUE, 'Tomatoes; farm size 1.8 ha; hub temperature 8C requested', 'USSD'),
    (28, TRUE, TRUE, 'Irish Potatoes; farm size 1.0 ha; cooperative pickup', 'WEB'),
    (29, TRUE, TRUE, 'Tomatoes; farm size 1.5 ha; morning dispatch', 'USSD'),
    (30, TRUE, TRUE, 'Cabbage; farm size 0.7 ha; cold storage required', 'WEB'),
    (31, TRUE, TRUE, 'Tomatoes; farm size 3.1 ha; large harvest window', 'USSD'),
    (32, TRUE, TRUE, 'Carrots; farm size 1.1 ha; washed and bagged', 'WEB'),
    (33, TRUE, TRUE, 'Green Pepper; farm size 0.9 ha; cool-chain handling', 'USSD'),
    (34, FALSE, TRUE, 'Onions; farm size 0.5 ha; direct hub delivery', 'WEB'),
    (35, TRUE, TRUE, 'Tomatoes; farm size 2.0 ha; scheduled harvest team', 'USSD'),
    (36, TRUE, TRUE, 'Tomatoes; farm size 1.6 ha; route consolidation', 'WEB'),
    (37, TRUE, TRUE, 'Irish Potatoes; farm size 0.8 ha; transport and storage', 'USSD'),
    (38, TRUE, TRUE, 'Tomatoes; farm size 2.6 ha; awaiting final grading', 'WEB'),
    (39, TRUE, FALSE, 'Carrots; farm size 0.5 ha; transport only', 'USSD'),
    (40, TRUE, TRUE, 'Tomatoes; farm size 1.7 ha; short storage requirement', 'WEB'),
    (41, TRUE, TRUE, 'Green Pepper; farm size 1.0 ha; export buyer sample', 'USSD'),
    (42, FALSE, TRUE, 'Onions; farm size 0.4 ha; hub reservation only', 'WEB'),
    (43, TRUE, TRUE, 'Tomatoes; farm size 1.5 ha; field crates needed', 'USSD'),
    (44, TRUE, TRUE, 'Cabbage; farm size 0.9 ha; route shared with Runda', 'WEB'),
    (45, TRUE, TRUE, 'Tomatoes; farm size 2.2 ha; high priority order', 'USSD'),
    (46, TRUE, FALSE, 'Carrots; farm size 0.6 ha; transport only', 'WEB'),
    (47, TRUE, TRUE, 'Tomatoes; farm size 1.4 ha; pending buyer assignment', 'USSD'),
    (48, TRUE, TRUE, 'Irish Potatoes; farm size 1.2 ha; cool storage requested', 'WEB');

INSERT INTO coordination_plans
    (plan_id, sector_id, generated_at, status)
VALUES
    (1, 1, '2026-07-16 05:30:00', 'COMPLETED'),
    (2, 2, '2026-07-16 05:35:00', 'COMPLETED'),
    (3, 3, '2026-07-16 05:40:00', 'COMPLETED'),
    (4, 4, '2026-07-16 05:45:00', 'COMPLETED'),
    (5, 5, '2026-07-16 05:50:00', 'COMPLETED'),
    (6, 6, '2026-07-16 05:55:00', 'COMPLETED'),
    (7, 7, '2026-07-16 06:00:00', 'COMPLETED'),
    (8, 8, '2026-07-16 06:05:00', 'COMPLETED'),
    (9, 9, '2026-07-16 06:10:00', 'COMPLETED'),
    (10, 10, '2026-07-16 06:15:00', 'COMPLETED'),
    (11, 11, '2026-07-16 06:20:00', 'COMPLETED'),
    (12, 12, '2026-07-16 06:25:00', 'RUNNING');

INSERT INTO trip_allocations
    (allocation_id, plan_id, truck_id, hub_id, sector_id, total_load_kg, pickup_start, estimated_hub_arrival, status, created_at)
VALUES
    (1, 1, 1, 1, 1, 11800, '2026-07-22 06:30:00', '2026-07-22 08:00:00', 'SCHEDULED', '2026-07-16 05:45:00'),
    (2, 2, 2, 1, 2, 9500, '2026-07-24 06:30:00', '2026-07-24 08:10:00', 'SCHEDULED', '2026-07-16 05:50:00'),
    (3, 2, 8, 4, 2, 13300, '2026-07-29 06:20:00', '2026-07-29 08:25:00', 'IN_PROGRESS', '2026-07-16 05:55:00'),
    (4, 3, 7, 4, 3, 9300, '2026-07-26 06:40:00', '2026-07-26 08:00:00', 'COMPLETED', '2026-07-16 06:00:00'),
    (5, 4, 8, 3, 4, 13200, '2026-07-28 06:30:00', '2026-07-28 08:20:00', 'SCHEDULED', '2026-07-16 06:05:00'),
    (6, 5, 3, 5, 5, 14500, '2026-07-23 06:15:00', '2026-07-23 07:45:00', 'SCHEDULED', '2026-07-16 06:10:00'),
    (7, 5, 4, 5, 5, 11600, '2026-07-31 06:50:00', '2026-07-31 08:20:00', 'CANCELLED', '2026-07-16 06:15:00'),
    (8, 6, 3, 3, 6, 8700, '2026-07-26 06:35:00', '2026-07-26 08:00:00', 'SCHEDULED', '2026-07-16 06:20:00'),
    (9, 6, 4, 3, 6, 12700, '2026-08-02 06:25:00', '2026-08-02 07:55:00', 'SCHEDULED', '2026-07-16 06:25:00'),
    (10, 7, 10, 3, 7, 9700, '2026-07-29 06:45:00', '2026-07-29 08:15:00', 'IN_PROGRESS', '2026-07-16 06:30:00'),
    (11, 8, 10, 6, 8, 12600, '2026-08-05 07:15:00', '2026-08-05 08:45:00', 'SCHEDULED', '2026-07-16 06:35:00'),
    (12, 9, 9, 6, 9, 11900, '2026-08-07 07:20:00', '2026-08-07 09:00:00', 'SCHEDULED', '2026-07-16 06:40:00'),
    (13, 9, 9, 6, 9, 7600, '2026-08-08 06:45:00', '2026-08-08 08:30:00', 'COMPLETED', '2026-07-16 06:45:00'),
    (14, 10, 5, 2, 10, 11700, '2026-08-09 07:05:00', '2026-08-09 08:40:00', 'SCHEDULED', '2026-07-16 06:50:00'),
    (15, 11, 5, 2, 11, 10200, '2026-08-11 06:55:00', '2026-08-11 08:25:00', 'SCHEDULED', '2026-07-16 06:55:00'),
    (16, 12, 5, 2, 12, 16800, '2026-08-13 06:35:00', '2026-08-13 08:05:00', 'SCHEDULED', '2026-07-16 07:00:00');

INSERT INTO forecast_allocations
    (allocation_id, forecast_id, allocated_quantity_kg, created_at)
VALUES
    (1, 1, 8200, '2026-07-16 05:45:00'),
    (1, 2, 3600, '2026-07-16 05:45:00'),
    (2, 5, 9500, '2026-07-16 05:50:00'),
    (3, 8, 13300, '2026-07-16 05:55:00'),
    (4, 9, 6200, '2026-07-16 06:00:00'),
    (4, 12, 3100, '2026-07-16 06:00:00'),
    (5, 13, 10400, '2026-07-16 06:05:00'),
    (5, 16, 2800, '2026-07-16 06:05:00'),
    (6, 17, 14500, '2026-07-16 06:10:00'),
    (7, 20, 11600, '2026-07-16 06:15:00'),
    (8, 21, 8700, '2026-07-16 06:20:00'),
    (9, 24, 12700, '2026-07-16 06:25:00'),
    (10, 25, 5200, '2026-07-16 06:30:00'),
    (10, 28, 4500, '2026-07-16 06:30:00'),
    (11, 29, 6900, '2026-07-16 06:35:00'),
    (11, 32, 5700, '2026-07-16 06:35:00'),
    (12, 33, 4300, '2026-07-16 06:40:00'),
    (12, 36, 7600, '2026-07-16 06:40:00'),
    (13, 36, 7600, '2026-07-16 06:45:00'),
    (14, 37, 3400, '2026-07-16 06:50:00'),
    (14, 40, 8300, '2026-07-16 06:50:00'),
    (15, 41, 6100, '2026-07-16 06:55:00'),
    (15, 44, 4100, '2026-07-16 06:55:00'),
    (16, 45, 10900, '2026-07-16 07:00:00'),
    (16, 48, 5900, '2026-07-16 07:00:00');

INSERT INTO excluded_trips
    (exclusion_id, forecast_id, plan_id, reason_code, reason_detail, excluded_at, created_at)
VALUES
    (1, 3, 1, 'CAPACITY_DEFERRED', 'Large tomato forecast moved to next coordination run after hub capacity review.', '2026-07-16 05:48:00', '2026-07-16 05:48:00'),
    (2, 6, 2, 'NO_TRANSPORT_REQUIRED', 'Farmer requested cold storage only and will deliver onions directly.', '2026-07-16 05:52:00', '2026-07-16 05:52:00'),
    (3, 14, 4, 'NO_TRANSPORT_REQUIRED', 'Carrot forecast requires only hub reservation.', '2026-07-16 06:08:00', '2026-07-16 06:08:00'),
    (4, 22, 6, 'NO_TRANSPORT_REQUIRED', 'Farmer will use cooperative pickup outside FreshLink fleet.', '2026-07-16 06:22:00', '2026-07-16 06:22:00'),
    (5, 31, 8, 'INSUFFICIENT_TRUCK_CAPACITY', 'High-volume harvest requires split allocation in the next run.', '2026-07-16 06:38:00', '2026-07-16 06:38:00');

INSERT INTO payments
    (payment_id, allocation_id, farmer_id, payer_type, payee_type, payer_phone, payee_phone, amount, currency, purpose, payment_method, status, payment_reference, flutterwave_ref, tx_ref, transaction_id, payment_link, provider_status, provider_response, created_at, verified_at, failed_at, paid_at, refunded_at, settled_at, last_checked_at)
VALUES
    (1, 1, 1, 'FARMER', 'PLATFORM', '0784100001', '0788300001', 35400.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PAID', 'TLP-1-20260716-A001', 'FLW-MOCK-1-A001', 'TLP-1-20260716-A001', '900001', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-1-a001', 'successful', '{"status":"success","processor_response":"Approved"}', '2026-07-16 06:00:00', '2026-07-16 06:08:00', NULL, '2026-07-16 06:08:00', NULL, '2026-07-16 06:08:00', '2026-07-16 06:08:00'),
    (2, 2, 5, 'FARMER', 'PLATFORM', '0784100005', '0788300001', 28500.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'INITIALIZED', 'TLP-2-20260716-A002', 'TLP-2-20260716-A002', 'TLP-2-20260716-A002', NULL, 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-2-a002', 'success', '{"status":"success","message":"Hosted link generated"}', '2026-07-16 06:03:00', NULL, NULL, NULL, NULL, NULL, '2026-07-16 06:03:00'),
    (3, 3, 8, 'FARMER', 'PLATFORM', '0784100008', '0788300004', 39900.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PENDING', 'TLP-3-20260716-A003', 'FLW-MOCK-3-A003', 'TLP-3-20260716-A003', '900003', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-3-a003', 'pending', '{"status":"success","processor_response":"Pending mobile money authorization"}', '2026-07-16 06:06:00', '2026-07-16 06:12:00', NULL, NULL, NULL, NULL, '2026-07-16 06:12:00'),
    (4, 4, 9, 'FARMER', 'PLATFORM', '0784100009', '0788300004', 27900.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PAID', 'TLP-4-20260716-A004', 'FLW-MOCK-4-A004', 'TLP-4-20260716-A004', '900004', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-4-a004', 'successful', '{"status":"success","processor_response":"Approved"}', '2026-07-16 06:09:00', '2026-07-16 06:18:00', NULL, '2026-07-16 06:18:00', NULL, '2026-07-16 06:18:00', '2026-07-16 06:18:00'),
    (5, 5, 13, 'FARMER', 'PLATFORM', '0784100013', '0788300003', 39600.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'CREATED', 'TLP-5-20260716-A005', 'TLP-5-20260716-A005', 'TLP-5-20260716-A005', NULL, NULL, NULL, NULL, '2026-07-16 06:12:00', NULL, NULL, NULL, NULL, NULL, NULL),
    (6, 6, 17, 'FARMER', 'PLATFORM', '0784100017', '0788300005', 43500.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'INITIALIZED', 'TLP-6-20260716-A006', 'TLP-6-20260716-A006', 'TLP-6-20260716-A006', NULL, 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-6-a006', 'success', '{"status":"success","message":"Hosted link generated"}', '2026-07-16 06:15:00', NULL, NULL, NULL, NULL, NULL, '2026-07-16 06:15:00'),
    (7, 7, 20, 'FARMER', 'PLATFORM', '0784100020', '0788300005', 34800.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'FAILED', 'TLP-7-20260716-A007', 'FLW-MOCK-7-A007', 'TLP-7-20260716-A007', '900007', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-7-a007', 'failed', '{"status":"error","processor_response":"Insufficient mobile money balance"}', '2026-07-16 06:18:00', '2026-07-16 06:25:00', '2026-07-16 06:25:00', NULL, NULL, NULL, '2026-07-16 06:25:00'),
    (8, 8, 21, 'FARMER', 'PLATFORM', '0784100021', '0788300003', 26100.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PAID', 'TLP-8-20260716-A008', 'FLW-MOCK-8-A008', 'TLP-8-20260716-A008', '900008', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-8-a008', 'successful', '{"status":"success","processor_response":"Approved"}', '2026-07-16 06:21:00', '2026-07-16 06:27:00', NULL, '2026-07-16 06:27:00', NULL, '2026-07-16 06:27:00', '2026-07-16 06:27:00'),
    (9, 9, 24, 'FARMER', 'PLATFORM', '0784100024', '0788300003', 38100.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PENDING', 'TLP-9-20260716-A009', 'FLW-MOCK-9-A009', 'TLP-9-20260716-A009', '900009', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-9-a009', 'pending', '{"status":"success","processor_response":"Awaiting bank confirmation"}', '2026-07-16 06:24:00', '2026-07-16 06:31:00', NULL, NULL, NULL, NULL, '2026-07-16 06:31:00'),
    (10, 10, 25, 'FARMER', 'PLATFORM', '0784100025', '0788300003', 29100.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PAID', 'TLP-10-20260716-A010', 'FLW-MOCK-10-A010', 'TLP-10-20260716-A010', '900010', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-10-a010', 'successful', '{"status":"success","processor_response":"Approved"}', '2026-07-16 06:27:00', '2026-07-16 06:34:00', NULL, '2026-07-16 06:34:00', NULL, '2026-07-16 06:34:00', '2026-07-16 06:34:00'),
    (11, 11, 29, 'FARMER', 'PLATFORM', '0784100029', '0788300006', 37800.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'INITIALIZED', 'TLP-11-20260716-A011', 'TLP-11-20260716-A011', 'TLP-11-20260716-A011', NULL, 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-11-a011', 'success', '{"status":"success","message":"Hosted link generated"}', '2026-07-16 06:30:00', NULL, NULL, NULL, NULL, NULL, '2026-07-16 06:30:00'),
    (12, 12, 33, 'FARMER', 'PLATFORM', '0784100033', '0788300006', 35700.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'CREATED', 'TLP-12-20260716-A012', 'TLP-12-20260716-A012', 'TLP-12-20260716-A012', NULL, NULL, NULL, NULL, '2026-07-16 06:33:00', NULL, NULL, NULL, NULL, NULL, NULL),
    (13, 13, 36, 'FARMER', 'PLATFORM', '0784100036', '0788300006', 22800.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PAID', 'TLP-13-20260716-A013', 'FLW-MOCK-13-A013', 'TLP-13-20260716-A013', '900013', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-13-a013', 'successful', '{"status":"success","processor_response":"Approved"}', '2026-07-16 06:36:00', '2026-07-16 06:42:00', NULL, '2026-07-16 06:42:00', NULL, '2026-07-16 06:42:00', '2026-07-16 06:42:00'),
    (14, 14, 37, 'FARMER', 'PLATFORM', '0784100037', '0788300002', 35100.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'FAILED', 'TLP-14-20260716-A014', 'FLW-MOCK-14-A014', 'TLP-14-20260716-A014', '900014', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-14-a014', 'failed', '{"status":"error","processor_response":"Payment abandoned"}', '2026-07-16 06:39:00', '2026-07-16 06:47:00', '2026-07-16 06:47:00', NULL, NULL, NULL, '2026-07-16 06:47:00'),
    (15, 15, 41, 'FARMER', 'PLATFORM', '0784100041', '0788300002', 30600.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'PENDING', 'TLP-15-20260716-A015', 'FLW-MOCK-15-A015', 'TLP-15-20260716-A015', '900015', 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-15-a015', 'pending', '{"status":"success","processor_response":"Pending card authorization"}', '2026-07-16 06:42:00', '2026-07-16 06:49:00', NULL, NULL, NULL, NULL, '2026-07-16 06:49:00'),
    (16, 16, 45, 'FARMER', 'PLATFORM', '0784100045', '0788300002', 50400.00, 'RWF', 'TRIP_TRANSPORT_AND_STORAGE', 'FLUTTERWAVE', 'INITIALIZED', 'TLP-16-20260716-A016', 'TLP-16-20260716-A016', 'TLP-16-20260716-A016', NULL, 'https://checkout.flutterwave.com/v3/hosted/pay/tlp-16-a016', 'success', '{"status":"success","message":"Hosted link generated"}', '2026-07-16 06:45:00', NULL, NULL, NULL, NULL, NULL, '2026-07-16 06:45:00');

INSERT INTO notifications
    (notification_id, recipient_type, recipient_phone, channel, message, status, sent_time, related_trip_id)
VALUES
    (1, 'FARMER', '0784100001', 'SMS', 'Reservation confirmed: 11800 kg will be collected from Gacurabwenge and delivered to Kamonyi Central Cold Hub.', 'SENT', '2026-07-16 06:05:00', 1),
    (2, 'FARMER', '0784100001', 'SMS', 'FreshLink payment successful. Reference TLP-1-20260716-A001 has been confirmed.', 'SENT', '2026-07-16 06:09:00', 1),
    (3, 'TRANSPORTER', '0788200001', 'SMS', 'Truck RAE 102F assigned to Gacurabwenge route for 2026-07-22 06:30.', 'SENT', '2026-07-16 06:10:00', 1),
    (4, 'FARMER', '0784100005', 'SMS', 'Payment initialized for your Karama tomato logistics reservation. Please complete payment using the Flutterwave link.', 'QUEUED', NULL, 2),
    (5, 'FARMER', '0784100008', 'SMS', 'Payment pending for allocation 3. FreshLink will confirm once Flutterwave posts final status.', 'SENT', '2026-07-16 06:14:00', 3),
    (6, 'HUB_OPERATOR', '0788300004', 'SMS', 'Cold hub reservation approved for Kayenzi Farmers Cooling Center.', 'SENT', '2026-07-16 06:16:00', 3),
    (7, 'FARMER', '0784100009', 'SMS', 'Trip completed for your Kayenzi produce. Thank you for using FreshLink.', 'SENT', '2026-07-16 06:44:00', 4),
    (8, 'FARMER', '0784100013', 'SMS', 'Payment created for Kayumbu allocation. Flutterwave link will be sent shortly.', 'QUEUED', NULL, 5),
    (9, 'FARMER', '0784100017', 'SMS', 'Payment initialized for Mugina Cold Storage Facility reservation.', 'SENT', '2026-07-16 06:18:00', 6),
    (10, 'FARMER', '0784100020', 'SMS', 'Payment failed for cancelled allocation 7. Please contact FreshLink support if you still need transport.', 'SENT', '2026-07-16 06:28:00', 7),
    (11, 'FARMER', '0784100021', 'SMS', 'Harvest reminder: Musambira tomato pickup is scheduled for 2026-07-26 at 06:35.', 'SENT', '2026-07-16 06:30:00', 8),
    (12, 'FARMER', '0784100024', 'SMS', 'Payment pending for allocation 9. Keep your mobile money account active for confirmation.', 'SENT', '2026-07-16 06:33:00', 9),
    (13, 'TRANSPORTER', '0788200005', 'SMS', 'Trip started for Ngamba route. Driver Blaise Niyitegeka is en route to collection point.', 'SENT', '2026-07-16 06:50:00', 10),
    (14, 'HUB_OPERATOR', '0788300006', 'SMS', 'Cold hub capacity updated after Nyamiyaga reservation: 12600 kg expected.', 'SENT', '2026-07-16 06:37:00', 11),
    (15, 'FARMER', '0784100033', 'SMS', 'Payment created for Nyarubaka allocation. Awaiting Flutterwave initialization.', 'QUEUED', NULL, 12),
    (16, 'FARMER', '0784100036', 'SMS', 'Trip completed and payment confirmed for allocation 13.', 'SENT', '2026-07-16 06:45:00', 13),
    (17, 'FARMER', '0784100037', 'SMS', 'Payment failed for allocation 14. Please retry from the FreshLink payment page.', 'SENT', '2026-07-16 06:48:00', 14),
    (18, 'FARMER', '0784100041', 'SMS', 'Payment pending for Rukoma allocation. FreshLink will notify you after confirmation.', 'SENT', '2026-07-16 06:51:00', 15),
    (19, 'FARMER', '0784100045', 'SMS', 'Payment initialized for Runda Fresh Storage Center reservation.', 'QUEUED', NULL, 16),
    (20, 'ADMIN', '0788300001', 'SMS', 'Dashboard alert: Kamonyi Central Cold Hub capacity updated after morning coordination run.', 'SENT', '2026-07-16 07:05:00', 1);

INSERT INTO cold_hub_capacity_updates
    (update_id, hub_id, updated_by_user_id, total_capacity_kg, available_capacity_kg, produce_type, notes, created_at)
VALUES
    (1, 1, 4, 65000, 41200, 'tomatoes', 'Capacity reduced after Gacurabwenge and Karama reservations.', '2026-07-16 06:12:00'),
    (2, 2, 5, 52000, 31750, 'tomatoes', 'Capacity reserved for Rugalika, Rukoma and Runda routes.', '2026-07-16 06:58:00'),
    (3, 3, 6, 48000, 28600, 'tomatoes', 'Musambira, Ngamba and Kayumbu produce reservations approved.', '2026-07-16 06:32:00'),
    (4, 4, 7, 36000, 21400, 'green pepper', 'Kayenzi and Karama mixed produce reservation approved.', '2026-07-16 06:18:00'),
    (5, 5, 8, 42000, 26100, 'tomatoes', 'Mugina high-volume tomato route reserved.', '2026-07-16 06:20:00'),
    (6, 6, 3, 24000, 16800, 'tomatoes', 'Nyarubaka and Nyamiyaga capacity adjusted after coordination run.', '2026-07-16 06:44:00');

INSERT INTO hub_allocation_receipts
    (allocation_id, confirmed_at, confirmed_by_user_id, received_quantity_kg)
VALUES
    (4, '2026-07-26 08:05:00', 7, 9300),
    (13, '2026-08-08 08:35:00', 3, 7600);

INSERT INTO trip_status_events
    (event_id, allocation_id, status, changed_by_user_id, created_at)
VALUES
    (1, 1, 'SCHEDULED', 2, '2026-07-16 05:45:00'),
    (2, 2, 'SCHEDULED', 2, '2026-07-16 05:50:00'),
    (3, 3, 'SCHEDULED', 2, '2026-07-16 05:55:00'),
    (4, 3, 'STARTED', 10, '2026-07-29 06:25:00'),
    (5, 4, 'SCHEDULED', 2, '2026-07-16 06:00:00'),
    (6, 4, 'STARTED', 12, '2026-07-26 06:45:00'),
    (7, 4, 'COMPLETED', 7, '2026-07-26 08:05:00'),
    (8, 5, 'SCHEDULED', 2, '2026-07-16 06:05:00'),
    (9, 6, 'SCHEDULED', 3, '2026-07-16 06:10:00'),
    (10, 7, 'SCHEDULED', 3, '2026-07-16 06:15:00'),
    (11, 7, 'CANCELLED', 3, '2026-07-16 06:28:00'),
    (12, 8, 'SCHEDULED', 3, '2026-07-16 06:20:00'),
    (13, 9, 'SCHEDULED', 3, '2026-07-16 06:25:00'),
    (14, 10, 'SCHEDULED', 2, '2026-07-16 06:30:00'),
    (15, 10, 'STARTED', 13, '2026-07-29 06:50:00'),
    (16, 11, 'SCHEDULED', 2, '2026-07-16 06:35:00'),
    (17, 12, 'SCHEDULED', 3, '2026-07-16 06:40:00'),
    (18, 13, 'SCHEDULED', 3, '2026-07-16 06:45:00'),
    (19, 13, 'STARTED', 13, '2026-08-08 06:50:00'),
    (20, 13, 'COMPLETED', 3, '2026-08-08 08:35:00'),
    (21, 14, 'SCHEDULED', 2, '2026-07-16 06:50:00'),
    (22, 15, 'SCHEDULED', 2, '2026-07-16 06:55:00'),
    (23, 16, 'SCHEDULED', 2, '2026-07-16 07:00:00');
