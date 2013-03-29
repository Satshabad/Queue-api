def init_db():
    from queue import db
    db.create_all()

if __name__ == '__main__':
    init_db()
