import sqlite3

class RPGDatabase:
    def __init__(self, db_name="rpg_system.db"):
        self.db_name = db_name
        # Cria as tabelas ao iniciar, mas não segura a conexão
        self.create_tables()
        self._migrate_db()
    
    def _migrate_db(self):
        """Verifica se precisa atualizar tabelas antigas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Migração de Magias (Já existia)
        try: cursor.execute("SELECT description FROM spells LIMIT 1")
        except: 
            cursor.execute("ALTER TABLE spells ADD COLUMN description TEXT")
            conn.commit()
            
        # 2. NOVA: Migração de Recursos
        try: cursor.execute("SELECT description FROM resources LIMIT 1")
        except: 
            cursor.execute("ALTER TABLE resources ADD COLUMN description TEXT")
            conn.commit()
            
        conn.close()

    def get_connection(self):
        """Cria uma nova conexão limpa sempre que chamado."""
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Tabela Personagens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                char_class TEXT,
                level INTEGER,
                max_hp INTEGER,
                current_hp INTEGER,
                ac INTEGER,
                save_dc INTEGER,
                stats TEXT
            )
        """)
        
        # 2. Tabela Recursos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                char_id INTEGER,
                name TEXT,
                max_val INTEGER,
                current_val INTEGER,
                FOREIGN KEY(char_id) REFERENCES characters(id)
            )
        """)
        
        # 3. Tabela Ações/Ataques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                char_id INTEGER,
                name TEXT,
                atk_bonus INTEGER,
                dmg_dice TEXT,
                dmg_bonus INTEGER,
                FOREIGN KEY(char_id) REFERENCES characters(id)
            )
        """)

        # 4. Tabela Magias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER,
                name TEXT,
                level INTEGER,
                school TEXT,
                FOREIGN KEY(character_id) REFERENCES characters(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    # =========================================
    # LEITURA (GET)
    # =========================================
    def get_all_characters(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, char_class, level FROM characters")
        data = cursor.fetchall()
        conn.close()
        return data

    def get_character_full(self, char_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Dados básicos
        cursor.execute("SELECT * FROM characters WHERE id = ?", (char_id,))
        char_data = cursor.fetchone()
        
        # Recursos
        cursor.execute("SELECT id, name, max_val, current_val FROM resources WHERE char_id = ?", (char_id,))
        resources = cursor.fetchall()
        
        # Ações
        cursor.execute("SELECT * FROM actions WHERE char_id = ?", (char_id,))
        actions = cursor.fetchall()
        
        conn.close()
        return char_data, resources, actions
    
    def get_resource_value(self, char_id, resource_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT current_val FROM resources WHERE char_id = ? AND name = ?", (char_id, resource_name))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return 0

    def get_spells(self, char_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Agora pegamos a description também
        cursor.execute('SELECT name, level, school, description FROM spells WHERE character_id = ? ORDER BY level ASC', (char_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def get_resources(self, char_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Pega id, char_id, name, max, current, description
        cursor.execute("SELECT * FROM resources WHERE char_id = ?", (char_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def get_actions(self, char_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM actions WHERE char_id = ?", (char_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    # =========================================
    # ESCRITA (INSERT/UPDATE)
    # =========================================
    def update_hp(self, char_id, new_hp):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE characters SET current_hp = ? WHERE id = ?", (new_hp, char_id))
        conn.commit()
        conn.close()

    def update_resource(self, res_id, new_val):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE resources SET current_val = ? WHERE id = ?", (new_val, res_id))
        conn.commit()
        conn.close()
    
    def update_resource_direct(self, char_id, name, val, desc=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verifica se já existe
        cursor.execute("SELECT id FROM resources WHERE char_id = ? AND name = ?", (char_id, name))
        exists = cursor.fetchone()
        
        if exists:
            # Atualiza valor E descrição
            cursor.execute("""
                UPDATE resources 
                SET max_val = ?, current_val = ?, description = ? 
                WHERE id = ?
            """, (val, val, desc, exists[0]))
        else:
            # Insere novo
            cursor.execute("""
                INSERT INTO resources (char_id, name, max_val, current_val, description) 
                VALUES (?, ?, ?, ?, ?)
            """, (char_id, name, val, val, desc))
            
        conn.commit()
        conn.close()

    def seed_character(self, name, cls, lvl, hp, stats):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO characters (name, char_class, level, max_hp, current_hp, ac, save_dc, stats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, cls, lvl, hp, hp, 10, 10, stats))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Adiciona ataque padrão
        self.add_action(new_id, "Soco/Desarmado", 2, "1d4", 0)
        
        return new_id

    def add_action(self, char_id, name, atk, dice, dmg_bonus):
        conn = self.get_connection() # <--- O ERRO ESTAVA AQUI (LINHA 133)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO actions (char_id, name, atk_bonus, dmg_dice, dmg_bonus)
            VALUES (?, ?, ?, ?, ?)
        """, (char_id, name, atk, dice, dmg_bonus))
        conn.commit()
        conn.close()

    def delete_action(self, action_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM actions WHERE id = ?", (action_id,))
        conn.commit()
        conn.close()

    def add_spell(self, char_id, name, level, school="Universal", description=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO spells (character_id, name, level, school, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (char_id, name, level, school, description))
        conn.commit()
        conn.close()
    
    def roll_dice(self, dice_str):
        import random
        try:
            num, sides = map(int, dice_str.lower().split('d'))
            return sum(random.randint(1, sides) for _ in range(num))
        except:
            return 0
    def delete_character(self, char_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Apaga em cascata (primeiro os dados dependentes, depois o personagem)
        cursor.execute("DELETE FROM resources WHERE char_id = ?", (char_id,))
        cursor.execute("DELETE FROM actions WHERE char_id = ?", (char_id,))
        cursor.execute("DELETE FROM spells WHERE character_id = ?", (char_id,))
        cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
        conn.commit()
        conn.close()
