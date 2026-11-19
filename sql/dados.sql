INSERT INTO usuario (id, nome, email, senha)
VALUES (
    1,
    'Administrador',
    'admin@clinica.com',
    'scrypt:32768:8:1$Yk7AXENIsmewzFW0$4794ade9828904a04021fe9bb3251ff79596fd77b91654e0cff447e7d201c15fc455c7903b957f13a5fb136725109f45b7f2d89d9142c720b339099d4d0eeb3b'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tutores (id, nome, cpf, telefone, email)
VALUES
(1, 'Ana Oliveira', MD5('12345678901'), '11999990001', 'ana@email.com'),
(2, 'Carlos Souza', MD5('23456789012'), '11999990002', 'carlos@email.com'),
(3, 'Mariana Lima', MD5('34567890123'), '11999990003', 'mariana@email.com')
ON CONFLICT DO NOTHING;

INSERT INTO pet (id, nome, especie, raca, idade, tutor_id)
VALUES
(1, 'Luna', 'Cachorro', 'Golden Retriever', 3, 1),
(2, 'Mimi', 'Gato', 'Siamês', 2, 2),
(3, 'Thor', 'Cachorro', 'Labrador', 5, 3)
ON CONFLICT (id) DO NOTHING;

INSERT INTO agendamentos (id, data, horario, motivo, pet_id)
VALUES
(1, '2026-11-20', '09:00', 'Consulta de rotina', 1),
(2, '2026-11-22', '10:30', 'Vacinação', 2),
(3, '2026-12-05', '14:00', 'Avaliação veterinária', 3)
ON CONFLICT (id) DO NOTHING;

SELECT setval('usuario_id_seq', (SELECT MAX(id) FROM usuario));
SELECT setval('tutores_id_seq', (SELECT MAX(id) FROM tutores));
SELECT setval('pet_id_seq', (SELECT MAX(id) FROM pet));
SELECT setval('agendamentos_id_seq', (SELECT MAX(id) FROM agendamentos));



