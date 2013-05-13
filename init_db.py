def init_db():
    from app import db
    db.create_all()

if __name__ == '__main__':
    init_db()
