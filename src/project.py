import psycopg2
import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from datetime import *
import csv
import openpyxl
import bcrypt

class DatabaseConnector:
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def insert_service(self, values):
        """Вставка данных в таблицу services."""
        query = """
            INSERT INTO services(time, name, amount, notation, summ, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, values)
                self.conn.commit()
        except Exception as e:
            print(f"Ошибка вставки данных: {e}")

    def execute(self, query, params=()):
        """Выполнение произвольного SQL-запроса с параметром."""
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur

    def fetch_data(self, query, params=None):
        try:
            connection_params = {
                'dbname': self.dbname,
                'user': self.user,
                'password': self.password,
                'host': self.host,
                'port': self.port
            }
            conn = psycopg2.connect(**connection_params)
            cur = conn.cursor()
            if params is not None:
                cur.execute(query, params)
            else:
                cur.execute(query)
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return []

    def insert_user(self, username, hashed_password):
        """Вставка нового пользователя с хэшированным паролем."""
        query = """
            INSERT INTO users(username, password_hash)
            VALUES (%s, %s);
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (username, hashed_password))
                self.conn.commit()
        except Exception as e:
            print(f"Ошибка вставки данных: {e}")

    def close_connection(self):
        if self.conn is not None:
            self.conn.close()
            print("Соединение закрыто.")

    def fetch_users(self):
        """Возврат списка всех пользователей из БД."""
        query = "SELECT id, username FROM users;"
        return self.fetch_data(query)

    def fetch_services(self):
        """Возврат списка всех услуг из БД."""
        query = """
            SELECT p.id, p.name, po.quantity, po.price
            FROM price p
            LEFT JOIN price_options po ON p.id = po.product_id
            ORDER BY p.id, po.quantity;
        """
        return self.fetch_data(query)

    def update_user(self, user_id, new_username):
        """Изменение имени пользователя."""
        query = "UPDATE users SET username=%s WHERE id=%s;"
        self.execute(query, (new_username, user_id))
        self.conn.commit()

    def delete_user(self, user_id):
        """Удаление пользователя по ID."""
        query = "DELETE FROM users WHERE id=%s;"
        self.execute(query, (user_id,))
        self.conn.commit()

    def update_service(self, service_id, new_name, new_price):
        """Изменение названия и цены услуги."""
        query = "UPDATE price SET name=%s, price=%s WHERE id=%s;"
        self.execute(query, (new_name, new_price, service_id))
        self.conn.commit()

    def delete_service(self, service_id):
        """Удаление услуги по ID."""
        query = "DELETE FROM price WHERE id=%s;"
        self.execute(query, (service_id,))
        self.conn.commit()

    def update_user_password(self, user_id, new_hashed_password):
        """Обновление пароля пользователя."""
        query = "UPDATE users SET password_hash=%s WHERE id=%s;"
        self.execute(query, (new_hashed_password, user_id))
        self.conn.commit()

    def update_profile(self, first_name, last_name, phone, email, address, user_id):
        """Обновляет профиль пользователя."""
        query = """
            INSERT INTO data_users (user_id, first_name, last_name, phone, email, address)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                first_name=EXCLUDED.first_name,
                last_name=EXCLUDED.last_name,
                phone=EXCLUDED.phone,
                email=EXCLUDED.email,
                address=EXCLUDED.address;
        """
        self.execute(query, (user_id, first_name, last_name, phone, email, address))
        self.conn.commit()

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('LoginForm')
        self.setWindowIcon(QIcon('bliz_logo1.png'))
        self.setStyleSheet("""
            QWidget#LoginForm{
                background-color: #FFCD46;  
            }
        """)

        # Главный вертикальный макет окна
        main_layout = QVBoxLayout()

        # Контейнер для главной страницы
        container = QFrame()
        container.setObjectName('container')
        container.setStyleSheet('''
            QFrame#container {
                background-color: #FFCD46; 
            }
        ''')

        # Горизонтальная компоновка для разделения на левую и правую части
        horizontal_layout = QHBoxLayout(container)
        horizontal_layout.setSpacing(0)

        # Левая сторона (форма авторизации)
        left_side = QFrame()
        left_side.setObjectName('leftPanel')
        left_side.setStyleSheet('''
            QFrame#leftPanel {
                background-color: white;  
                border-radius: 5px;  
            }
        ''')
        left_side.setAutoFillBackground(True)
        left_side.setFrameShape(QFrame.Box)
        left_side.setFrameShadow(QFrame.Raised)
        left_side.setContentsMargins(0, 0, 0, 0)
        left_side.setMinimumWidth(600)

        # Верхний заголовок "Вход"
        header_label = QLabel("Вход", parent=left_side)
        header_label.setObjectName('headerLabel')
        header_label.setStyleSheet('''
            QLabel#headerLabel {
                font-size: 64px;
                color: #333333;
                text-align: center;
                margin-bottom: 20px; 
            }
        ''')
        header_label.setAlignment(Qt.AlignCenter)

        # Оранжевый контейнер для формы входа
        orange_container = QFrame()
        orange_container.setObjectName('orangeContainer')
        orange_container.setFixedSize(400, 200)
        orange_container.setStyleSheet('''
            #orangeContainer {
                background-color: #FFCD46;
                border-radius: 20px;
            }
        ''')

        # Внутренняя компоновка оранжевого контейнера
        inner_layout = QVBoxLayout()
        inner_layout.setSpacing(10)

        label_login = QLabel("     Логин:")
        self.login_input = QLineEdit()
        self.login_input.setMinimumWidth(350)
        self.login_input.setStyleSheet('''
            QLineEdit {
                height: 20px;
                padding: 5px;
                border: 1px solid gray;
                border-radius: 10px;
            }
        ''')
        self.login_input.setPlaceholderText("Введите логин...")
        self.login_input.setMaxLength(20)  # Ограничение максимального количества символов до 20
        inner_layout.addWidget(label_login)
        inner_layout.addWidget(self.login_input, alignment=Qt.AlignCenter)

        label_password = QLabel("     Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumWidth(350)
        self.password_input.setStyleSheet('''
            QLineEdit {
                height: 20px;
                padding: 5px;
                border: 1px solid gray;
                border-radius: 10px;
            }
        ''')
        self.password_input.setPlaceholderText("Введите пароль...")
        self.password_input.setMaxLength(20)  # Ограничение длины пароля до 20 символов
        inner_layout.addWidget(label_password)
        inner_layout.addWidget(self.password_input, alignment=Qt.AlignCenter)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.check)
        login_button.setMinimumWidth(350)
        login_button.setStyleSheet('''
            QPushButton {
                height: 25px;
                padding: 5px;
                background-color: #1E1E1E;
                color: white;
                border-radius: 10px;
            }
            QPushButton:focus {
                outline: none; /* Убираем пунктир */
            }
        ''')

        inner_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        orange_container.setLayout(inner_layout)

        # Центрирование содержимого в левом блоке
        left_inner_layout = QVBoxLayout()
        left_inner_layout.addWidget(header_label)  # Добавляем заголовочную метку
        left_inner_layout.addStretch(1)
        left_inner_layout.addWidget(orange_container, alignment=Qt.AlignCenter)
        left_inner_layout.addStretch(1)
        left_side.setLayout(left_inner_layout)

        # Правая сторона (картинка)
        right_side = QLabel()
        right_side.setPixmap(QPixmap('photo_login.jpg'))  # Путь к изображению
        right_side.setScaledContents(True)
        right_side.setMaximumWidth(600)
        right_side.setContentsMargins(0, 0, 0, 0)  # Без внутренних отступов

        # Добавляем обе части в горизонтальный макет
        horizontal_layout.addWidget(left_side)
        horizontal_layout.addWidget(right_side)

        # Вставляем контейнер с горизонтальным макетом внутрь вертикального макета
        main_layout.addWidget(container)

        # Применяем основной макет к форме
        self.setLayout(main_layout)
        self.setWindowTitle("Авторизация")
        self.setFixedSize(1200, 624)
        self.show()

    def check(self):
        username = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните оба поля')
            return

        db_connector = DatabaseConnector(
            dbname='postgres',
            user='postgres',
            password='22222',
            host='localhost',
            port='5432'
        )

        # Проверяем подключение к БД в самом начале
        if not db_connector.connect():
            QMessageBox.critical(self, 'Ошибка', 'Не удалось подключиться к базе данных.')
            return

        query = """
        SELECT id, password_hash FROM users WHERE username=%s;
        """

        result = db_connector.fetch_data(query, (username,))

        if not result:
            QMessageBox.warning(self, 'Ошибка', 'Пользователь не найден.')
            db_connector.close_connection()
            return

        user_id, stored_hash = result[0]
        stored_hash_bytes = stored_hash.tobytes()

        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                QMessageBox.information(self, 'Уведомление', 'Вы успешно вошли!')
                self.close()
                if username == "admin":
                    self.parent_window = AdminWindow()
                else:
                    self.parent_window = MainWindow(user_id)
                self.parent_window.show()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неверное имя пользователя или пароль.')

        except ValueError as e:
            print(f'Ошибка при проверке пароля: {e}')
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при проверке пароля: {e}')
        finally:
            db_connector.close_connection()

