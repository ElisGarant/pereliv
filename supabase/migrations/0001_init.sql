-- Сгенерировано из server/app/models.py командой python -m app.schema

CREATE TABLE modules (
	id SERIAL NOT NULL, 
	title VARCHAR(128) NOT NULL, 
	direction VARCHAR(8), 
	position INTEGER NOT NULL, 
	is_free BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

ALTER TABLE modules ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE orders (
	id SERIAL NOT NULL, 
	type VARCHAR(16) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	client VARCHAR(200) NOT NULL, 
	rate VARCHAR(32) NOT NULL, 
	unit VARCHAR(64) NOT NULL, 
	volume VARCHAR(64) NOT NULL, 
	deadline VARCHAR(64) NOT NULL, 
	seats INTEGER NOT NULL, 
	brief TEXT NOT NULL, 
	rules JSON NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE users (
	id SERIAL NOT NULL, 
	tg_id BIGINT NOT NULL, 
	username VARCHAR(64), 
	first_name VARCHAR(128) NOT NULL, 
	last_name VARCHAR(128), 
	photo_url VARCHAR(512), 
	role VARCHAR(16) NOT NULL, 
	direction VARCHAR(8), 
	ref_code VARCHAR(16), 
	referrer_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (ref_code), 
	FOREIGN KEY(referrer_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_users_tg_id ON users (tg_id);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE applications (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	direction VARCHAR(8) NOT NULL, 
	age_group VARCHAR(16) NOT NULL, 
	hours VARCHAR(16) NOT NULL, 
	experience VARCHAR(16) NOT NULL, 
	goal VARCHAR(32) NOT NULL, 
	about TEXT NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	decided_by INTEGER, 
	decided_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(decided_by) REFERENCES users (id)
);

CREATE INDEX ix_applications_user_id ON applications (user_id);
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE audit_log (
	id SERIAL NOT NULL, 
	actor_id INTEGER, 
	action VARCHAR(64) NOT NULL, 
	payload JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE lessons (
	id SERIAL NOT NULL, 
	module_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	position INTEGER NOT NULL, 
	youtube_id VARCHAR(16), 
	duration_sec INTEGER NOT NULL, 
	chapters JSON NOT NULL, 
	summary_md TEXT NOT NULL, 
	task_text TEXT NOT NULL, 
	materials JSON NOT NULL, 
	pass_score INTEGER NOT NULL, 
	retake_minutes INTEGER NOT NULL, 
	xp INTEGER NOT NULL, 
	published BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(module_id) REFERENCES modules (id) ON DELETE CASCADE
);

CREATE INDEX ix_lessons_module_id ON lessons (module_id);
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE order_members (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id, user_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_order_members_order_id ON order_members (order_id);
CREATE INDEX ix_order_members_user_id ON order_members (user_id);
ALTER TABLE order_members ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE reports (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	numbers JSON NOT NULL, 
	comment TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_reports_user_id ON reports (user_id);
CREATE INDEX ix_reports_order_id ON reports (order_id);
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE role_test_results (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	answers JSON NOT NULL, 
	scores JSON NOT NULL, 
	top VARCHAR(8) NOT NULL, 
	smart INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_role_test_results_user_id ON role_test_results (user_id);
ALTER TABLE role_test_results ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE voice_notes (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	duration INTEGER NOT NULL, 
	text TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_voice_notes_user_id ON voice_notes (user_id);
ALTER TABLE voice_notes ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE lesson_progress (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	seen BOOLEAN NOT NULL, 
	best_score INTEGER NOT NULL, 
	attempts INTEGER NOT NULL, 
	last_attempt_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, lesson_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
);

CREATE INDEX ix_lesson_progress_user_id ON lesson_progress (user_id);
ALTER TABLE lesson_progress ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE notes (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	t_sec INTEGER, 
	text TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
);

CREATE INDEX ix_notes_user_id ON notes (user_id);
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

CREATE TABLE quiz_questions (
	id SERIAL NOT NULL, 
	lesson_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	text TEXT NOT NULL, 
	options JSON NOT NULL, 
	correct INTEGER NOT NULL, 
	explanation TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
);

CREATE INDEX ix_quiz_questions_lesson_id ON quiz_questions (lesson_id);
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;  -- политик нет: таблицы доступны только серверу

