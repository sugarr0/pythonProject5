import sys
import sqlite3
import datetime as dt

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QLabel, QDialog, \
    QPushButton, QLineEdit, QSpinBox


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reader_id = None
        self.updates = []
        self.open1()

    def open1(self):
        uic.loadUi('untitled1.ui', self)
        self.setWindowTitle('Книги')
        self.btn1.clicked.connect(self.open2)
        self.connection = sqlite3.connect("books.db")
        self.find_t.clicked.connect(self.find_title)
        self.tableWidget.itemChanged.connect(self.item_changed)
        self.btn_save.clicked.connect(self.save_results)
        self.btn_delete.clicked.connect(self.delete)
        self.btn_add.clicked.connect(self.add_el)
        self.find_title()

    def find_title(self):
        cur = self.connection.cursor()
        title = self.lineEdit.text()
        if title == '':
            res = cur.execute(f"""SELECT Books.id, Authors.Name, Books.Title, Books.Stylage, Books.Shelf
            FROM Books
            LEFT JOIN Authors ON Authors.id = Books.AutorId""").fetchall()
        else:
            res = cur.execute(f"""SELECT Books.id, Authors.Name, Books.Title, Books.Stylage, Books.Shelf
            FROM Books
            LEFT JOIN Authors ON Authors.id = Books.AutorId
            WHERE Title=?""", (title,)).fetchall()
        if not res:
            self.label.setText('Такой книги нет')
            return
        self.tableWidget.setRowCount(len(res))
        self.tableWidget.setColumnCount(len(res[0]))
        self.titles = ['id', 'author', 'Title', 'Stylage', 'Shelf']
        titles = ['id', 'Автор', 'Название', 'Стрилаж', 'Полка']
        for i, elem in enumerate(res):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableWidget.setHorizontalHeaderLabels(titles)
        self.label.setText('')

    def item_changed(self, item):
        que = "UPDATE Books\nSET "
        que += f"{self.titles[item.column()]} = '{item.text()}'\n"
        que += f"WHERE id = '{self.tableWidget.item(item.row(), 0).text()}'"
        if self.titles[item.column()] not in ('id', 'author'):
            self.updates.append(que)
        elif self.titles[item.column()] == 'author':
            a = self.author_verification(item.text())
            que = "UPDATE Books\nSET "
            que += f"AutorId = '{a}'\n"
            que += f"WHERE id = '{self.tableWidget.item(item.row(), 0).text()}'"
            self.updates.append(que)

    def author_verification(self, aut):
        cur = self.connection.cursor()
        authors = cur.execute(f"""SELECT id FROM Authors
                            WHERE Name = ?""", (aut,)).fetchall()
        if not authors:
            cur.execute("""INSERT INTO Authors(Name) VALUES(?)""", (aut,))
            authors = cur.execute(f"""SELECT id FROM Authors
                                    WHERE Name = ?""", (aut,)).fetchall()
        return authors[0][0]

    def save_results(self):
        if self.updates:
            cur = self.connection.cursor()
            for i in self.updates:
                cur.execute(i)
                self.connection.commit()
            self.updates = []

    def delete(self):
        rows = list(set([i.row() for i in self.tableWidget.selectedItems()]))
        ids = [self.tableWidget.item(i, 0).text() for i in rows]
        ansv = QMessageBox.question(self, '', "Удалить эти элементы?",
                                    QMessageBox.Yes, QMessageBox.No)
        if ansv == QMessageBox.Yes:
            cur = self.connection.cursor()
            cur.execute("DELETE FROM Books WHERE id IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.connection.commit()
            cur2 = self.connection.cursor()
            cur2.execute("DELETE FROM ReadersBooks WHERE BookId IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.connection.commit()
        self.find_title()

    def add_el(self):
        self.add_form = AddBookForm(self)
        self.add_form.exec()

    def add_book(self, res):
        if res not in [(1,), (0,)]:
            self.label.setText('Завершено')
            aut, tit, sh, polc = [i for i in res]
            cur = self.connection.cursor()
            autId = self.author_verification(aut)
            books = cur.execute(f"""SELECT id FROM Books
                    WHERE Title = ? AND AutorId = ?""", (tit, autId)).fetchall()
            if books:
                self.label.setText('Эта книга уже есть в библиотеке')
            else:
                cur.execute("""INSERT INTO Books(AutorId, Title, Stylage, Shelf) VALUES(?, ?, ?, ?)""",
                            (autId, tit, sh, polc))
            self.connection.commit()
            self.find_title()
        elif res == (1,):
            self.label.setText('Заполните поля верно')
        else:
            self.label.setText('')

    def closeEvent(self, event):
        self.connection.close()

    def open2(self):
        uic.loadUi('untitled2.ui', self)
        self.setWindowTitle('Читатели')
        self.btn2.clicked.connect(self.open1)
        self.updates = []
        self.btnFindName.clicked.connect(self.find_readers)
        self.get.clicked.connect(self.show_books)
        self.delete_reader.clicked.connect(self.delete_readers)
        self.add_readerbook.clicked.connect(self.add_book_readers)
        self.delete_readerbook.clicked.connect(self.delete_book_readers)
        self.add_reader.clicked.connect(self.add_read)
        self.btnFindId.clicked.connect(self.find_id)
        self.find_readers()

    def find_readers(self):
        self.overdue()
        cur = self.connection.cursor()
        name = self.lineName.text()
        if name == '':
            res = cur.execute(f"""SELECT * FROM Readers""").fetchall()
            self.spinBox.setValue(0)
        else:
            res = cur.execute(f"""SELECT * FROM Readers
            WHERE FullName=?""", (name,)).fetchall()
        if not res:
            self.label.setText('Этот человек не брал книг в нашей библиотеке')
            return
        res = sorted(res, key=lambda x: x[2], reverse=True)
        self.tableReaders.setRowCount(len(res))
        self.tableReaders.setColumnCount(len(res[0]))
        self.titles = ['id', 'Полное имя', 'Количество книг', 'Задержка книги', 'Серия', 'Номер']
        for i, elem in enumerate(res):
            for j, val in enumerate(elem):
                self.tableReaders.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableReaders.setHorizontalHeaderLabels(self.titles)
        self.label.setText('')

    def find_id(self):
        cur = self.connection.cursor()
        ib = self.spinBox.text()
        if ib == '0':
            res = cur.execute(f"""SELECT * FROM Readers""").fetchall()
            self.lineName.setText('')
        else:
            res = cur.execute(f"""SELECT * FROM Readers
                    WHERE id=?""", (ib,)).fetchall()
        if not res:
            self.label.setText('Читатель отсутствует')
            return
        res = sorted(res, key=lambda x: x[2], reverse=True)
        self.tableReaders.setRowCount(len(res))
        self.tableReaders.setColumnCount(len(res[0]))
        self.titles = ['id', 'Полное имя', 'Количество книг', 'Задержка книги', 'Серия', 'Номер']
        for i, elem in enumerate(res):
            for j, val in enumerate(elem):
                self.tableReaders.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableReaders.setHorizontalHeaderLabels(self.titles)
        self.label.setText('')

    def overdue(self):
        cur = self.connection.cursor()
        cur.execute("""UPDATE Readers SET Overdue = 0""")
        res = cur.execute(f"""SELECT ReaderId, Date
                                    FROM ReadersBooks""").fetchall()
        for i, el in enumerate(res):
            today = dt.date.today()
            day = dt.date(int(el[1].split('.')[2]), int(el[1].split('.')[1]), int(el[1].split('.')[0]))
            if today > day:
                cur.execute("""UPDATE Readers SET Overdue = Overdue + 1 WHERE id = ?""",
                            (el[0],))

    def show_books(self):
        cur = self.connection.cursor()
        try:
            row = self.tableReaders.selectedItems()[0].row()
        except IndexError:
            self.label.setText('Выберете читателя')
            return
        ind = self.tableReaders.item(row, 0).text()
        res = cur.execute(f"""SELECT Books.Title, Authors.Name, ReadersBooks.Date
                        FROM ReadersBooks
                        LEFT JOIN Books ON Books.id = ReadersBooks.BookId
                        LEFT JOIN Authors ON Authors.id = Books.AutorId
                        WHERE ReaderId=?""", (ind,)).fetchall()
        if not res:
            self.label.setText('Этот читатель ещё не брал книги')
            return
        today = dt.date.today()
        self.reader_id = ind
        self.tableBooks.setRowCount(len(res))
        self.tableBooks.setColumnCount(len(res[0]))
        titles = ['Название', 'Автор', 'Дата возврата']
        for i, elem in enumerate(res):
            for j, val in enumerate(elem):
                self.tableBooks.setItem(i, j, QTableWidgetItem(str(val)))
                if j == 2:
                    day = dt.date(int(val.split('.')[2]), int(val.split('.')[1]), int(val.split('.')[0]))
                    if today > day:
                        self.tableBooks.item(i, j).setBackground(QtGui.QColor(200, 100, 100))
        self.tableBooks.setHorizontalHeaderLabels(titles)
        self.label.setText('')

    def delete_readers(self):
        rows = list(set([i.row() for i in self.tableReaders.selectedItems()]))
        ids = [self.tableReaders.item(i, 0).text() for i in rows]
        if not ids:
            self.label.setText('Выберите читателя')
            return
        ansv = QMessageBox.question(self, '', "Удалить эти элементы?",
                                    QMessageBox.Yes, QMessageBox.No)
        if ansv == QMessageBox.Yes:
            cur = self.connection.cursor()
            cur.execute("DELETE FROM Readers WHERE id IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.connection.commit()
            cur2 = self.connection.cursor()
            cur2.execute("DELETE FROM ReadersBooks WHERE ReaderId IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.connection.commit()
        self.find_readers()

    def add_book_readers(self):
        try:
            row = self.tableReaders.selectedItems()[0].row()
        except Exception:
            self.label.setText('Выберете читателя')
            return
        self.reader_id = self.tableReaders.item(row, 0).text()
        overdue = self.connection.cursor().execute(f"""SELECT Overdue FROM Readers
                            WHERE id = ?""", (self.reader_id,)).fetchall()
        if overdue[0][0] != 0:
            self.label.setText('Сначала верните книги, которые залежались у вас')
            return
        else:
            self.label.setText('')
        self.form = AddBookReader(self, self.reader_id)
        self.form.exec()

    def delete_book_readers(self):
        rows = list(set([i.row() for i in self.tableBooks.selectedItems()]))
        title = [self.tableBooks.item(i, 0).text() for i in rows]
        authorId = [self.tableBooks.item(i, 1).text() for i in rows]
        if not title:
            self.label.setText('Выберите книги')
            return
        ansv = QMessageBox.question(self, '', "Удалить эти книги?",
                                    QMessageBox.Yes, QMessageBox.No)
        if ansv == QMessageBox.Yes:
            cur = self.connection.cursor()
            ids = []
            for i in range(len(title)):
                ids.extend(cur.execute(f"""SELECT Books.id FROM Books 
                LEFT JOIN Authors ON Authors.id = Books.AutorId
                WHERE Books.Title = ? AND Authors.Name = ?""", (title[i], authorId[i])).fetchall())
            ids = [elem[0] for j, elem in enumerate(ids)]
            cur.execute("""UPDATE Readers SET Count = Count - ? WHERE id = ?""",
                        (len(ids), self.reader_id))
            cur.execute(f"DELETE FROM ReadersBooks WHERE ReaderId = {self.reader_id} AND BookId IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.connection.commit()
        self.show_books()
        self.find_readers()

    def add_read(self):
        self.addReader = AddReader(self)
        self.addReader.exec()

    def addForReader(self, res):
        ids = res[0]
        d = res[1]
        cur = self.connection.cursor()
        for i in ids:
            n = cur.execute(f"""SELECT * FROM ReadersBooks
             WHERE ReaderId = ? AND BookId = ?""", (self.reader_id, i)).fetchall()
            if not n:
                cur1 = self.connection.cursor()
                cur1.execute("""INSERT INTO ReadersBooks(ReaderId, BookId, Date) VALUES(?, ?, ?)""",
                             (self.reader_id, i, d))
                self.connection.commit()
                cur.execute("""UPDATE Readers SET Count = Count + 1 WHERE id = ?""",
                            (self.reader_id,))
                self.connection.commit()
        self.show_books()
        self.find_readers()

    def new_reader(self, res):
        name = res[0]
        series = res[1]
        number = res[2]
        cur = self.connection.cursor()
        cur.execute(
            """INSERT INTO Readers(FullName, Count, Overdue, Series, Number) VALUES(?, 0, 0, ?, ?)""",
            (name, series, number))
        self.connection.commit()
        self.find_readers()
        f = open(name + ".txt", 'w')
        i = cur.execute(f"""SELECT id FROM Readers""").fetchall()
        f.write(f'\t\t\tРасписка\t\t\t\n\nНовый читатель ' +
                f'библиотеки: {name}\nid: {i[-1][0]}\n\nПаспортные ' +
                f'данные:\n\tСерия:{series}\t\tНомер:{number}\n\nВаша подпись:\t\t\tПодпись библиотекаря:\n' +
                f'\n_____________			_________________')
        f.close()
        QMessageBox.question(self, '', "Расписка сформированна",
                                    QMessageBox.Ok)


class AddBookForm(QDialog):
    def __init__(self, other):
        super().__init__()
        self.setWindowTitle('Добавить книгу')
        self.pushButton = QPushButton(self)
        self.pushButton.setText('Добавить')
        self.pushButton.clicked.connect(self.accept)
        self.pushButton.setGeometry(30, 360, 111, 31)
        self.pushButton_2 = QPushButton(self)
        self.pushButton_2.setText('Закрыть')
        self.pushButton_2.clicked.connect(self.rejectmy)
        self.pushButton_2.setGeometry(240, 360, 111, 31)
        self.line_author = QLineEdit(self)
        self.line_author.setGeometry(10, 70, 371, 31)
        self.line_title = QLineEdit(self)
        self.line_title.setGeometry(10, 160, 371, 31)
        self.spinBox1 = QSpinBox(self)
        self.spinBox1.setGeometry(50, 280, 42, 22)
        self.spinBox2 = QSpinBox(self)
        self.spinBox2.setGeometry(280, 280, 41, 21)
        self.label1 = QLabel(self)
        self.label1.setText("Автор:")
        self.label1.move(10, 40)
        self.label2 = QLabel(self)
        self.label2.setText("Название:")
        self.label2.move(10, 130)
        self.label3 = QLabel(self)
        self.label3.setText("Стилаж:")
        self.label3.move(50, 250)
        self.label4 = QLabel(self)
        self.label4.setText("Полка:")
        self.label4.move(280, 250)
        self.other_widget = other

    def accept(self):
        super().accept()
        if '' not in (self.line_title.text(), self.line_author.text()) and '0' not in (
                self.spinBox1.text(), self.spinBox2.text()):
            self.other_widget.add_book((self.line_author.text(), self.line_title.text(), self.spinBox1.text(),
                                        self.spinBox2.text()))
        else:
            self.rejectmy(1)

    def rejectmy(self, i=0):
        super().reject()
        self.other_widget.add_book((i,))


class AddBookReader(QDialog):
    def __init__(self, other, rid):
        super().__init__()
        uic.loadUi('addBooks.ui', self)
        self.setWindowTitle('Добавить книги')
        self.cur = sqlite3.connect("books.db")
        self.other = other
        self.reader = rid
        self.pushButton.clicked.connect(self.accept)
        self.pushButton_2.clicked.connect(self.reject)
        self.show_books()

    def show_books(self):
        self.label.setText('')
        cur = self.cur.cursor()
        res = cur.execute(f"""SELECT Books.id, Authors.Name, Books.Title, Books.Stylage, Books.Shelf
                    FROM Books
                    LEFT JOIN Authors ON Authors.id = Books.AutorId""").fetchall()
        self.tableAddBooks.setRowCount(len(res))
        self.tableAddBooks.setColumnCount(len(res[0]))
        for i, elem in enumerate(res):
            for j, val in enumerate(elem):
                self.tableAddBooks.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableAddBooks.setHorizontalHeaderLabels(['id', 'Автор', 'Название', 'Стрилаж', 'Полка'])

    def accept(self):
        rows = list(set([i.row() for i in self.tableAddBooks.selectedItems()]))
        ids = [self.tableAddBooks.item(i, 0).text() for i in rows]
        cur = self.cur.cursor()
        res = cur.execute(f"""SELECT *
                            FROM ReadersBooks
                            WHERE ReaderId = ?""", (self.reader,)).fetchall()
        if not ids:
            self.label.setText('выберите книги')
        elif len([j for j in enumerate(res)]) + len(ids) > 15:
            self.label.setText('У вас может находиться не более 15 книг')
            return
        else:
            ansv = QMessageBox.question(self, '', "Добавить эти книги?",
                                        QMessageBox.Yes, QMessageBox.No)
            if ansv == QMessageBox.Yes:
                date = dt.date.today()
                date2 = dt.timedelta(days=31)
                date += date2
                d = str(date.day) + '.' + str(date.month) + '.' + str(date.year)
                self.other.addForReader([ids, d])
                self.reject()
            else:
                self.reject()


class AddReader(QDialog):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('addReader.ui', self)
        self.setWindowTitle('Добавить читателя')
        self.cur = sqlite3.connect("books.db")
        self.other = other
        self.pushButton.clicked.connect(self.my_accept)
        self.pushButton_2.clicked.connect(self.reject)

    def my_accept(self):
        name = self.lineFuulName.text()
        series = self.lineSeries.text()
        number = self.lineNumber.text()
        try:
            series = int(series)
        except ValueError:
            self.label2.setText('Неверно введённое значение')
            return
        try:
            number = int(number)
        except ValueError:
            self.label3.setText('Неверно введённое значение')
            return
        if len(self.lineSeries.text()) != 4:
            self.label2.setText('неверно введённое значение')
            return
        else:
            self.label2.setText('')
        if len(self.lineNumber.text()) != 6:
            self.label3.setText('Неверно введённое значение')
            return
        else:
            self.label3.setText('')
        self.other.new_reader([name, series, number])
        self.reject()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
