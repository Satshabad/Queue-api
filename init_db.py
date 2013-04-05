def init_db():
    from main import db
    db.create_all()

if __name__ == '__main__':
    init_db()