class ChangePasswordDialog(QDialog):
    def __init__(self, database_connector, user_id, parent=None):
        super().__init__(parent)
        self.database_connector = database_connector
        self.user_id = user_id

        layout = QFormLayout()

        # Поле для ввода старого пароля
        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Старый пароль:", self.old_password_input)

        # Поле для ввода нового пароля
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setMaxLength(20)  # Ограничение длины нового пароля до 20 символов
        layout.addRow("Новый пароль:", self.new_password_input)

        # Поле для подтверждения нового пароля
        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_new_password_input.setMaxLength(20)  # То же самое ограничение для повторного ввода
        layout.addRow("Повторите новый пароль:", self.confirm_new_password_input)

        # Кнопка "Сменить пароль"
        change_button = QPushButton("Сменить пароль")
        change_button.clicked.connect(self.change_password)
        layout.addWidget(change_button)

        self.setLayout(layout)
        self.setWindowTitle("Смена пароля")

    def change_password(self):
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_new_password = self.confirm_new_password_input.text()

        # Проверка на совпадение новых паролей
        if new_password != confirm_new_password:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают.")
            return

        # Получение текущего хэша пароля из базы данных
        existing_user_data = self.database_connector.fetch_data("SELECT password_hash FROM users WHERE id=%s;", (self.user_id,))
        if not existing_user_data:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")
            return

        existing_hashed_password = existing_user_data[0][0].tobytes()

        # Проверка текущего пароля
        if not bcrypt.checkpw(old_password.encode('utf-8'), existing_hashed_password):
            QMessageBox.warning(self, "Ошибка", "Некорректный старый пароль.")
            return

        # Хеширование нового пароля
        new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Обновление пароля в базе данных
        self.database_connector.update_user_password(self.user_id, new_hashed_password)
        QMessageBox.information(self, "Успешно", "Ваш пароль успешно изменён.")
        self.accept()

class AdminWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Установим соединение с базой данных
        self.database_connector = DatabaseConnector(
            dbname="postgres",
            user="postgres",
            password="22222",
            host="localhost",
            port="5432"
        )

        # Проверим подключение
        if not self.database_connector.connect():
            raise RuntimeError("Нет подключения к базе данных!")

        self.setWindowIcon(QIcon('bliz_logo1.png'))

        self.setStyleSheet("""
            QWidget {
                background-color: #FFCD46;
            }
            QLabel#headerLabel {
                font-size: 32px;
                color: #333333;
                text-align: center;
                margin-bottom: 20px;
            }
            QPushButton {
                height: 25px;
                padding: 5px;
                background-color: #1E1E1E;
                color: white;
            }
            QTableWidget {
                background-color: #FFFFFF;
                selection-background-color: #DADADA;
            }
            QTableWidget::horizontalHeader {
                background-color: #FFCD46;
                color: black;
            }
            QTableWidget::verticalHeader {
                display: none;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Табуляция для двух секций: Пользователи и Услуги
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_users_tab(), 'Пользователи')
        self.tab_widget.addTab(self.create_services_tab(), 'Услуги')

        layout.addWidget(self.tab_widget)

        self.tab_widget.setStyleSheet("""
                    QTabWidget::pane {
                        border: 1px solid #E5B533;
                        background: #FFCD46;
                    }
                    QTabBar::tab {
                        background: #1E1E1E;
                        border: 1px solid #404040;
                        padding: 10px 90px;
                        color: #FFFFFF;
                    }
                    QTabBar::tab:selected {
                        background: #333333;
                        color: #FFFFFF;
                    }
                    QTabBar {
                        background: #1E1E1E;
                    }
                """)

        self.setLayout(layout)
        self.setWindowTitle('Администрирование')
        self.setFixedSize(1200, 600)
        self.show()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        action_change_password = QAction("Сменить пароль", self)
        action_change_password.triggered.connect(
            lambda: self.show_change_password_dialog(self.users_table.currentRow()))
        menu.addAction(action_change_password)
        menu.exec_(self.users_table.mapToGlobal(pos))

    def show_change_password_dialog(self, row):
        if row >= 0:
            user_id = int(self.users_table.item(row, 0).text())
            dialog = ChangePasswordDialog(self.database_connector, user_id, self)
            dialog.exec_()

    def create_users_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Заголовок раздела
        label_admin = QLabel("Управление пользователями")
        label_admin.setObjectName('headerLabel')
        layout.addWidget(label_admin)

        # Таблица пользователей
        self.users_table = QTableWidget(0, 2)
        self.users_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self.show_context_menu)
        self.users_table.setHorizontalHeaderLabels(["ID", "Имя пользователя"])
        self.users_table.setStyleSheet("QTableWidget {background-color: #FFFFFF; }")
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.users_table.cellChanged.connect(self.on_cell_change)

        # Настройка размеров столбцов
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Подгружаем пользователей из базы данных
        self.load_users()

        # Кнопки действий над пользователями
        buttons_layout = QHBoxLayout()
        add_user_button = QPushButton("Добавить пользователя")
        del_user_button = QPushButton("Удалить пользователя")
        buttons_layout.addWidget(add_user_button)
        buttons_layout.addWidget(del_user_button)

        add_user_button.clicked.connect(self.add_user)
        del_user_button.clicked.connect(self.delete_user)

        layout.addWidget(self.users_table)
        layout.addLayout(buttons_layout)

        tab.setLayout(layout)
        return tab

    def create_services_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Заголовок секции
        label_services = QLabel("Управление услугами")
        label_services.setObjectName('headerLabel')
        layout.addWidget(label_services)

        # Таблица услуг
        self.services_table = QTableWidget(0, 3)
        self.services_table.setHorizontalHeaderLabels(["ID", "Название", "Варианты (количество : цена)"])
        self.services_table.setStyleSheet("QTableWidget {background-color: #FFFFFF; }")
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.services_table.cellChanged.connect(self.on_cell_change)

        # Настройка размеров столбцов
        self.services_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Подгружаем услуги из базы данных
        self.load_services()

        # Кнопки действий над услугами
        buttons_layout = QHBoxLayout()
        add_service_button = QPushButton("Добавить услугу")
        del_service_button = QPushButton("Удалить услугу")
        buttons_layout.addWidget(add_service_button)
        buttons_layout.addWidget(del_service_button)

        add_service_button.clicked.connect(self.add_service)
        del_service_button.clicked.connect(self.delete_service)

        layout.addWidget(self.services_table)
        layout.addLayout(buttons_layout)

        tab.setLayout(layout)
        return tab

    def load_users(self):
        """Подгружает пользователей из базы данных и показывает их в таблице."""
        data = self.database_connector.fetch_users()
        self.users_table.setRowCount(len(data))
        for row_num, row_data in enumerate(data):
            user_id, username = row_data
            self.users_table.setItem(row_num, 0, QTableWidgetItem(str(user_id)))
            self.users_table.setItem(row_num, 1, QTableWidgetItem(username))

    def load_services(self):
        """Подгружает услуги из базы данных и показывает их в таблице."""
        data = self.database_connector.fetch_services()
        unique_products = {}  # Хранит уникальные товары и их вариации

        for row_data in data:
            service_id, name, quantity, price = row_data
            if service_id not in unique_products:
                unique_products[service_id] = {"name": name, "variations": []}
            unique_products[service_id]["variations"].append({"quantity": quantity, "price": price})

        # Подготовим таблицу
        self.services_table.setRowCount(len(unique_products))
        row_num = 0
        for service_id, details in unique_products.items():
            variations_str = ", ".join(f"{v['quantity']} шт.: {v['price']}" for v in details["variations"])
            self.services_table.setItem(row_num, 0, QTableWidgetItem(str(service_id)))
            self.services_table.setItem(row_num, 1, QTableWidgetItem(details["name"]))
            self.services_table.setItem(row_num, 2, QTableWidgetItem(variations_str))
            row_num += 1

    def on_cell_change(self, row, column):
        """Реакция на изменение ячейки в таблице."""
        # Определение изменённой ячейки и её типа
        changed_item = self.users_table.item(row, column)
        if changed_item:
            value = changed_item.text()
            cell_type = self.users_table.horizontalHeaderItem(column).text()
            user_id = self.users_table.item(row, 0).text()

            if cell_type == "Имя пользователя":
                self.database_connector.update_user(int(user_id), value)

        # Подобная логика для услуг
        changed_item = self.services_table.item(row, column)
        if changed_item:
            value = changed_item.text()
            cell_type = self.services_table.horizontalHeaderItem(column).text()
            service_id = self.services_table.item(row, 0).text()

            if cell_type == "Название":
                name = value
                price = self.services_table.item(row, 2).text()
                self.database_connector.update_service(int(service_id), name, float(price))
            elif cell_type == "Варианты (количество : цена)":
                # Эта обработка зависит от конкретной логики хранения данных
                pass

    def add_user(self):
        """Добавляет нового пользователя в базу данных."""
        username, ok_pressed = QInputDialog.getText(self, "Новый пользователь", "Введите имя пользователя:")
        if ok_pressed and username.strip():
            hashed_password = bcrypt.hashpw(b"defaultpassword", bcrypt.gensalt())
            self.database_connector.insert_user(username, hashed_password)
            self.load_users()

    def delete_user(self):
        """Удаляет выбранного пользователя из базы данных."""
        selected_rows = set(index.row() for index in self.users_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну строку.")
            return

        reply = QMessageBox.question(self, 'Подтверждение', 'Вы уверены, что хотите удалить выбранных пользователей?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in sorted(selected_rows, reverse=True):
                user_id = self.users_table.item(row, 0).text()
                self.database_connector.delete_user(int(user_id))
                self.users_table.removeRow(row)

    def add_service(self):
        """Добавляет новую услугу в базу данных."""
        name, ok_pressed = QInputDialog.getText(self, "Новая услуга", "Введите название услуги:")
        if ok_pressed and name.strip():
            price, ok_pressed = QInputDialog.getDouble(self, "Цена услуги", "Введите цену услуги:")
            if ok_pressed:
                self.database_connector.insert_service((None, name, price))
                self.load_services()

    def delete_service(self):
        """Удаляет выбранную услугу из базы данных."""
        selected_rows = set(index.row() for index in self.services_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы одну строку.")
            return

        reply = QMessageBox.question(self, 'Подтверждение', 'Вы уверены, что хотите удалить выбранные услуги?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in sorted(selected_rows, reverse=True):
                service_id = self.services_table.item(row, 0).text()
                self.database_connector.delete_service(int(service_id))
                self.services_table.removeRow(row)

class ProfileEditDialog(QDialog):
    def __init__(self, initial_data, database_connector, parent=None, user_id=None):
        super().__init__(parent)
        self.initial_data = initial_data
        self.database_connector = database_connector
        self.user_id = user_id  # Идентификатор пользователя
        self.updated_data = None  # Переменная для хранения обновленных данных

        self.setStyleSheet("""
            QDialog {
                background-color: #FFCD46;
            }
        """)

        layout = QFormLayout()

        # Элементы для ввода данных
        self.first_name_input = QLineEdit(initial_data.get("first_name", ""))
        layout.addRow("Имя:", self.first_name_input)

        self.last_name_input = QLineEdit(initial_data.get("last_name", ""))
        layout.addRow("Фамилия:", self.last_name_input)

        self.phone_input = QLineEdit(initial_data.get("phone", ""))
        layout.addRow("Телефон:", self.phone_input)

        self.email_input = QLineEdit(initial_data.get("email", ""))
        layout.addRow("Email:", self.email_input)

        self.address_input = QLineEdit(initial_data.get("address", ""))
        layout.addRow("Адрес:", self.address_input)

        # Кнопка "Сохранить"
        save_button = QPushButton("Сохранить изменения")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle("Редактирование профиля")

    def save_changes(self):
        """Сохраняет изменения в профиле пользователя."""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        address = self.address_input.text().strip()

        # Проверка заполненности полей
        if not first_name or not last_name or not phone or not email or not address:
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны для заполнения.")
            return

        # Собираем обновленные данные
        self.updated_data = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "email": email,
            "address": address
        }

        self.accept()

    def get_updated_data(self):
        """Возвращает обновленные данные пользователя."""
        return self.updated_data


class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

        # Установка иконки окна
        self.setWindowIcon(QIcon('bliz_logo1.png'))
        self.setWindowTitle("Блиц-фото")
        self.setStyleSheet("""
                    QMainWindow#MainWindow{
                        background-color: #FFCD46;  
                    }
                    QMessageBox {
                        background-color: #FFCD46;
                    }
                    QMessageBox QPushButton[text="OK"] {
                        background-color: #1E1E1E;
                        color: white;
                        border-radius: 5px;
                        padding: 5px 20px;
                    }
                    QMessageBox QPushButton[text="OK"]:hover {
                        background-color: #333333;
                    }
                """)

        # Подключение к базе данных
        self.database_connector = DatabaseConnector(dbname="postgres", user="postgres", password="22222",
                                                    host="localhost", port="5432")
        if not self.database_connector.connect():
            raise RuntimeError("Нет подключения к базе данных!")

        # Основной макет приложения
        main_layout = QVBoxLayout()

        # Макет для поиска и фильтров
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по услугам...")
        filter_layout.addWidget(self.search_input)

        # Кнопка поиска
        search_button = QPushButton("Искать")
        search_button.setMinimumWidth(250)
        search_button.setStyleSheet('''
            QPushButton {
                height: 25px;
                padding: 5px;
                background-color: #1E1E1E;
                color: white;
                border-radius: 10px;
            }
            QPushButton:focus {
                outline: none; /* Убираем пунктир */
            }
        ''')
        search_button.clicked.connect(self.perform_search)
        filter_layout.addWidget(search_button)

        # Поля ввода для выбора диапазона дат
        self.start_date_input = QDateEdit()
        self.start_date_input.setDisplayFormat("yyyy-MM-dd")
        filter_layout.addWidget(self.start_date_input)

        self.end_date_input = QDateEdit()
        self.end_date_input.setDisplayFormat("yyyy-MM-dd")
        filter_layout.addWidget(self.end_date_input)

        # Добавляем фильтр в основной макет
        main_layout.addLayout(filter_layout)

        # Создание вкладок
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_services_tab(), 'Услуги')
        self.tab_widget.addTab(self.create_report_tab(), 'Отчёт')
        self.tab_widget.addTab(self.create_profile_tab(), 'Профиль')

        self.load_services_to_table()

        # Настройка стилей табов
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5B533;
                background: #FFCD46;
            }
            QTabBar::tab {
                background: #1E1E1E;
                border: 1px solid #404040;
                padding: 10px 90px;
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background: #333333;
                color: #FFFFFF;
            }
            QTabBar {
                background: #1E1E1E;
            }
        """)

        # Основная таблица находится на первой вкладке
        main_layout.addWidget(self.tab_widget)

        # Центральный виджет главного окна
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(main_layout)

        # Общий стиль окна
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFCD46;
            }
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                padding: 10px 90px;
            }
        """)

    def perform_search(self):
        search_text = self.search_input.text().strip().lower()

        # Определяем условия поиска
        conditions = []
        if search_text:
            conditions.append(f"name ILIKE '%{search_text}%'")

        # Проверяем наличие введённой даты
        start_date = self.start_date_input.date().toString(Qt.ISODate)
        end_date = self.end_date_input.date().toString(Qt.ISODate)
        if start_date != "" or end_date != "":
            date_conditions = []
            if start_date != "":
                date_conditions.append(f"service_date >= '{start_date}'")
            if end_date != "":
                date_conditions.append(f"service_date <= '{end_date}'")
            conditions.append(" AND ".join(date_conditions))

        # Формируем WHERE часть запроса
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Собираем полный запрос
        query = f"""
            SELECT id, time, name, amount, notation, summ 
            FROM services 
            {where_clause}
            ORDER BY id ASC;
        """

        # Загружаем данные в таблицу
        data = self.database_connector.fetch_data(query)
        self.services_table.clearContents()
        self.services_table.setRowCount(len(data))

        # Заполняем таблицу новыми данными
        for row_num, row_data in enumerate(data):
            record_id, time_val, name_val, amount_val, notation_val, summ_val = row_data
            self.services_table.setItem(row_num, 0, QTableWidgetItem(str(record_id)))
            self.services_table.setItem(row_num, 1, QTableWidgetItem(str(time_val)))
            self.services_table.setItem(row_num, 2, QTableWidgetItem(name_val))
            self.services_table.setItem(row_num, 3, QTableWidgetItem(str(amount_val)))
            self.services_table.setItem(row_num, 4, QTableWidgetItem(notation_val))
            self.services_table.setItem(row_num, 5, QTableWidgetItem(str(summ_val)))

    def load_report_data(self):
        """Загрузка данных из базы данных для отчета."""
        today = date.today()
        formatted_today = today.strftime('%Y-%m-%d')

        query = f"""
            SELECT SUM(summ) AS выручка,
                   SUM(CASE WHEN payment_method = 'наличные' THEN summ ELSE 0 END) AS наличные,
                   SUM(CASE WHEN payment_method = 'тинькофф' THEN summ ELSE 0 END) AS тинькофф,
                   SUM(CASE WHEN payment_method = 'сбер' THEN summ ELSE 0 END) AS сбер
            FROM services WHERE service_date = '{formatted_today}';
        """

        data = self.database_connector.fetch_data(query)
        if len(data) > 0:
            revenue, cash, tinkoff, sber = data[0]
            return {'revenue': revenue, 'cash': cash, 'tinkoff': tinkoff, 'sber': sber}
        else:
            return {}

    def update_report_fields(self, report_data):
        """Обновление значений полей отчета."""
        revenue_value = report_data.get('revenue', 0)
        cash_value = report_data.get('cash', 0)
        tinkoff_value = report_data.get('tinkoff', 0)
        sber_value = report_data.get('sber', 0)

        self.revenue_field.setText(str(revenue_value))
        self.cash_field.setText(str(cash_value))
        self.tinkoff_field.setText(str(tinkoff_value))
        self.sber_field.setText(str(sber_value))

    def create_services_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Таблица услуг
        self.services_table = QTableWidget(0, 6)
        self.services_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.services_table.setStyleSheet("QTableWidget {background-color: #FFFFFF;}")
        self.services_table.setMinimumHeight(500)  # Минимальная высота для удобочитаемости

        # Заголовки колонок
        headers = ["ID", "Время", "Наименование", "Количество", "Примечание", "Сумма"]
        self.services_table.setHorizontalHeaderLabels(headers)
        self.services_table.setColumnHidden(0, True)  # Скрываем первый столбец (ID)

        # Равномерное распределение ширины колонок
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Добавляем таблицу в макет
        layout.addWidget(self.services_table)

        # Кнопки добавления и редактирования
        button_layout = QHBoxLayout()

        # Задаем фиксированный размер кнопкам, чтобы они не растягивались
        add_button = QPushButton("Добавить запись")
        add_button.setFixedWidth(350)  # Зафиксировали ширину кнопки

        edit_button = QPushButton("Редактировать запись")
        edit_button.setFixedWidth(350)  # Зафиксировали ширину второй кнопки

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)

        # Сигналы кнопок
        add_button.clicked.connect(self.on_add_service)
        edit_button.clicked.connect(self.on_edit_service)

        # Добавляем кнопки под таблицу
        layout.addLayout(button_layout)

        return tab

    def create_report_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        white_panel = QFrame()
        white_panel.setObjectName('roundedPanel')
        white_panel.setAutoFillBackground(True)
        palette = white_panel.palette()
        palette.setColor(white_panel.backgroundRole(), QColor(Qt.white))
        white_panel.setPalette(palette)
        white_panel.setFrameShape(QFrame.NoFrame)
        white_panel.setFrameShadow(QFrame.Plain)
        white_panel.setFixedWidth(700)
        white_panel.setFixedHeight(500)

        white_panel.setStyleSheet('''
                        #roundedPanel {
                            border-radius: 20px;
                            background-color: white;
                        }
                    ''')

        report_label = QLabel('Отчёт')
        report_label.setStyleSheet('font-size: 18px; font-weight: bold')

        report_label_layout = QHBoxLayout()
        report_label_layout.addStretch(1)
        report_label_layout.addWidget(report_label)
        report_label_layout.addStretch(1)

        form_layout = QFormLayout()

        # 1. Получаем имя пользователя из базы данных
        user_profile = self.database_connector.fetch_data(
            "SELECT first_name FROM data_users WHERE user_id=%s",
            (self.user_id,)
        )

        # Если данных нет, используем пустую строку
        user_name = user_profile[0][0] if user_profile else ""

        form_layout.addRow("Дата:", QLineEdit(datetime.now().strftime("%d.%m.%Y")))
        form_layout.addRow("Имя:", QLineEdit(user_name))  # Динамическое имя
        form_layout.addRow("Остаток на начало дня:", QLineEdit())

        # Данные берем из базы данных
        self.revenue_field = QLabel("0")  # Выручка
        self.cash_field = QLabel("0")  # Наличные
        self.tinkoff_field = QLabel("0")  # Тинькофф
        self.sber_field = QLabel("0")  # Сбер

        form_layout.addRow("Выручка:", self.revenue_field)
        form_layout.addRow("Наличные:", self.cash_field)
        form_layout.addRow("Тинькофф:", self.tinkoff_field)
        form_layout.addRow("Сбер:", self.sber_field)

        button_layout = QHBoxLayout()
        calculate_button = QPushButton("Рассчитать отчет")
        export_button = QPushButton("Экспортировать отчет")
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(export_button)

        # Обработка нажатия кнопки расчета отчета
        calculate_button.clicked.connect(self.on_calculate_clicked)
        export_button.clicked.connect(self.export_report)

        # Объединяем элементы
        content_layout = QVBoxLayout()
        content_layout.addLayout(report_label_layout)
        content_layout.addLayout(form_layout)
        content_layout.addLayout(button_layout)
        white_panel.setLayout(content_layout)

        # Центрирование панели
        central_layout = QHBoxLayout()
        central_layout.addStretch(1)
        central_layout.addWidget(white_panel)
        central_layout.addStretch(1)
        layout.addLayout(central_layout)

        tab.setLayout(layout)
        return tab

    def on_calculate_clicked(self):
        """Обработчик нажатия кнопки расчёта отчёта."""
        salary_dialog = SalaryCalculationDialog(parent=self)
        salary_dialog.exec_()
        report_data = self.load_report_data()
        self.update_report_fields(report_data)

    def on_add_service(self):
        """Открытие формы добавления услуги."""
        dialog = AddServiceDialog(self)
        if dialog.exec_():  # Если форма была закрыта с подтверждением
            self.load_services_to_table()  # Перезагружаем таблицу

    def on_edit_service(self):
        """Открытие формы редактирования услуги."""
        selected_row = self.services_table.currentRow()
        if selected_row >= 0:
            # Получаем реальный ID записи
            record_id_item = self.services_table.item(selected_row, 0)
            if record_id_item:
                record_id = int(record_id_item.text())
                dialog = EditServiceDialog(self, record_id)
                if dialog.exec_():
                    self.load_services_to_table()

    def load_services_to_table(self):
        """Загрузка данных за сегодняшний день из базы данных в таблицу."""

        # Получаем объект даты для сегодняшнего дня
        today = date.today()

        # Используем параметр %s для передачи даты
        query = """
            SELECT id, time, name, amount, notation, summ 
            FROM services 
            WHERE service_date = %s 
            ORDER BY id ASC;  
        """

        params = (today,)

        data = self.database_connector.fetch_data(query, params)

        # Очищаем старую таблицу и заполняем новой...
        self.services_table.clearContents()
        self.services_table.setRowCount(len(data))
        self.services_table.setColumnCount(6)
        self.services_table.setColumnHidden(0, True)

        for row_num, row_data in enumerate(data):
            record_id, time_val, name_val, amount_val, notation_val, summ_val = row_data

            self.services_table.setItem(row_num, 0, QTableWidgetItem(str(record_id)))
            self.services_table.setItem(row_num, 1, QTableWidgetItem(str(time_val)))
            self.services_table.setItem(row_num, 2, QTableWidgetItem(name_val))
            self.services_table.setItem(row_num, 3, QTableWidgetItem(str(amount_val)))
            self.services_table.setItem(row_num, 4, QTableWidgetItem(notation_val))
            self.services_table.setItem(row_num, 5, QTableWidgetItem(str(summ_val)))

    def create_profile_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Закругленную белую панель для всей структуры
        white_panel = QFrame()
        white_panel.setObjectName('roundedPanel')
        white_panel.setAutoFillBackground(True)
        palette = white_panel.palette()
        palette.setColor(white_panel.backgroundRole(), QColor(Qt.white))
        white_panel.setPalette(palette)
        white_panel.setFrameShape(QFrame.NoFrame)
        white_panel.setFrameShadow(QFrame.Plain)
        white_panel.setFixedWidth(1000)
        white_panel.setFixedHeight(500)

        # Стили для закругления краев панели
        white_panel.setStyleSheet('''
            #roundedPanel {
                border-radius: 20px;  /* Радиус закругления углов */
                background-color: white;
            }
        ''')

        # Используем сетку для разделения пространства на две части
        grid_layout = QGridLayout()

        # Картинка пользователя (можно оставить пустым или поставить placeholder)
        self.photo_label = QLabel()  # Сделайте метку доступной в классе
        self.photo_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(self.photo_label, 0, 0, 2, 1)  # Место для фотографии

        # Кнопка для загрузки изображения
        upload_button = QPushButton("Загрузить фото")
        upload_button.clicked.connect(self.upload_image)  # Связываем событие нажатия с обработчиком
        grid_layout.addWidget(upload_button, 2, 0)  # Кнопка под фотографией

        # Правая сторона - форма с информацией
        form_layout = QFormLayout()

        # Получаем данные пользователя из базы данных
        user_id = self.user_id  # Предполагается, что идентификатор пользователя хранится в self.user_id
        user_profile = self.database_connector.fetch_data(
            "SELECT first_name, last_name, phone, email, address FROM data_users WHERE user_id=%s",
            (user_id,)
        )

        # Если данных нет, создаём пустую запись
        if not user_profile:
            user_profile = {
                "first_name": "",
                "last_name": "",
                "phone": "",
                "email": "",
                "address": ""
            }
        else:
            user_profile = dict(zip(('first_name', 'last_name', 'phone', 'email', 'address'), user_profile[0]))

        # Заполняем форму данными пользователя
        form_layout.addRow("Имя:", QLabel(user_profile.get("first_name", "")))
        form_layout.addRow("Фамилия:", QLabel(user_profile.get("last_name", "")))
        form_layout.addRow("Телефон:", QLabel(user_profile.get("phone", "")))
        form_layout.addRow("Email:", QLabel(user_profile.get("email", "")))
        form_layout.addRow("Адрес:", QLabel(user_profile.get("address", "")))

        # Заполняем вторую ячейку сеточного макета формой
        grid_layout.addLayout(form_layout, 0, 1, 2, 1)  # Формируем правую сторону с данными пользователя

        # Кнопки редактирования профиля
        button_layout = QHBoxLayout()
        edit_button = QPushButton("Редактировать профиль")
        edit_button.clicked.connect(self.open_edit_profile_dialog)
        delete_button = QPushButton("Выйти из аккаунта")
        delete_button.clicked.connect(self.out_account)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)

        # Расположение кнопок внизу сетки
        grid_layout.addLayout(button_layout, 2, 1)  # Расположим кнопки под правой стороной

        # Завершаем компоновку
        white_panel.setLayout(grid_layout)

        # Центрирование панели
        central_layout = QHBoxLayout()
        central_layout.addStretch(1)
        central_layout.addWidget(white_panel)
        central_layout.addStretch(1)
        layout.addLayout(central_layout)

        tab.setLayout(layout)
        return tab

    def open_edit_profile_dialog(self):
        """Открывает диалоговое окно для редактирования профиля."""
        # Получаем текущие данные пользователя из базы данных
        profile_data = self.database_connector.fetch_data(
            "SELECT first_name, last_name, phone, email, address FROM data_users WHERE user_id=%s",
            (self.user_id,)
        )

        if not profile_data:
            default_profile_data = {
                "first_name": "",
                "last_name": "",
                "phone": "",
                "email": "",
                "address": ""
            }
        else:
            default_profile_data = dict(zip(("first_name", "last_name", "phone", "email", "address"), profile_data[0]))

        dialog = ProfileEditDialog(default_profile_data, self.database_connector, self, user_id=self.user_id)

        # Результат выполнения диалога (Accepted - ОК, Rejected - Отмена)
        if dialog.exec_() == QDialog.Accepted:
            # Диалог закрыт с сохранением изменений
            updated_data = dialog.get_updated_data()
            self.database_connector.update_profile(
                updated_data["first_name"], updated_data["last_name"],
                updated_data["phone"], updated_data["email"],
                updated_data["address"], self.user_id
            )
            QMessageBox.information(self, "Успех", "Ваш профиль успешно обновлён.")

            # Находим индекс вкладки "Профиль"
            profile_index = None
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == 'Профиль':
                    profile_index = i
                    break

            if profile_index is not None:
                # Удаляем старую вкладку
                old_tab = self.tab_widget.widget(profile_index)
                self.tab_widget.removeTab(profile_index)

                # Создаем новую вкладку с обновленными данными
                new_tab = self.create_profile_tab()

                # Вставляем её на то же место
                self.tab_widget.insertTab(profile_index, new_tab, 'Профиль')

                # Возвращаем фокус на неё (если она была открыта)
                self.tab_widget.setCurrentIndex(profile_index)

            # Находим индекс вкладки "Отчёт"
            report_tab_index = None
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == 'Отчёт':
                    report_tab_index = i
                    break

            # Если вкладка "Отчёт" существует, обновляем её
            if report_tab_index is not None:
                # Запоминаем, была ли она открыта в этот момент
                was_active = (self.tab_widget.currentIndex() == report_tab_index)

                # Удаляем старую вкладку
                self.tab_widget.removeTab(report_tab_index)

                # Создаем новую вкладку с обновленными данными
                new_report_tab = self.create_report_tab()

                # Вставляем новую вкладку на старое место
                self.tab_widget.insertTab(report_tab_index, new_report_tab, 'Отчёт')

                # Если она была открыта, возвращаем фокус на неё
                if was_active:
                    self.tab_widget.setCurrentIndex(report_tab_index)

    def out_account(self):
        self.close()

    def upload_image(self):
        """Метод для загрузки изображения"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выбор изображения",
            "",
            "Images (*.png *.jpg *.bmp);;All Files (*)",
            options=options
        )
        if file_name:
            pixmap = QPixmap(file_name).scaledToWidth(200)
            self.photo_label.setPixmap(pixmap)
            self.photo_label.adjustSize()

    def export_report(self):
        options = QFileDialog.Options()

        file_filter = "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет",
            None,
            file_filter,
            options=options
        )

        if not file_name:
            return

        try:
            if file_name.lower().endswith('.csv'):
                self._save_as_csv(file_name)
            elif file_name.lower().endswith('.xlsx'):
                self._save_as_excel(file_name)
            else:
                if 'CSV' in selected_filter and not file_name.lower().endswith('.csv'):
                    file_name += '.csv'
                    self._save_as_csv(file_name)
                elif 'Excel' in selected_filter and not file_name.lower().endswith('.xlsx'):
                    file_name += '.xlsx'
                    self._save_as_excel(file_name)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось определить формат файла.")
                    return

            QMessageBox.information(self, "Успех", f"Отчет успешно экспортирован в файл:\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def _save_as_csv(self, filename):
        """Сохраняет данные в формате CSV."""
        with open(filename, 'w', newline='',
                  encoding='utf-8-sig') as file:  # utf-8-sig для корректного открытия в Excel
            writer = csv.writer(file)

            # Шапка таблицы
            headers = ["Время", "Наименование", "Количество", "Цена", "Тип оплаты", "Итоговая стоимость"]
            writer.writerow(headers)

            # Данные из таблицы
            rows_count = self.services_table.rowCount()
            cols_count = self.services_table.columnCount()

            for row in range(rows_count):
                row_data = []
                for col in range(cols_count):
                    item = self.services_table.item(row, col)
                    row_data.append(item.text() if item is not None else "")
                writer.writerow(row_data)

    def _save_as_excel(self, filename):
        """Сохраняет данные в формате Excel (.xlsx)."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Отчет"

        # Записываем заголовки
        headers = ["Время", "Наименование", "Количество", "Цена", "Тип оплаты", "Итоговая стоимость"]
        ws.append(headers)

        # Применяем жирный шрифт к заголовкам
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)

        # Записываем данные из таблицы
        rows_count = self.services_table.rowCount()
        cols_count = self.services_table.columnCount()

        for row in range(rows_count):
            row_data = []
            for col in range(cols_count):
                item = self.services_table.item(row, col)
                row_data.append(item.text() if item is not None else "")
            ws.append(row_data)

        # Сохраняем файл
        wb.save(filename)

class AddServiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db_connector = parent.database_connector
        self.init_ui()
        self.setWindowTitle("Добавление записи")
        self.setWindowIcon(QIcon('bliz_logo1.png'))
        self.setStyleSheet("""
            QDialog {
                background-color: #FFCD46;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Поле времени
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        form_layout.addRow("Время:", self.time_input)

        # Название услуги (с возможностью автодополнения)
        self.name_input = QLineEdit()
        completer = QCompleter()
        model = QStringListModel()
        self.load_names_from_db(model)
        completer.setModel(model)
        self.name_input.setCompleter(completer)
        form_layout.addRow("Название:", self.name_input)

        # Выбор количества (поле ввода с поддержкой прямого ввода)
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator())
        self.amount_input.textEdited.connect(self.update_price)
        form_layout.addRow("Количество:", self.amount_input)

        # Итоговая сумма
        self.summ_input = QLabel()
        form_layout.addRow("Сумма:", self.summ_input)

        # Способ оплаты
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(['наличные', 'тинькофф', 'сбер'])
        form_layout.addRow("Способ оплаты:", self.payment_method_combo)

        # Добавляем форму в основную компоновку
        layout.addLayout(form_layout)

        # Кнопка отправки
        submit_button = QPushButton("Добавить услугу")
        submit_button.clicked.connect(self.submit_service)
        layout.addWidget(submit_button)

        self.setLayout(layout)

        # Подключаем сигналы:
        self.name_input.textEdited.connect(self.on_name_changed)
        self.name_input.editingFinished.connect(self.on_name_changed)  # Вызвать обновление после завершения ввода

    def load_names_from_db(self, model):
        """Загружаем доступные услуги из базы данных"""
        results = self.db_connector.fetch_data("SELECT DISTINCT name FROM price;")
        service_names = [item[0].strip() for item in results]  # Чистим пробелы
        model.setStringList(service_names)

    def update_amount_options(self):
        """Обновляет доступные варианты количества для текущего выбранного товара."""
        selected_name = self.name_input.text().strip()

        if not selected_name:
            return

        # Получаем product_id по наименованию товара
        product_result = self.db_connector.fetch_data(
            "SELECT id FROM price WHERE name=%s",
            (selected_name,)
        )

        if not product_result:
            # Товара нет в базе, разрешаем произвольный ввод
            self.amount_input.clear()
            self.amount_input.setPlaceholderText("Введите нужное количество")
            return

        product_id = product_result[0][0]

        # Проверяем, есть ли комбинации количества для этого product_id
        option_results = self.db_connector.fetch_data(
            "SELECT quantity FROM price_options WHERE product_id=%s",
            (product_id,)
        )

        if option_results:
            # Продукт есть в price_options
            has_quantity_one = any(row[0] == 1 for row in option_results)

            if has_quantity_one and product_id != 8:
                # Можно выбрать произвольное количество, кроме product_id = 8
                self.amount_input.clear()
                self.amount_input.setPlaceholderText("Введите нужное количество")
            elif product_id == 8:
                # Фиксированное количество 1 для product_id = 8
                self.amount_input.clear()
                self.amount_input.setText("1")  # Прямо задаём значение
            else:
                # Показываем доступные фиксированные варианты
                quantities = list(set(row[0] for row in option_results))
                quantities.sort()
                # Поскольку мы работаем с QLineEdit, оставляем его доступным для ввода
                self.amount_input.clear()
                self.amount_input.setPlaceholderText("Доступные значения: {}".format(", ".join(map(str, quantities))))
        else:
            # Товара нет в price_options, разрешен произвольный ввод
            self.amount_input.clear()
            self.amount_input.setPlaceholderText("Введите нужное количество")

    def update_price(self):
        """Обновляет итоговую сумму на основе выбранного количества и товара."""
        selected_name = self.name_input.text().strip()
        amount_text = self.amount_input.text()  # Теперь используем .text() вместо currentText()

        if not selected_name or not amount_text:
            return

        try:
            amount = int(amount_text)
        except ValueError:
            # Пользователь ввёл некорректное значение, оставляем сумму пустой
            self.summ_input.setText("")
            return

        # Получаем product_id по наименованию товара
        product_result = self.db_connector.fetch_data(
            "SELECT id FROM price WHERE name=%s",
            (selected_name,)
        )

        if not product_result:
            # Товара нет в базе, сообщаем об ошибке
            self.summ_input.setText("Товар отсутствует в базе данных")
            return

        product_id = product_result[0][0]

        # Проверяем, есть ли фиксированная цена для указанной комбинации
        exact_match_results = self.db_connector.fetch_data(
            "SELECT price FROM price_options WHERE product_id=%s AND quantity=%s",
            (product_id, amount)
        )

        if exact_match_results:
            # Нашли точное совпадение, используем фиксированную цену
            fixed_price = exact_match_results[0][0]
            self.summ_input.setText(f"{fixed_price:.2f}")
        else:
            # Проверяем, есть ли базовая цена для этого товара
            base_price_results = self.db_connector.fetch_data(
                "SELECT price FROM price_options WHERE product_id=%s",
                (product_id,)
            )

            if base_price_results:
                # Имеются базовые цены, можем рассчитать итоговую сумму
                base_price = base_price_results[0][0]
                total_price = base_price * amount
                self.summ_input.setText(f"{float(total_price):.2f}")
            else:
                # Если ни фиксированного, ни базового варианта нет, выдаём ошибку
                self.summ_input.setText("Недоступное количество или неизвестная цена")

    def submit_service(self):
        """Отправляем данные в базу данных."""
        time_value = self.time_input.text()
        name_value = self.name_input.text().strip()  # чистим только пробелы
        amount_value = int(self.amount_input.text())
        notation_value = ""  # примечание пока пустое

        # Просто берем текст метки и пытаемся превратить его в число
        summ_value_str = self.summ_input.text()
        if summ_value_str != "Нет подходящей опции":  # Проверяем условие на валидный текст
            summ_value = float(summ_value_str)
        else:
            summ_value = 0

        payment_method_value = self.payment_method_combo.currentText()

        values = (
            time_value, name_value, amount_value, notation_value, summ_value, payment_method_value
        )
        self.db_connector.insert_service(values)
        self.accept()

    def on_name_changed(self):
        """Обработчик события изменения имени услуги"""
        self.update_amount_options()
        self.update_price()

class EditServiceDialog(QDialog):
    def __init__(self, parent, record_id):
        super().__init__(parent)
        self.parent = parent
        self.record_id = record_id  # Сохраняем ID записи
        self.db_connector = parent.database_connector
        self.init_ui()
        self.fill_form_with_existing_data()
        self.setWindowTitle("Редактирование записи")
        self.setWindowIcon(QIcon('bliz_logo1.png'))
        self.setStyleSheet("""
            QDialog {
                background-color: #FFCD46;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Поле времени
        self.time_input = QTimeEdit()
        form_layout.addRow("Время:", self.time_input)

        # Название услуги (с возможностью автодополнения)
        self.name_input = QLineEdit()
        completer = QCompleter()
        model = QStringListModel()
        self.load_names_from_db(model)
        completer.setModel(model)
        self.name_input.setCompleter(completer)
        form_layout.addRow("Название:", self.name_input)

        # Выбор количества (текстовое поле ввода)
        self.amount_input = QLineEdit()  # Используем QLineEdit для ввода количества
        validator = QIntValidator()      # Ограничиваем ввод только целыми числами
        self.amount_input.setValidator(validator)
        form_layout.addRow("Количество:", self.amount_input)

        # Итоговая сумма (QLabel)
        self.summ_input = QLabel()       # Используем QLabel для отображения суммы
        form_layout.addRow("Сумма:", self.summ_input)

        # Примечание
        self.notation_input = QLineEdit()
        form_layout.addRow("Примечание:", self.notation_input)

        # Выпадающий способ оплаты
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(['наличные', 'тинькофф', 'сбер'])
        form_layout.addRow("Способ оплаты:", self.payment_method_combo)

        # Добавляем форму в основную компоновку
        layout.addLayout(form_layout)

        # Кнопка сохранения
        submit_button = QPushButton("Сохранить изменения")
        submit_button.clicked.connect(self.save_edits)
        layout.addWidget(submit_button)

        self.setLayout(layout)

        # Подключаем сигналы:
        self.name_input.textEdited.connect(self.on_name_changed)
        self.amount_input.textEdited.connect(self.on_amount_changed)  # Следим за изменением текста

    def load_names_from_db(self, model):
        """Загружаем доступные услуги из базы данных"""
        results = self.db_connector.fetch_data("SELECT DISTINCT name FROM price;")
        service_names = [item[0].strip() for item in results]  # Чистим пробелы
        model.setStringList(service_names)

    def fill_form_with_existing_data(self):
        """Заполняем форму данными из текущей строки."""
        # Получаем данные из базы данных по ID записи
        query = f"""
            SELECT time, name, amount, notation, summ, payment_method
            FROM services
            WHERE id = {self.record_id};
        """
        data = self.db_connector.fetch_data(query)

        if data:
            row_data = data[0]
            # Преобразуем объект time в строку перед передачей в QTime.fromString
            time_str = row_data[0].strftime("%H:%M:%S")
            self.time_input.setTime(QTime.fromString(time_str, "HH:mm:ss"))
            self.name_input.setText(row_data[1])
            self.amount_input.setText(str(row_data[2]))  # Устанавливаем количество
            self.notation_input.setText(row_data[3])
            self.summ_input.setText(str(row_data[4]))
            self.payment_method_combo.setCurrentText(row_data[5])

    def update_amount_options(self):
        """Обновляет доступные варианты количества для текущего выбранного товара."""
        pass  # Больше не нужно, так как мы используем QLineEdit для ввода количества

    def update_price(self):
        """Обновляет итоговую сумму на основе выбранного количества и товара."""
        selected_name = self.name_input.text().strip()
        amount_text = self.amount_input.text()

        if not selected_name or not amount_text:
            return

        try:
            amount = int(amount_text)
        except ValueError:
            # Некорректное значение, очищаем сумму
            self.summ_input.setText("")
            return

        # Получаем product_id по наименованию товара
        product_result = self.db_connector.fetch_data(
            "SELECT id FROM price WHERE name=%s",
            (selected_name,)
        )

        if not product_result:
            # Товара нет в базе, сообщаем об ошибке
            self.summ_input.setText("Товар отсутствует в базе данных")
            return

        product_id = product_result[0][0]

        # Проверяем, есть ли фиксированная цена для указанной комбинации
        exact_match_results = self.db_connector.fetch_data(
            "SELECT price FROM price_options WHERE product_id=%s AND quantity=%s",
            (product_id, amount)
        )

        if exact_match_results:
            # Нашли точное совпадение, используем фиксированную цену
            fixed_price = exact_match_results[0][0]
            self.summ_input.setText(f"{fixed_price:.2f}")
        else:
            # Проверяем, есть ли базовая цена для этого товара
            base_price_results = self.db_connector.fetch_data(
                "SELECT price FROM price_options WHERE product_id=%s",
                (product_id,)
            )

            if base_price_results:
                # Имеются базовые цены, можем рассчитать итоговую сумму
                base_price = base_price_results[0][0]
                total_price = base_price * amount
                self.summ_input.setText(f"{total_price:.2f}")
            else:
                self.summ_input.setText("Базовая цена не задана")

    def save_edits(self):
        """Сохранение изменений в базе данных."""
        time_value = self.time_input.text()
        name_value = self.name_input.text().strip()  # чистим только пробелы
        amount_value = int(self.amount_input.text())  # Используем .text() для QLineEdit
        notation_value = self.notation_input.text()
        summ_value = float(self.summ_input.text())

        payment_method_value = self.payment_method_combo.currentText()

        new_values = (
            time_value, name_value, amount_value, notation_value, summ_value, payment_method_value
        )

        # Логгирование данных перед обновлением
        print("Данные для обновления:")
        print(
            f"Время: {time_value}, Название: {name_value}, Кол-во: {amount_value}, Примечание: {notation_value}, Сумма: {summ_value}, Платеж: {payment_method_value}"
        )

        update_query = """
            UPDATE services SET
                time=%s,
                name=%s,
                amount=%s,
                notation=%s,
                summ=%s,
                payment_method=%s
            WHERE id=%s;
        """

        try:
            # Объединяем new_values и self.record_id в один кортеж
            all_values = (*new_values, self.record_id)
            self.db_connector.execute(update_query, all_values)
            self.db_connector.conn.commit()  # Подтверждаем транзакцию
            self.accept()  # Закрываем диалог успешно
        except Exception as e:
            print(f"Ошибка при сохранении изменений: {e}")

    def on_name_changed(self):
        """Обработчик события изменения имени услуги"""
        self.update_price()

    def on_amount_changed(self):
        """Обновляем цену при изменении количества"""
        self.update_price()

class SalaryCalculationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Инициализация интерфейса
        self.init_ui()
        self.setWindowIcon(QIcon('bliz_logo1.png'))
        self.setStyleSheet("""
                    QDialog {
                        background-color: #FFCD46;
                    }
                """)

    def init_ui(self):
        layout = QVBoxLayout()

        # Создаем формы для полей ввода
        form_layout = QFormLayout()

        # Остаток по зарплате предыдущий
        self.prev_salary_input = QLineEdit()
        form_layout.addRow("Остаток по зп предыдущий:", self.prev_salary_input)

        # Выход (например, премиальные выплаты)
        self.exit_input = QLineEdit()
        form_layout.addRow("Выход:", self.exit_input)

        # Автоматический расчет 7% от общей выручки
        self.seven_percent_label = QLabel("7%:")
        form_layout.addRow("", self.seven_percent_label)

        # Металлокерамика
        self.metall_input = QLineEdit()
        form_layout.addRow("Металлокерамика:", self.metall_input)

        # Полиграфия
        self.print_input = QLineEdit()
        form_layout.addRow("Полиграфия:", self.print_input)

        # Формат A3
        self.a3_input = QLineEdit()
        form_layout.addRow("A3:", self.a3_input)

        # Графический дизайн
        self.graphic_design_input = QLineEdit()
        form_layout.addRow("Граф дизайн:", self.graphic_design_input)

        # Отзыв (возможно бонус или штраф)
        self.review_input = QLineEdit()
        form_layout.addRow("Отзыв:", self.review_input)

        # Выход в выходной день
        self.weekend_exit_input = QLineEdit()
        form_layout.addRow("Выход в выходной день:", self.weekend_exit_input)

        # Опоздания (штрафы)
        self.late_input = QLineEdit()
        form_layout.addRow("Опоздание:", self.late_input)

        # Получено денег
        self.received_input = QLineEdit()
        form_layout.addRow("Получено:", self.received_input)

        # Расчет остатка по зарплате
        self.final_salary_label = QLabel("Остаток по зп:")
        form_layout.addRow("", self.final_salary_label)

        # Добавляем форму в общую компоновку
        layout.addLayout(form_layout)

        # Кнопка расчета
        calculate_button = QPushButton("Рассчитать зарплату")
        calculate_button.clicked.connect(self.calculate_salary)
        layout.addWidget(calculate_button)

        # Устанавливаем общий макет
        self.setLayout(layout)
        self.setWindowTitle("Расчёт заработной платы")
        self.setWindowIcon(QIcon('salary_icon.png'))  # иконка окна
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F0F0;
            }
        """)

    def calculate_salary(self):
        """
        Метод рассчитывает итоговую заработную плату сотрудника,
        учитывая введённые поля и автоматическое вычисление некоторых значений.
        """
        prev_salary = float(self.prev_salary_input.text() or 0)
        exit_value = float(self.exit_input.text() or 0)
        metall = float(self.metall_input.text() or 0)
        print_val = float(self.print_input.text() or 0)
        a3 = float(self.a3_input.text() or 0)
        graphic_design = float(self.graphic_design_input.text() or 0)
        review = float(self.review_input.text() or 0)
        weekend_exit = float(self.weekend_exit_input.text() or 0)
        late_penalty = float(self.late_input.text() or 0)
        received = float(self.received_input.text() or 0)

        # Вычисляем процент от общей выручки (7%)
        total_revenue = sum([metall, print_val, a3, graphic_design])
        seven_percent = round(total_revenue * 0.07, 2)
        self.seven_percent_label.setText(f"7%: {seven_percent:.2f}")  # отображаем автоматически подсчитанный %

        # Рассчитываем итоговую зарплату
        final_salary = prev_salary + exit_value + seven_percent + review + weekend_exit - late_penalty - received
        self.final_salary_label.setText(f"Остаток по зп: {final_salary:.2f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMessageBox {
            background-color: #FFCD46;
        }
        QMessageBox QPushButton[text="OK"] {
            background-color: #1E1E1E;
            color: white;
            border-radius: 5px;
            padding: 5px 20px;
        }
        QMessageBox QPushButton[text="OK"]:hover {
            background-color: #333333;
        }
    """)
    window = LoginForm()
    window.show()
    sys.exit(app.exec())